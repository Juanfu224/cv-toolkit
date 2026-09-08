from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import dump_yaml, load_yaml
from familias import load_familias
from paths import BASE, PLANTILLAS


def _rol_en_familia(rol: dict, familia: str) -> bool:
    fams = rol.get("familias") or []
    if not fams:
        return True
    return familia in fams


def _texto_evidencia(ev: dict) -> str:
    accion = (ev.get("accion") or "").rstrip(".")
    resultado = ev.get("resultado")
    if resultado:
        return f"{accion}. {resultado}".rstrip(".")
    return accion


def _fecha_corta(value) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if text.lower() in {"actualidad", "actual"}:
        return "Actualidad"
    if len(text) >= 7 and text[4] == "-" and text[:4].isdigit():
        return text[:7]
    if len(text) >= 4 and text[:4].isdigit():
        return text[:4]
    return text


def _formacion(perfil: dict) -> list[dict]:
    out = []
    for edu in perfil.get("educacion") or []:
        fecha = _fecha_corta(edu.get("fin") or edu.get("fecha") or "")
        out.append(
            {
                "titulo": edu.get("titulo"),
                "centro": edu.get("centro"),
                "fecha": fecha,
            }
        )
    return out


def _fechas_rol(rol: dict) -> str:
    inicio = _fecha_corta(rol.get("inicio") or "")
    fin = rol.get("fin") or ""
    if rol.get("actual") or str(fin).lower() in {"actualidad", "actual"}:
        fin = "Actualidad"
    else:
        fin = _fecha_corta(fin)
    if inicio and fin:
        return f"{inicio} — {fin}"
    return str(inicio or fin)


def scaffold_familia(
    familia: str,
    perfil: dict,
    evidencias: list[dict],
    skills: list[dict],
    fam_meta: dict,
) -> dict:
    ev_by_rol: dict[str, list[dict]] = {}
    for ev in evidencias:
        fams = ev.get("familias") or []
        if fams and familia not in fams:
            continue
        ev_by_rol.setdefault(ev.get("rol") or "", []).append(ev)

    experiencia = []
    for rol in perfil.get("experiencia") or []:
        if not _rol_en_familia(rol, familia):
            continue
        bullets = []
        for ev in ev_by_rol.get(rol.get("id"), []):
            texto = _texto_evidencia(ev)
            if texto:
                bullets.append({"texto": texto, "evidencia_id": ev["id"]})
        experiencia.append(
            {
                "titulo": rol.get("titulo"),
                "empresa": rol.get("empresa"),
                "fechas": _fechas_rol(rol),
                "actual": bool(rol.get("actual")),
                "bullets": bullets,
            }
        )
    experiencia.sort(key=lambda r: not r.get("actual"))

    competencias = []
    for sk in skills:
        nivel = sk.get("nivel")
        fams = sk.get("familias") or []
        if nivel == "formativo":
            continue
        if fams and familia not in fams:
            continue
        if sk.get("nombre") and sk["nombre"] not in competencias:
            competencias.append(sk["nombre"])
        if len(competencias) >= 15:
            break

    secciones = ["perfil", "competencias", "experiencia"]
    proyectos = []
    if fam_meta.get("incluye_proyectos", True):
        secciones.append("proyectos")
        for proj in perfil.get("proyectos") or []:
            bullets = []
            for ev in ev_by_rol.get(proj.get("id"), []):
                texto = _texto_evidencia(ev)
                if texto:
                    bullets.append({"texto": texto, "evidencia_id": ev["id"]})
            proyectos.append(
                {
                    "nombre": proj.get("nombre"),
                    "url": proj.get("url"),
                    "stack": proj.get("stack") or [],
                    "bullets": bullets,
                }
            )
    secciones += ["formacion", "idiomas"]
    if perfil.get("certificaciones"):
        secciones.append("certificaciones")

    headline = perfil.get("headline_base") or (perfil.get("titulos_defendibles") or [""])[0]
    perfil_txt = (perfil.get("headline_base") or "").strip()
    if not perfil_txt:
        perfil_txt = f"{perfil.get('nombre')} — {headline}"

    return {
        "nombre": perfil.get("nombre"),
        "headline": headline,
        "familia": familia,
        "perfil": perfil_txt,
        "secciones": secciones,
        "competencias": competencias,
        "experiencia": experiencia,
        "proyectos": proyectos,
        "formacion": _formacion(perfil),
        "idiomas": perfil.get("idiomas") or [],
        "certificaciones": perfil.get("certificaciones") or [],
    }


def scaffold(
    base: Path | None = None, plantillas: Path | None = None
) -> list[Path]:
    base = base or BASE
    plantillas = plantillas or PLANTILLAS
    perfil = load_yaml(base / "perfil.yaml")
    evidencias = (load_yaml(base / "evidencias.yaml").get("evidencias") or [])
    skills = (load_yaml(base / "skills.yaml").get("skills") or [])
    familias = load_familias(base)
    if not familias:
        raise SystemExit("familias.yaml vacío: define al menos una familia antes de scaffold")

    written: list[Path] = []
    plantillas.mkdir(parents=True, exist_ok=True)
    for fid, meta in familias.items():
        cv = scaffold_familia(fid, perfil, evidencias, skills, meta)
        dest = plantillas / f"cv_default_{fid}.yaml"
        dump_yaml(dest, cv)
        print(f"escrito {dest}")
        written.append(dest)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Genera plantillas/cv_default_<familia>.yaml desde el vault"
    )
    parser.add_argument("--base", type=Path)
    parser.add_argument("--plantillas", type=Path)
    args = parser.parse_args()
    scaffold(args.base, args.plantillas)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
