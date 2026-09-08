from __future__ import annotations

import argparse
import copy
import re
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import dump_yaml, load_yaml
from match import cv_blob, keyword_in_text
from paths import BASE, is_allowed_output
from render_cv import apply_perfil, to_docx, to_markdown, to_pdf

SKILL_FLOOR = 8
SKILL_CAP = 15
CORE_BULLETS_FIRST_ROLE = 2
LONG_BULLET_CHARS = 220
METRIC_RE = re.compile(r"\d|%|€|\$")


@dataclass(order=True)
class PackUnit:
    score: float
    kind: str = field(compare=False)
    key: str = field(compare=False)
    apply: Callable[[dict], None] = field(compare=False, repr=False)
    t1_terms: list[str] = field(default_factory=list, compare=False)


def t1_terms_from_gaps(gaps: dict | None) -> list[str]:
    if not gaps:
        return []
    out: list[str] = []
    for row in gaps.get("t1") or []:
        if not isinstance(row, dict):
            continue
        if row.get("status") in {"have", "rephrase"} and row.get("term"):
            out.append(str(row["term"]))
    return out


def _covers_any(text: str, terms: list[str], aliases: dict | None = None) -> list[str]:
    aliases = aliases or {}
    hit = []
    for term in terms:
        if keyword_in_text(term, text, aliases):
            hit.append(term)
    return hit


def score_text(
    text: str,
    *,
    t1: list[str],
    aliases: dict | None = None,
    recency: float = 0.0,
    skill_bonus: float = 0.0,
) -> tuple[float, list[str]]:
    covered = _covers_any(text, t1, aliases)
    score = 1000.0 * len(covered)
    if METRIC_RE.search(text or ""):
        score += 100.0
    score += recency
    score += skill_bonus
    # Penalize verbose bullets so more high-signal units can fit.
    n = len(text or "")
    if n > LONG_BULLET_CHARS:
        score -= min((n - LONG_BULLET_CHARS) / 40.0, 25.0)
    return score, covered


def _bullet_texto(item: Any) -> str:
    if isinstance(item, dict):
        return item.get("texto") or ""
    return str(item)


def _bullet_id(item: Any, fallback: str) -> str:
    if isinstance(item, dict) and item.get("evidencia_id"):
        return str(item["evidencia_id"])
    return fallback


def pdf_page_count(cv: dict, dest: Path) -> int:
    to_pdf(cv, dest)
    return len(PdfReader(str(dest)).pages)


