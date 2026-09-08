from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from common import dump_yaml  # noqa: E402

GENERIC_ALIASES = {
    "aliases": {
        "typescript": ["TypeScript"],
        "sql": ["SQL", "PostgreSQL"],
        "php": ["PHP"],
        "rest apis": ["APIs REST"],
        "help desk": ["Soporte técnico"],
        "kubernetes": [],
        "ad": ["Active Directory"],
        "angular": ["Angular"],
    }
}


def write_vault(root: Path, **overrides) -> Path:
    """Vault mínimo en un directorio temporal. Solo para tests."""
    base = root / "base"
    plantillas = root / "plantillas"
    base.mkdir(parents=True, exist_ok=True)
    plantillas.mkdir(parents=True, exist_ok=True)

    perfil = {
        "nombre": "Nombre Prueba",
        "headline_base": "Desarrollador web",
        "titulos_defendibles": ["Desarrollador web", "Técnico de soporte"],
        "contacto": {
            "telefono": "(+34) 600 000 000",
            "email": "test@example.com",
            "ciudad": "Valencia",
            "pais": "España",
            "linkedin": "https://www.linkedin.com/in/test",
            "github": "https://github.com/test",
        },
        "idiomas": [{"idioma": "Español", "nivel": "Nativo"}],
        "educacion": [{"titulo": "DAW", "centro": "IES", "fin": "2024-06"}],
        "experiencia": [
            {
                "id": "rol-a",
                "titulo": "Desarrollador full stack",
                "empresa": "Empresa A",
                "inicio": "2025",
                "fin": "actualidad",
                "actual": True,
                "familias": ["dev"],
            },
            {
                "id": "rol-b",
                "titulo": "Técnico de soporte",
                "empresa": "Empresa B",
                "inicio": "2023",
                "fin": "2025",
                "actual": False,
                "familias": ["soporte"],
            },
        ],
        "proyectos": [
            {
                "id": "proj-a",
                "nombre": "Proyecto A",
                "url": "https://github.com/test/proyecto-a",
                "stack": ["PHP", "Angular"],
                "familias": ["dev"],
            }
        ],
        "certificaciones": [],
    }
    evidencias = {
        "evidencias": [
            {
                "id": f"ev-{i:02d}",
                "rol": rol,
                "familias": fams,
                "keywords": kws,
                "accion": accion,
                "resultado": "Hecho verificable en entorno de prueba",
            }
            for i, (rol, fams, kws, accion) in enumerate(
                [
                    ("rol-a", ["dev"], ["Angular", "TypeScript", "HTML", "CSS", "JavaScript"], "Desarrollar interfaces con Angular y TypeScript"),
                    ("rol-a", ["dev"], ["APIs REST"], "Mantener APIs REST"),
                    ("rol-a", ["dev"], ["SQL", "PostgreSQL"], "Consultar datos con SQL"),
                    ("rol-a", ["dev"], ["PHP"], "Implementar endpoints en PHP"),
                    ("rol-b", ["soporte"], ["Soporte técnico"], "Resolver incidencias de soporte técnico"),
                    ("rol-b", ["soporte"], ["Ticketing"], "Gestionar tickets N1"),
                    ("rol-b", ["soporte"], ["Active Directory"], "Resetear credenciales en Active Directory"),
                    ("proj-a", ["dev"], ["PHP", "Angular"], "Construir el proyecto A con PHP y Angular"),
                ],
                start=1,
            )
        ]
    }
    skills = {
        "skills": [
            {"nombre": n, "nivel": "diario", "familias": f}
            for n, f in [
                ("HTML", ["dev"]),
                ("CSS", ["dev"]),
                ("JavaScript", ["dev"]),
                ("TypeScript", ["dev"]),
                ("Angular", ["dev"]),
                ("APIs REST", ["dev"]),
                ("PHP", ["dev"]),
                ("SQL", ["dev"]),
                ("PostgreSQL", ["dev"]),
                ("Soporte técnico", ["soporte"]),
                ("Ticketing", ["soporte"]),
                ("Active Directory", ["soporte"]),
            ]
        ]
    }
    familias = {
        "familias": [
            {
                "id": "dev",
                "nombre": "Desarrollo",
                "incluye_proyectos": True,
                "salario": {"min": 22000, "max": 28000},
            },
            {
                "id": "soporte",
                "nombre": "Soporte",
                "incluye_proyectos": False,
                "salario": {"min": 20000, "max": 23000},
            },
        ]
    }
    constraints = {
        "ubicacion": {
            "ciudad": "Valencia",
            "provincia": "Valencia",
            "pais": "España",
            "remoto": True,
            "hibrido": True,
            "presencial": "caso_a_caso",
            "traslado_confirmado": False,
        },
        "salario": {"alinear_a_rango_publicado": True},
        "knockout": {
            "anios_experiencia_max_aceptados": 4,
            "seniority_no_aplicar": ["senior", "lead", "architect", "manager"],
        },
    }

    files = {
        "perfil.yaml": perfil,
        "evidencias.yaml": evidencias,
        "skills.yaml": skills,
        "familias.yaml": familias,
        "constraints.yaml": constraints,
        "aliases.yaml": GENERIC_ALIASES,
    }
    files.update(overrides)
    for name, data in files.items():
        dump_yaml(base / name, data)
    return base
