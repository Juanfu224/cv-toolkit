from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (
    cert_label,
    dump_yaml,
    load_yaml,
    norm,
    phrase_in_terms,
    phrase_in_text,
    tokens,
)
from paths import BASE, is_allowed_output
from validate_jd import validate_jd


def vault_terms(perfil: dict, skills: dict, evidencias_doc: dict) -> set[str]:
    terms: set[str] = set()
    for sk in skills.get("skills") or []:
        if sk.get("nombre"):
            terms.add(norm(sk["nombre"]))
    for ev in evidencias_doc.get("evidencias") or []:
        for kw in ev.get("keywords") or []:
            terms.add(norm(kw))
    for edu in perfil.get("educacion") or []:
        if edu.get("titulo"):
            terms.add(norm(edu["titulo"]))
    for rol in perfil.get("experiencia") or []:
        for field in ("titulo", "empresa"):
            if rol.get(field):
                terms.add(norm(rol[field]))
    for proj in perfil.get("proyectos") or []:
        if proj.get("nombre"):
            terms.add(norm(proj["nombre"]))
        for st in proj.get("stack") or []:
            terms.add(norm(st))
    for t in perfil.get("titulos_defendibles") or []:
        terms.add(norm(t))
    for cert in perfil.get("certificaciones") or []:
        label = cert_label(cert)
        if label:
            terms.add(norm(label))
    return terms


def alias_map(aliases: dict) -> dict[str, list]:
    return {norm(k): v for k, v in (aliases.get("aliases") or {}).items()}


def classify(keyword: str, aliases: dict, terms: set[str]) -> str:
    n = norm(keyword)
    mapped = alias_map(aliases).get(n) or None
    if phrase_in_terms(keyword, terms):
        if mapped:
            canonical = [norm(x) for x in mapped]
            if n in canonical or n in terms:
                return "have"
            return "rephrase"
        return "have"
    if mapped and any(phrase_in_terms(x, terms) for x in mapped):
        return "rephrase"
    return "missing"


def cv_blob(cv: dict) -> tuple[str, str]:
    """Texto de competencias y de bullets (experiencia + proyectos).

    Perfil/headline no cuentan como bullets: la cobertura doble T1 exige
    el término en competencias y en al menos un bullet real.
    """
    skills = " ".join(cv.get("competencias") or [])
    bullets: list[str] = []
    for rol in cv.get("experiencia") or []:
        for b in rol.get("bullets") or []:
            bullets.append(b.get("texto") if isinstance(b, dict) else str(b))
    for proj in cv.get("proyectos") or []:
        for b in proj.get("bullets") or []:
            bullets.append(b.get("texto") if isinstance(b, dict) else str(b))
    return skills, " ".join(bullets)


def keyword_in_text(keyword: str, text: str, aliases: dict) -> bool:
    if phrase_in_text(keyword, text):
        return True
    mapped = alias_map(aliases).get(norm(keyword))
    if mapped:
        return any(phrase_in_text(x, text) for x in mapped if x)
    return False


def same_area(jd_ciudad: str, constraints: dict) -> bool:
    ciudad_toks = set(tokens(jd_ciudad or ""))
    if not ciudad_toks:
        return True
    ubi = constraints.get("ubicacion") or {}
    home_toks: set[str] = set()
    for phrase in (ubi.get("ciudad"), ubi.get("provincia")):
        home_toks.update(tokens(phrase or ""))
    return bool(ciudad_toks & home_toks)


def cert_ok(required: list[str], perfil: dict) -> tuple[bool, list[str]]:
    have = set()
    for c in perfil.get("certificaciones") or []:
        label = cert_label(c)
        if label:
            have.add(norm(label))
    missing = [c for c in required if c and not phrase_in_terms(c, have)]
    return not missing, missing


def classify_list(items: list[str], aliases: dict, terms: set[str]) -> list[dict]:
    return [{"term": item, "status": classify(item, aliases, terms)} for item in items]


def coverage(rows: list[dict]) -> float:
    if not rows:
        return 1.0
    ok = sum(1 for r in rows if r["status"] in {"have", "rephrase"})
    return round(ok / len(rows), 3)