def build_units(
    draft: dict,
    t1: list[str],
    aliases: dict | None = None,
) -> tuple[dict, list[PackUnit], list[str], list[str]]:
    """Return (core_cv, ranked_packable_units, forced_keys, warnings)."""
    aliases = aliases or {}
    core = copy.deepcopy(draft)
    units: list[PackUnit] = []
    forced: list[str] = []
    warnings: list[str] = []

    # --- Skills ---
    skills = list(draft.get("competencias") or [])[:SKILL_CAP]
    scored_skills: list[tuple[float, str, list[str]]] = []
    for sk in skills:
        sc, cov = score_text(sk, t1=t1, aliases=aliases, skill_bonus=50.0)
        scored_skills.append((sc, sk, cov))
    scored_skills.sort(key=lambda x: (-x[0], x[1].lower()))

    # Prefer T1-covering skills in the floor, then fill up to SKILL_FLOOR.
    floor: list[str] = []
    for sc, sk, cov in scored_skills:
        if cov and sk not in floor and len(floor) < SKILL_FLOOR:
            floor.append(sk)
    for sc, sk, cov in scored_skills:
        if sk not in floor and len(floor) < SKILL_FLOOR:
            floor.append(sk)

    rest_clean = [(sc, sk, cov) for sc, sk, cov in scored_skills if sk not in floor]

    core["competencias"] = floor
    forced.extend(f"skill:{s}" for s in floor)

    for sc, sk, cov in rest_clean:

        def _add_skill(cv: dict, name: str = sk) -> None:
            comps = list(cv.get("competencias") or [])
            if name not in comps and len(comps) < SKILL_CAP:
                comps.append(name)
                cv["competencias"] = comps

        units.append(
            PackUnit(
                score=-sc,
                kind="skill",
                key=f"skill:{sk}",
                apply=_add_skill,
                t1_terms=cov,
            )
        )

    # --- Experiencia ---
    roles = list(draft.get("experiencia") or [])
    core_roles: list[dict] = []
    for ri, rol in enumerate(roles):
        bullets = list(rol.get("bullets") or [])
        recency = 200.0 if rol.get("actual") or ri == 0 else max(0.0, 80.0 - 20.0 * ri)
        scored_bullets: list[tuple[float, Any, str, list[str]]] = []
        for bi, b in enumerate(bullets):
            texto = _bullet_texto(b)
            bid = _bullet_id(b, f"rol{ri}-b{bi}")
            sc, cov = score_text(texto, t1=t1, aliases=aliases, recency=recency)
            scored_bullets.append((sc, b, bid, cov))
        scored_bullets.sort(key=lambda x: -x[0])

        if ri == 0:
            if len(scored_bullets) < CORE_BULLETS_FIRST_ROLE:
                warnings.append(
                    f"rol reciente tiene {len(scored_bullets)} bullet(s); "
                    f"núcleo pide {CORE_BULLETS_FIRST_ROLE} si el vault las tiene"
                )
            keep = scored_bullets[:CORE_BULLETS_FIRST_ROLE]
            extra = scored_bullets[CORE_BULLETS_FIRST_ROLE:]
            core_rol = {
                "titulo": rol.get("titulo"),
                "empresa": rol.get("empresa"),
                "fechas": rol.get("fechas"),
                "actual": rol.get("actual"),
                "bullets": [b for _, b, _, _ in keep],
            }
            core_roles.append(core_rol)
            forced.extend(f"bullet:{bid}" for _, _, bid, _ in keep)
            for sc, b, bid, cov in extra:

                def _add_bullet(
                    cv: dict,
                    role_idx: int = 0,
                    bullet: Any = b,
                ) -> None:
                    exp = cv.setdefault("experiencia", [])
                    if role_idx >= len(exp):
                        return
                    bl = list(exp[role_idx].get("bullets") or [])
                    bl.append(copy.deepcopy(bullet))
                    exp[role_idx]["bullets"] = bl

                units.append(
                    PackUnit(
                        score=-sc,
                        kind="bullet",
                        key=f"bullet:{bid}",
                        apply=_add_bullet,
                        t1_terms=cov,
                    )
                )
        else:
            # Role appears when its first included bullet is applied.
            for sc, b, bid, cov in scored_bullets:

                def _add_role_bullet(
                    cv: dict,
                    role_template: dict = rol,
                    bullet: Any = b,
                ) -> None:
                    exp = cv.setdefault("experiencia", [])
                    found = None
                    for existing in exp:
                        if (
                            existing.get("titulo") == role_template.get("titulo")
                            and existing.get("empresa") == role_template.get("empresa")
                            and existing.get("fechas") == role_template.get("fechas")
                        ):
                            found = existing
                            break
                    if found is None:
                        found = {
                            "titulo": role_template.get("titulo"),
                            "empresa": role_template.get("empresa"),
                            "fechas": role_template.get("fechas"),
                            "actual": role_template.get("actual"),
                            "bullets": [],
                        }
                        exp.append(found)
                    bl = list(found.get("bullets") or [])
                    bl.append(copy.deepcopy(bullet))
                    found["bullets"] = bl

                units.append(
                    PackUnit(
                        score=-(sc - 5.0),  # slight penalty vs first-role bullets
                        kind="bullet",
                        key=f"bullet:{bid}",
                        apply=_add_role_bullet,
                        t1_terms=cov,
                    )
                )

    core["experiencia"] = core_roles

    # --- Proyectos ---
    core["proyectos"] = []
    secciones = list(draft.get("secciones") or [])
    has_proyectos = "proyectos" in secciones
    for pi, proj in enumerate(draft.get("proyectos") or []):
        if not has_proyectos:
            break
        bullets = list(proj.get("bullets") or [])
        for bi, b in enumerate(bullets):
            texto = _bullet_texto(b)
            bid = _bullet_id(b, f"proj{pi}-b{bi}")
            sc, cov = score_text(
                texto + " " + " ".join(proj.get("stack") or []),
                t1=t1,
                aliases=aliases,
                recency=40.0,
            )

            def _add_proj_bullet(
                cv: dict,
                project: dict = proj,
                bullet: Any = b,
            ) -> None:
                projs = cv.setdefault("proyectos", [])
                found = None
                for existing in projs:
                    if existing.get("nombre") == project.get("nombre"):
                        found = existing
                        break
                if found is None:
                    found = {
                        "nombre": project.get("nombre"),
                        "url": project.get("url"),
                        "stack": list(project.get("stack") or []),
                        "bullets": [],
                    }
                    projs.append(found)
                    secs = list(cv.get("secciones") or [])
                    if "proyectos" not in secs:
                        # Insert before formacion if present
                        if "formacion" in secs:
                            secs.insert(secs.index("formacion"), "proyectos")
                        else:
                            secs.append("proyectos")
                        cv["secciones"] = secs
                bl = list(found.get("bullets") or [])
                bl.append(copy.deepcopy(bullet))
                found["bullets"] = bl

            units.append(
                PackUnit(
                    score=-(sc - 15.0),
                    kind="project_bullet",
                    key=f"bullet:{bid}",
                    apply=_add_proj_bullet,
                    t1_terms=cov,
                )
            )

    # Compact sections stay in core as-is (formacion/idiomas/certs).
    units.sort()  # ascending score field = descending priority because negated
    return core, units, forced, warnings


