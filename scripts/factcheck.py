from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import dump_yaml, load_yaml, norm
from match import classify, vault_terms
from paths import BASE, is_allowed_output

METRIC_RE = re.compile(
    r"(?:€|\$)\s*\d[\d.]*(?:[.,]\d+)?|\d[\d.]*(?:[.,]\d+)?\s*(?:€|\$|%)"
)
HTTP_RE = re.compile(r"^https?://", re.I)
PRESENTACION_MAX = 250
OUTREACH_MAX = 80
MAX_HECHOS = 3

ARTIFACT_MD = ("presentacion.md", "respuestas.md", "outreach.md")
VAULT_FILES = (
    "perfil.yaml",
    "evidencias.yaml",
    "skills.yaml",
    "aliases.yaml",
    "constraints.yaml",
    "familias.yaml",
)


def word_count(text: str) -> int:
    return len(re.findall(r"\S+", text or ""))


def vault_blob(base: Path) -> str:
    parts: list[str] = []
    for name in VAULT_FILES:
        path = base / name
        if path.exists():
            parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts)


def cv_human_text(cv: dict) -> str:
    chunks: list[str] = [
        str(cv.get("headline") or ""),
        str(cv.get("perfil") or ""),
        " ".join(cv.get("competencias") or []),
    ]
    for bloque in (cv.get("experiencia") or []) + (cv.get("proyectos") or []):
        chunks.append(str(bloque.get("empresa") or ""))
        chunks.append(str(bloque.get("titulo") or ""))
        chunks.append(str(bloque.get("nombre") or ""))
        for b in bloque.get("bullets") or []:
            if isinstance(b, dict):
                chunks.append(str(b.get("texto") or ""))
            else:
                chunks.append(str(b))
    return "\n".join(chunks)


def artifact_texts(pack_dir: Path, cv: dict | None) -> tuple[str, dict[str, str]]:
    named: dict[str, str] = {}
    chunks: list[str] = []
    if cv is not None:
        text = cv_human_text(cv)
        named["cv.yaml"] = text
        chunks.append(text)
    for name in ARTIFACT_MD:
        path = pack_dir / name
        if path.exists():
            text = path.read_text(encoding="utf-8")
            named[name] = text
            chunks.append(text)
    return "\n".join(chunks), named


def metric_in_vault(metric: str, blob: str) -> bool:
    """Exige la cifra con su unidad (%/€/$) en el vault; no basta el número suelto."""
    compact = re.sub(r"\s+", "", metric).lower().replace(",", ".")
    blob_compact = re.sub(r"\s+", "", blob).lower().replace(",", ".")
    return compact in blob_compact


def check_metrics(text: str, blob: str) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for match in METRIC_RE.finditer(text or ""):
        raw = match.group(0).strip()
        key = norm(raw)
        if not key or key in seen:
            continue
        seen.add(key)
        if not metric_in_vault(raw, blob):
            out.append(
                {
                    "tipo": "metrica",
                    "dato": raw,
                    "detalle": "métrica ausente del vault",
                }
            )
    return out


def check_tecnologias(cv: dict, vault: dict[str, Any]) -> list[dict]:
    terms = vault_terms(vault["perfil"], vault["skills"], vault["evidencias"])
    aliases = vault["aliases"]
    viol: list[dict] = []
    for term in cv.get("competencias") or []:
        if not term:
            continue
        if classify(str(term), aliases, terms) == "missing":
            viol.append(
                {
                    "tipo": "tecnologia",
                    "dato": str(term),
                    "detalle": "competencia no está en el vault ni en aliases",
                }
            )
    return viol


def check_empleadores(cv: dict, perfil: dict) -> list[dict]:
    known = {norm(r.get("empresa") or "") for r in perfil.get("experiencia") or []}
    known |= {norm(p.get("nombre") or "") for p in perfil.get("proyectos") or []}
    known.discard("")
    viol: list[dict] = []
    for rol in cv.get("experiencia") or []:
        emp = rol.get("empresa")
        if emp and norm(str(emp)) not in known:
            viol.append(
                {
                    "tipo": "empleador",
                    "dato": str(emp),
                    "detalle": "empleador no está en el vault",
                }
            )
    for proj in cv.get("proyectos") or []:
        name = proj.get("nombre")
        if name and norm(str(name)) not in known:
            viol.append(
                {
                    "tipo": "empleador",
                    "dato": str(name),
                    "detalle": "proyecto no está en el vault",
                }
            )
    return viol