def veredicto_de(
    jd: dict,
    constraints: dict,
    perfil: dict,
    aliases: dict,
    terms: set[str],
    rows_t1: list[dict],
    cov_t1: float,
    must_rows: list[dict],
) -> tuple[str, list[str]]:
    motivos: list[str] = []
    resultado = "aplicar"

    seniority = norm(str(jd.get("seniority") or ""))
    banned = [norm(x) for x in (constraints.get("knockout") or {}).get("seniority_no_aplicar") or []]
    if seniority and any(b in seniority.split() or b == seniority for b in banned):
        resultado = "no_aplicar"
        motivos.append(f"seniority no defendible: {jd.get('seniority')}")

    anios = jd.get("anios_experiencia_min")
    max_anios = (constraints.get("knockout") or {}).get("anios_experiencia_max_aceptados")
    if isinstance(anios, (int, float)) and isinstance(max_anios, (int, float)) and anios > max_anios:
        resultado = "no_aplicar"
        motivos.append(f"pide {anios} años; tope honesto {max_anios}")

    certs = jd.get("certificaciones_obligatorias") or []
    ok_c, missing_cert = cert_ok(certs, perfil)
    if not ok_c:
        resultado = "no_aplicar"
        motivos.append(f"certificaciones obligatorias ausentes: {missing_cert}")

    modalidad = tokens(str(jd.get("modalidad") or ""))
    ubi = constraints.get("ubicacion") or {}
    if "presencial" in modalidad and not same_area(jd.get("ciudad") or "", constraints):
        if not ubi.get("traslado_confirmado"):
            resultado = "no_aplicar"
            motivos.append(
                f"presencial en {jd.get('ciudad') or 'otra ciudad'} y traslado no confirmado"
            )

    must_missing = [r["term"] for r in must_rows if r["status"] == "missing"]
    if must_missing:
        resultado = "no_aplicar"
        motivos.append(f"must_have ausentes: {must_missing}")

    t1_missing = [r["term"] for r in rows_t1 if r["status"] == "missing"]
    if resultado != "no_aplicar":
        if cov_t1 < 0.4:
            resultado = "no_aplicar"
            motivos.append(f"cobertura T1 {cov_t1:.0%} por debajo del 40%")
        elif cov_t1 < 0.7 or t1_missing:
            resultado = "aplicar_con_reservas"
            if t1_missing:
                motivos.append(f"T1 ausentes: {t1_missing}")
            if cov_t1 < 0.7:
                motivos.append(f"cobertura T1 {cov_t1:.0%} por debajo del 70%")
        else:
            motivos.append(f"cobertura T1 {cov_t1:.0%}")

    return resultado, motivos


def run_match(
    jd: dict,
    cv: dict | None = None,
    base_dir: Path | None = None,
    *,
    forzar: bool = False,
) -> tuple[dict, dict]:
    base = base_dir or BASE
    perfil = load_yaml(base / "perfil.yaml")
    skills = load_yaml(base / "skills.yaml")
    evidencias = load_yaml(base / "evidencias.yaml")
    aliases = load_yaml(base / "aliases.yaml")
    constraints = load_yaml(base / "constraints.yaml")
    terms = vault_terms(perfil, skills, evidencias)

    kw = jd.get("keywords") or {}
    rows_t1 = classify_list(list(kw.get("t1") or []), aliases, terms)
    rows_t2 = classify_list(list(kw.get("t2") or []), aliases, terms)
    rows_t3 = classify_list(list(kw.get("t3") or []), aliases, terms)
    must_rows = classify_list(list(jd.get("must_have") or []), aliases, terms)
    cov_t1 = coverage(rows_t1)

    doble = None
    huerfanas: list[str] = []
    if cv:
        skills_txt, bullets_txt = cv_blob(cv)
        relevant = [r for r in rows_t1 if r["status"] in {"have", "rephrase"}]
        covered = 0
        for r in relevant:
            in_skills = keyword_in_text(r["term"], skills_txt, aliases)
            in_bullets = keyword_in_text(r["term"], bullets_txt, aliases)
            if in_skills and in_bullets:
                covered += 1
            else:
                huerfanas.append(r["term"])
        doble = round(covered / len(relevant), 3) if relevant else 1.0

    resultado, motivos = veredicto_de(
        jd, constraints, perfil, aliases, terms, rows_t1, cov_t1, must_rows
    )
    gaps = {
        "t1": rows_t1,
        "t2": rows_t2,
        "t3": rows_t3,
        "score_t1": cov_t1,
        "cobertura_doble": doble,
        "huerfanas": huerfanas,
        "must_have": must_rows,
        "nice_to_have": classify_list(list(jd.get("nice_to_have") or []), aliases, terms),
    }
    veredicto = {
        "resultado": resultado,
        "motivos": motivos,
        "score_t1": cov_t1,
        "cobertura_doble": doble,
        "forzar": bool(forzar),
    }
    return gaps, veredicto


def main() -> int:
    parser = argparse.ArgumentParser(description="Match determinista oferta vs vault")
    parser.add_argument("--jd", required=True, type=Path)
    parser.add_argument("--cv", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--veredicto", type=Path)
    parser.add_argument("--base", type=Path, help="Vault alternativo (tests)")
    parser.add_argument(
        "--forzar",
        action="store_true",
        help="Marca forzar:true en el veredicto (HITL; no cambia el resultado)",
    )
    args = parser.parse_args()

    if args.out and not is_allowed_output(args.out):
        raise SystemExit("--out fuera del repo o tmp")
    if args.veredicto and not is_allowed_output(args.veredicto):
        raise SystemExit("--veredicto fuera del repo o tmp")

    jd = load_yaml(args.jd)
    errors = validate_jd(jd)
    if errors:
        print(f"jd INVÁLIDO ({args.jd}):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    cv = load_yaml(args.cv) if args.cv and args.cv.exists() else None
    gaps, veredicto = run_match(jd, cv, base_dir=args.base, forzar=args.forzar)

    if args.out:
        dump_yaml(args.out, gaps)
    else:
        import yaml as _yaml

        _yaml.safe_dump(gaps, sys.stdout, allow_unicode=True, sort_keys=False)
    if args.veredicto:
        dump_yaml(args.veredicto, veredicto)

    print(f"veredicto: {veredicto['resultado']}  score_t1={veredicto['score_t1']}")
    if veredicto.get("forzar"):
        print("  forzar: true")
    for m in veredicto["motivos"]:
        print(f"  - {m}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