def t1_coverage(cv: dict, t1: list[str], aliases: dict | None = None) -> tuple[list[str], list[str]]:
    """Return (missing_in_skills, missing_in_bullets) for T1 terms."""
    aliases = aliases or {}
    skills_txt, bullets_txt = cv_blob(cv)
    miss_skills: list[str] = []
    miss_bullets: list[str] = []
    for term in t1:
        if not keyword_in_text(term, skills_txt, aliases):
            miss_skills.append(term)
        if not keyword_in_text(term, bullets_txt, aliases):
            miss_bullets.append(term)
    return miss_skills, miss_bullets


def _force_t1(
    packed: dict,
    draft: dict,
    t1: list[str],
    aliases: dict | None,
    report: dict,
) -> None:
    """Best-effort: reintroduce draft skills/bullets that cover missing T1."""
    aliases = aliases or {}
    miss_sk, miss_bu = t1_coverage(packed, t1, aliases)
    for term in miss_sk:
        for sk in draft.get("competencias") or []:
            if keyword_in_text(term, sk, aliases):
                comps = list(packed.get("competencias") or [])
                if sk not in comps:
                    if len(comps) >= SKILL_CAP:
                        drop_idx = None
                        for i, existing in enumerate(comps):
                            if not _covers_any(existing, t1, aliases):
                                drop_idx = i
                                break
                        if drop_idx is None:
                            report.setdefault("warnings", []).append(
                                f"no se pudo forzar skill T1 {sk!r}: "
                                "todas las competencias cubren T1 y hay tope"
                            )
                            break
                        comps.pop(drop_idx)
                    comps.append(sk)
                    packed["competencias"] = comps
                    report.setdefault("forced", []).append(
                        {"key": f"skill:{sk}", "reason": f"t1:{term}"}
                    )
                break
    for term in miss_bu:
        # Prefer experience bullets from draft
        placed = False
        for rol in draft.get("experiencia") or []:
            for b in rol.get("bullets") or []:
                if keyword_in_text(term, _bullet_texto(b), aliases):
                    # Ensure role exists then append bullet
                    exp = packed.setdefault("experiencia", [])
                    found = None
                    for existing in exp:
                        if (
                            existing.get("titulo") == rol.get("titulo")
                            and existing.get("empresa") == rol.get("empresa")
                        ):
                            found = existing
                            break
                    if found is None:
                        found = {
                            "titulo": rol.get("titulo"),
                            "empresa": rol.get("empresa"),
                            "fechas": rol.get("fechas"),
                            "actual": rol.get("actual"),
                            "bullets": [],
                        }
                        exp.append(found)
                    texts = {_bullet_texto(x) for x in found.get("bullets") or []}
                    if _bullet_texto(b) not in texts:
                        found.setdefault("bullets", []).append(copy.deepcopy(b))
                        report.setdefault("forced", []).append(
                            {
                                "key": f"bullet:{_bullet_id(b, term)}",
                                "reason": f"t1:{term}",
                            }
                        )
                    placed = True
                    break
            if placed:
                break