def check_longitud(named: dict[str, str]) -> tuple[list[dict], int | None, int | None]:
    viol: list[dict] = []
    pres = named.get("presentacion.md")
    outr = named.get("outreach.md")
    n_pres = word_count(pres) if pres is not None else None
    n_out = word_count(outr) if outr is not None else None
    if n_pres is not None and n_pres > PRESENTACION_MAX:
        viol.append(
            {
                "tipo": "longitud",
                "dato": "presentacion.md",
                "detalle": f"{n_pres} palabras (máx. {PRESENTACION_MAX})",
            }
        )
    if n_out is not None and n_out > OUTREACH_MAX:
        viol.append(
            {
                "tipo": "longitud",
                "dato": "outreach.md",
                "detalle": f"{n_out} palabras (máx. {OUTREACH_MAX})",
            }
        )
    return viol, n_pres, n_out


def check_empresa(pack_dir: Path) -> list[dict]:
    path = pack_dir / "empresa.yaml"
    if not path.exists():
        return []
    data = load_yaml(path)
    viol: list[dict] = []
    hechos = list(data.get("hechos") or [])
    if len(hechos) > MAX_HECHOS:
        viol.append(
            {
                "tipo": "empresa",
                "dato": "hechos",
                "detalle": f"{len(hechos)} hechos (máx. {MAX_HECHOS})",
            }
        )
    for item in hechos:
        if not isinstance(item, dict):
            viol.append(
                {
                    "tipo": "empresa",
                    "dato": str(item),
                    "detalle": "hecho no es un objeto",
                }
            )
            continue
        fuente = str(item.get("fuente") or "")
        if not HTTP_RE.match(fuente):
            viol.append(
                {
                    "tipo": "empresa",
                    "dato": str(item.get("hecho") or fuente),
                    "detalle": "hecho sin fuente http(s)",
                }
            )
    if hechos and data.get("sin_hechos_verificables") is True:
        viol.append(
            {
                "tipo": "empresa",
                "dato": "sin_hechos_verificables",
                "detalle": "true con hechos presentes",
            }
        )
    return viol


def load_vault(base: Path) -> dict[str, Any]:
    return {
        "perfil": load_yaml(base / "perfil.yaml"),
        "skills": load_yaml(base / "skills.yaml"),
        "evidencias": load_yaml(base / "evidencias.yaml"),
        "aliases": load_yaml(base / "aliases.yaml"),
    }


def run_factcheck(pack_dir: Path, base: Path | None = None) -> dict:
    base = base or BASE
    blob = vault_blob(base)
    vault = load_vault(base)
    cv_path = pack_dir / "cv.yaml"
    cv = load_yaml(cv_path) if cv_path.exists() else None
    combined, named = artifact_texts(pack_dir, cv)
    violaciones: list[dict] = []
    violaciones.extend(check_metrics(combined, blob))
    if cv is not None:
        violaciones.extend(check_tecnologias(cv, vault))
        violaciones.extend(check_empleadores(cv, vault["perfil"]))
    long_v, n_pres, n_out = check_longitud(named)
    violaciones.extend(long_v)
    violaciones.extend(check_empresa(pack_dir))

    unique_metrics = {norm(m) for m in METRIC_RE.findall(combined or "") if norm(m)}
    tech_total = len([c for c in (cv.get("competencias") or []) if c]) if cv else 0
    emp_total = 0
    if cv:
        emp_total = len([r for r in (cv.get("experiencia") or []) if r.get("empresa")])
        emp_total += len([p for p in (cv.get("proyectos") or []) if p.get("nombre")])
    claims = len(unique_metrics) + tech_total + emp_total
    failed = sum(
        1 for v in violaciones if v["tipo"] in {"metrica", "tecnologia", "empleador"}
    )
    supported = max(claims - failed, 0)
    confianza = 1.0 if claims == 0 else round(supported / claims, 3)
    ok = not violaciones and confianza >= 1.0
    return {
        "ok": ok,
        "confianza": confianza,
        "presentacion_palabras": n_pres,
        "outreach_palabras": n_out,
        "violaciones": violaciones,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Comprueba que el pack no inventa métricas, techs ni empleadores"
    )
    parser.add_argument("--dir", required=True, type=Path, help="Carpeta de la candidatura")
    parser.add_argument("--base", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.out and not is_allowed_output(args.out):
        print("factcheck: --out fuera del repo o tmp", file=sys.stderr)
        return 1
    report = run_factcheck(args.dir, args.base)
    if args.out:
        dump_yaml(args.out, report)
        print(f"escrito {args.out}")
    else:
        json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    print(f"factcheck: {'ok' if report['ok'] else 'FAIL'}  confianza={report['confianza']}")
    for v in report["violaciones"]:
        print(f"  - {v['tipo']}: {v['dato']} ({v['detalle']})")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
