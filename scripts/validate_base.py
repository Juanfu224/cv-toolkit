from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import is_placeholder, load_yaml
from familias import load_familias
from paths import BASE, PLANTILLAS

REQUIRED_PERFIL = ["nombre", "contacto", "experiencia", "educacion"]
REQUIRED_CONTACTO = ["telefono", "email", "ciudad", "pais"]
OPTIONAL_CONTACTO = ["linkedin", "github"]
NIVELES = {"diario", "proyecto", "formativo"}


def load_from(base: Path, name: str) -> dict:
    return load_yaml(base / name)


def evidencia_ids_en_cv(cv: dict) -> list[str]:
    ids: list[str] = []
    for bloque in (cv.get("experiencia") or []) + (cv.get("proyectos") or []):
        for b in bloque.get("bullets") or []:
            if isinstance(b, dict) and b.get("evidencia_id"):
                ids.append(b["evidencia_id"])
    return ids


def vault_vacio(perfil: dict) -> bool:
    return is_placeholder(perfil.get("nombre")) and not (perfil.get("experiencia") or [])


def validate(base: Path | None = None, plantillas: Path | None = None) -> int:
    base = base or BASE
    plantillas = plantillas or PLANTILLAS
    errors: list[str] = []
    warnings: list[str] = []

    perfil = load_from(base, "perfil.yaml")
    if vault_vacio(perfil):
        print("validate_base: VACÍO (copia tu CV a base/origen/ y ejecuta «inicializa mi base»)")
        return 2

    skills = load_from(base, "skills.yaml")
    evidencias_doc = load_from(base, "evidencias.yaml")
    aliases = load_from(base, "aliases.yaml")
    constraints = load_from(base, "constraints.yaml")
    familias = load_familias(base)

    for key in REQUIRED_PERFIL:
        if key not in perfil:
            errors.append(f"perfil.yaml: falta {key}")

    contacto = perfil.get("contacto") or {}
    for key in REQUIRED_CONTACTO:
        if is_placeholder(contacto.get(key)):
            errors.append(f"perfil.yaml: falta contacto.{key}")
        elif "bit.ly" in str(contacto.get(key)):
            errors.append(f"perfil.yaml: contacto.{key} usa acortador bit.ly")
    for key in OPTIONAL_CONTACTO:
        val = contacto.get(key)
        if is_placeholder(val):
            warnings.append(f"perfil.yaml: contacto.{key} vacío (opcional)")
        elif "bit.ly" in str(val):
            errors.append(f"perfil.yaml: contacto.{key} usa acortador bit.ly")

    if is_placeholder(perfil.get("nombre")):
        errors.append("perfil.yaml: falta nombre")

    rol_ids = {r.get("id") for r in perfil.get("experiencia") or [] if r.get("id")}
    proyecto_ids = {p.get("id") for p in perfil.get("proyectos") or [] if p.get("id")}

    for bloque in perfil.get("experiencia") or []:
        if bloque.get("pendiente"):
            warnings.append(
                f"experiencia {bloque.get('empresa')}: pendiente {bloque['pendiente']}"
            )
    for bloque in perfil.get("educacion") or []:
        if bloque.get("pendiente"):
            warnings.append(
                f"educacion {bloque.get('titulo')}: pendiente {bloque['pendiente']}"
            )

    evidencias = evidencias_doc.get("evidencias") or []
    ids: list[str] = []
    for ev in evidencias:
        eid = ev.get("id")
        if not eid:
            errors.append("evidencia sin id")
            continue
        ids.append(eid)
        rol = ev.get("rol")
        if rol not in rol_ids and rol not in proyecto_ids:
            errors.append(f"evidencia {eid}: rol {rol!r} no está en perfil")
        if not ev.get("accion"):
            errors.append(f"evidencia {eid}: falta accion")
        if not ev.get("keywords"):
            warnings.append(f"evidencia {eid}: sin keywords")
    if len(ids) != len(set(ids)):
        errors.append("ids de evidencia duplicados")
    if len(evidencias) < 8:
        warnings.append("pocas evidencias STAR; el skill avisará de base incompleta")

    known = set(ids)
    defaults = sorted(plantillas.glob("cv_default_*.yaml"))
    if not defaults and (perfil.get("experiencia") or []):
        warnings.append("no hay plantillas/cv_default_*.yaml; ejecuta cvtool scaffold")
    for path in defaults:
        cv = load_yaml(path)
        for eid in evidencia_ids_en_cv(cv):
            if eid not in known:
                errors.append(f"{path.name}: evidencia_id {eid} no está en el vault")
        exp = cv.get("experiencia") or []
        actual_idx = [i for i, rol in enumerate(exp) if rol.get("actual")]
        if actual_idx and actual_idx[0] != 0:
            warnings.append(f"{path.name}: puesto actual no es el primero")

    for sk in skills.get("skills") or []:
        nombre = sk.get("nombre")
        nivel = sk.get("nivel")
        if not nombre:
            errors.append("skill sin nombre")
        if nivel not in NIVELES:
            errors.append(f"skill {nombre}: nivel inválido {nivel!r}")

    if "aliases" not in aliases:
        errors.append("aliases.yaml: falta clave aliases")

    if not familias:
        warnings.append("familias.yaml vacío; define al menos una familia de puesto")
    for fid, fam in familias.items():
        band = fam.get("salario") or {}
        if "min" not in band or "max" not in band:
            errors.append(f"familias.yaml: {fid} sin salario.min/max")

    if constraints.get("ubicacion", {}).get("traslado_confirmado") is None:
        warnings.append("constraints: traslado_confirmado no definido")

    for line in warnings:
        print(f"WARN  {line}")
    for line in errors:
        print(f"ERROR {line}")

    if errors:
        print(f"validate_base: {len(errors)} error(es), {len(warnings)} aviso(s)")
        return 1
    print(f"validate_base: OK ({len(warnings)} aviso(s))")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida el vault en base/")
    parser.add_argument("--base", type=Path)
    parser.add_argument("--plantillas", type=Path)
    args = parser.parse_args()
    return validate(args.base, args.plantillas)


if __name__ == "__main__":
    raise SystemExit(main())