def pack(
    draft: dict,
    gaps: dict | None = None,
    aliases: dict | None = None,
    work_dir: Path | None = None,
) -> tuple[dict, dict]:
    """Greedy pack: maximize units while PDF stays on 1 page.

    Returns (packed_cv, report). Raises SystemExit on failure if core alone
    exceeds one page or forced T1 still overflows.
    """
    t1 = t1_terms_from_gaps(gaps)
    aliases = aliases or {}
    core, units, forced_keys, warnings = build_units(draft, t1, aliases)

    tmp_ctx = None
    if work_dir is None:
        tmp_ctx = tempfile.TemporaryDirectory(prefix="cvpack-")
        work = Path(tmp_ctx.name)
    else:
        work = Path(work_dir)
        work.mkdir(parents=True, exist_ok=True)
    pdf_path = work / "_pack_probe.pdf"

    try:
        try:
            pages = pdf_page_count(core, pdf_path)
        except Exception as exc:  # noqa: BLE001 — surface render errors
            raise SystemExit(f"pack: no se pudo renderizar el núcleo: {exc}") from exc

        report: dict[str, Any] = {
            "t1": t1,
            "included": [{"key": k, "reason": "core"} for k in forced_keys],
            "excluded": [],
            "forced": [],
            "warnings": list(warnings),
            "pages_core": pages,
        }

        if pages > 1:
            raise SystemExit(
                "pack: el núcleo (contacto, perfil, ≥2 bullets del rol reciente, "
                f"piso de competencias) ya ocupa {pages} páginas; acorta textos en cv.yaml"
            )

        current = copy.deepcopy(core)
        for unit in units:
            candidate = copy.deepcopy(current)
            unit.apply(candidate)
            pages = pdf_page_count(candidate, pdf_path)
            if pages == 1:
                current = candidate
                report["included"].append(
                    {"key": unit.key, "reason": "fit", "score": -unit.score}
                )
            else:
                report["excluded"].append(
                    {"key": unit.key, "reason": "overflow", "score": -unit.score}
                )

        _force_t1(current, draft, t1, aliases, report)
        pages = pdf_page_count(current, pdf_path)
        report["pages"] = pages
        if pages > 1:
            # Rebuild: core + T1 force, then re-add fit units by descending score while ≤1 page.
            unit_by_key = {u.key: u for u in units}
            fit_items = [item for item in report["included"] if item.get("reason") == "fit"]
            fit_items.sort(key=lambda x: -(x.get("score") or 0))
            rebuilt = copy.deepcopy(core)
            _force_t1(rebuilt, draft, t1, aliases, report)
            kept: list[dict] = [
                item for item in report["included"] if item.get("reason") == "core"
            ]
            for item in fit_items:
                u = unit_by_key.get(item["key"])
                if not u:
                    continue
                trial = copy.deepcopy(rebuilt)
                u.apply(trial)
                if pdf_page_count(trial, pdf_path) == 1:
                    rebuilt = trial
                    kept.append(item)
                else:
                    report["excluded"].append(
                        {
                            "key": item["key"],
                            "reason": "overflow_after_t1",
                            "score": item.get("score"),
                        }
                    )
            report["included"] = kept + list(report.get("forced") or [])
            current = rebuilt
            pages = pdf_page_count(current, pdf_path)
            report["pages"] = pages
            if pages > 1:
                raise SystemExit(
                    f"pack: tras forzar T1 el PDF sigue en {pages} páginas; "
                    "acorta perfil/bullets del núcleo"
                )

        miss_sk, miss_bu = t1_coverage(current, t1, aliases)
        report["t1_missing_skills"] = miss_sk
        report["t1_missing_bullets"] = miss_bu
        return current, report
    finally:
        if tmp_ctx is not None:
            tmp_ctx.cleanup()


def _default_aliases() -> dict:
    path = BASE / "aliases.yaml"
    if path.exists():
        return load_yaml(path)
    return {}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Empaqueta cv.yaml para máxima señal en ≤1 página A4"
    )
    parser.add_argument("--cv", required=True, type=Path, help="cv.yaml draft")
    parser.add_argument("--out", required=True, type=Path, help="cv.yaml empaquetado")
    parser.add_argument("--gaps", type=Path, help="gaps.yaml del match (T1)")
    parser.add_argument(
        "--aliases",
        type=Path,
        help="aliases.yaml (por defecto base/aliases.yaml si existe)",
    )
    parser.add_argument("--report", type=Path, help="pack_report.yaml")
    parser.add_argument(
        "--out-dir",
        type=Path,
        help="Si se indica, también escribe PDF/DOCX/MD (basename curriculum)",
    )
    parser.add_argument("--basename", default="curriculum")
    parser.add_argument(
        "--no-perfil",
        action="store_true",
        help="No sobrescribe nombre/contacto desde base/perfil.yaml",
    )
    args = parser.parse_args()

    if not args.cv.exists():
        raise SystemExit(f"no existe {args.cv}")
    if not is_allowed_output(args.out):
        raise SystemExit("--out fuera del repo o tmp")
    if args.report and not is_allowed_output(args.report):
        raise SystemExit("--report fuera del repo o tmp")
    if args.out_dir and not is_allowed_output(args.out_dir):
        raise SystemExit("--out-dir fuera del repo o tmp")

    cv = load_yaml(args.cv)
    if not args.no_perfil:
        cv = apply_perfil(cv)

    gaps = load_yaml(args.gaps) if args.gaps and args.gaps.exists() else None
    if args.aliases:
        aliases = load_yaml(args.aliases) if args.aliases.exists() else {}
    else:
        aliases = _default_aliases()

    packed, report = pack(cv, gaps=gaps, aliases=aliases)
    dump_yaml(args.out, packed)
    print(f"escrito {args.out}")

    report_path = args.report or (args.out.parent / "pack_report.yaml")
    dump_yaml(report_path, report)
    print(f"escrito {report_path}")
    print(
        f"pack: OK  páginas={report.get('pages')}  "
        f"incluidos={len(report.get('included') or [])}  "
        f"excluidos={len(report.get('excluded') or [])}"
    )

    if args.out_dir:
        out = args.out_dir
        out.mkdir(parents=True, exist_ok=True)
        base = args.basename
        md_path = out / f"{base}.md"
        pdf_path = out / f"{base}.pdf"
        docx_path = out / f"{base}.docx"
        md_path.write_text(to_markdown(packed), encoding="utf-8")
        to_pdf(packed, pdf_path)
        to_docx(packed, docx_path)
        print(f"escrito {md_path}")
        print(f"escrito {pdf_path}")
        print(f"escrito {docx_path}")

    if report.get("warnings"):
        for w in report["warnings"]:
            print(f"WARN  {w}")
    if report.get("t1_missing_skills") or report.get("t1_missing_bullets"):
        print(
            "WARN  T1 sin cobertura completa tras pack: "
            f"skills={report.get('t1_missing_skills')} "
            f"bullets={report.get('t1_missing_bullets')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
