from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from basename import send_basename
from common import is_placeholder, load_yaml
from familias import default_cv_path, familia_ids
from paths import BASE, CANDIDATURAS, CV_DIR, PLANTILLAS, ROOT, TABLERO
from validate_base import validate

PY = sys.executable
SCRIPTS = Path(__file__).resolve().parent
TESTS = ROOT / "tests"


def _run(args: list[str]) -> int:
    proc = subprocess.run(args, cwd=ROOT)
    return proc.returncode


def cmd_validate(_args: argparse.Namespace) -> int:
    return validate()


def _familia_cv(familia: str) -> Path:
    path = default_cv_path(PLANTILLAS, familia)
    if not path.exists():
        known = ", ".join(p.stem.replace("cv_default_", "") for p in PLANTILLAS.glob("cv_default_*.yaml"))
        raise SystemExit(
            f"no existe {path.name}. Familias con plantilla: {known or '(ninguna; ejecuta cvtool scaffold)'}"
        )
    return path


def cmd_render(args: argparse.Namespace) -> int:
    copy_yaml = False
    if args.cv:
        cv = Path(args.cv)
        if not cv.exists():
            raise SystemExit(f"no existe {cv}")
    elif args.familia:
        cv = _familia_cv(args.familia)
        copy_yaml = True
    else:
        raise SystemExit("render requiere --familia o --cv")
    out = args.out_dir or CV_DIR
    code = _run(
        [
            PY,
            str(SCRIPTS / "render_cv.py"),
            "--cv",
            str(cv),
            "--out-dir",
            str(out),
            "--basename",
            args.basename,
        ]
    )
    if code == 0 and copy_yaml:
        dest = Path(out) / "cv.yaml"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(cv, dest)
        print(f"copiado {dest}")
    return code


def cmd_verify(args: argparse.Namespace) -> int:
    pdf = args.pdf or (CV_DIR / "curriculum.pdf")
    cmd = [PY, str(SCRIPTS / "verify_pdf.py"), str(pdf)]
    if args.out:
        cmd.extend(["--out", str(args.out)])
    return _run(cmd)


def cmd_test(_args: argparse.Namespace) -> int:
    return _run(
        [PY, "-m", "unittest", "discover", "-s", str(TESTS), "-p", "test_*.py", "-v"]
    )


def cmd_salary(args: argparse.Namespace) -> int:
    cmd = [PY, str(SCRIPTS / "suggest_salary.py"), "--familia", args.familia]
    if args.oferta_min is not None:
        cmd.extend(["--oferta-min", str(args.oferta_min)])
    if args.oferta_max is not None:
        cmd.extend(["--oferta-max", str(args.oferta_max)])
    return _run(cmd)


def cmd_scaffold(_args: argparse.Namespace) -> int:
    return _run([PY, str(SCRIPTS / "scaffold_defaults.py")])


def cmd_basename(args: argparse.Namespace) -> int:
    perfil = load_yaml(BASE / "perfil.yaml")
    nombre = perfil.get("nombre") or ""
    if is_placeholder(nombre):
        raise SystemExit("perfil.nombre está vacío; inicializa la base primero")
    print(send_basename(nombre, args.puesto, args.empresa))
    return 0


def cmd_match(args: argparse.Namespace) -> int:
    cmd = [PY, str(SCRIPTS / "match.py"), "--jd", str(args.jd)]
    if args.cv:
        cmd.extend(["--cv", str(args.cv)])
    if args.out:
        cmd.extend(["--out", str(args.out)])
    if args.veredicto:
        cmd.extend(["--veredicto", str(args.veredicto)])
    if args.base:
        cmd.extend(["--base", str(args.base)])
    return _run(cmd)


def cmd_copy(args: argparse.Namespace) -> int:
    dest = args.to_dir or CV_DIR
    return _run(
        [
            PY,
            str(SCRIPTS / "copy_to_cv.py"),
            "--from-dir",
            str(args.from_dir),
            "--to-dir",
            str(dest),
        ]
    )


def cmd_tablero(args: argparse.Namespace) -> int:
    cmd = [PY, str(SCRIPTS / "tablero.py"), args.accion]
    if args.accion == "set":
        cmd.extend(["--slug", args.slug, "--estado", args.estado])
        if args.empresa:
            cmd.extend(["--empresa", args.empresa])
        if args.puesto:
            cmd.extend(["--puesto", args.puesto])
        if args.enviada:
            cmd.extend(["--enviada", args.enviada])
        if args.seguimiento:
            cmd.extend(["--seguimiento", args.seguimiento])
        if args.notas:
            cmd.extend(["--notas", args.notas])
    return _run(cmd)


def _origen_files() -> dict[str, Path]:
    origen = BASE / "origen"
    found = {}
    for name in ("curriculum.md", "curriculum.pdf", "presentacion.md"):
        path = origen / name
        if path.exists() and path.stat().st_size > 0:
            found[name] = path
    return found


def cmd_init(_args: argparse.Namespace) -> int:
    origen = _origen_files()
    print("Checklist de inicialización")
    print(f"  curriculum.md: {'sí' if 'curriculum.md' in origen else 'NO'}")
    print(f"  curriculum.pdf: {'sí' if 'curriculum.pdf' in origen else 'no'}")
    print(f"  presentacion.md: {'sí' if 'presentacion.md' in origen else 'NO (opcional)'}")
    if "curriculum.md" not in origen and "curriculum.pdf" not in origen:
        print("Falta CV en base/origen/. Copia curriculum.md o curriculum.pdf y di: inicializa mi base")
        return 1
    print("Siguiente paso: en Cursor, escribe «inicializa mi base».")
    print("El agente extrae hechos a base/*.yaml. Luego: cvtool scaffold && cvtool validate")
    return 0


def cmd_status(_args: argparse.Namespace) -> int:
    perfil = load_yaml(BASE / "perfil.yaml")
    code = validate()
    estado = {0: "listo", 1: "inconsistente", 2: "vacío"}.get(code, "desconocido")
    print(f"vault: {estado}")
    print(f"nombre: {perfil.get('nombre')}")
    print(f"familias: {', '.join(familia_ids()) or '(ninguna)'}")
    defaults = sorted(p.name for p in PLANTILLAS.glob("cv_default_*.yaml"))
    print(f"plantillas: {', '.join(defaults) or '(ninguna)'}")
    origen = _origen_files()
    print(f"origen: {', '.join(origen) or '(vacío)'}")
    slugs = sorted(
        p.name
        for p in CANDIDATURAS.iterdir()
        if p.is_dir() and p.name[:1].isdigit()
    )
    print(f"candidaturas: {len(slugs)}" + (f" (última {slugs[-1]})" if slugs else ""))
    if TABLERO.exists():
        from tablero import list_rows

        rows = list_rows()
        enviadas = sum(1 for r in rows if r.get("estado") == "enviada")
        print(f"tablero: {len(rows)} filas, {enviadas} enviadas")
    if code == 2:
        print("siguiente: copia CV a base/origen/ y di «inicializa mi base»")
    elif code == 0:
        print("siguiente: pega una oferta en oferta/ y di «genera candidatura»")
    return 0 if code != 1 else 1


def cmd_doctor(_args: argparse.Namespace) -> int:
    from doctor import run_doctor

    return run_doctor()


def cmd_respuestas(args: argparse.Namespace) -> int:
    return _run(
        [
            PY,
            str(SCRIPTS / "render_respuestas.py"),
            "--data",
            str(args.data),
            "--out",
            str(args.out),
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="CLI del sistema de candidaturas")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("validate", help="Valida el vault en base/")
    sub.add_parser("status", help="Resumen del vault, plantillas y tablero")
    sub.add_parser("doctor", help="Chequeo de salud (Python, deps, WeasyPrint, vault)")
    sub.add_parser("scaffold", help="Genera cv_default_<familia>.yaml desde el vault")
    sub.add_parser("test", help="Ejecuta la suite unittest")

    sub.add_parser("init", help="Comprueba base/origen/ antes de inicializar")

    p_render = sub.add_parser("render", help="Renderiza un CV (default de familia o --cv)")
    p_render.add_argument("--familia")
    p_render.add_argument("--cv", type=Path, help="cv.yaml adaptado (candidatura)")
    p_render.add_argument("--out-dir", type=Path)
    p_render.add_argument("--basename", default="curriculum")

    p_match = sub.add_parser("match", help="Match determinista oferta vs vault")
    p_match.add_argument("--jd", required=True, type=Path)
    p_match.add_argument("--cv", type=Path)
    p_match.add_argument("--out", type=Path)
    p_match.add_argument("--veredicto", type=Path)
    p_match.add_argument("--base", type=Path)

    p_copy = sub.add_parser("copy", help="Copia la candidatura a cv/")
    p_copy.add_argument("--from-dir", required=True, type=Path)
    p_copy.add_argument("--to-dir", type=Path)

    p_resp = sub.add_parser("respuestas", help="Renderiza respuestas.md desde YAML")
    p_resp.add_argument("--data", required=True, type=Path)
    p_resp.add_argument("--out", required=True, type=Path)

    p_verify = sub.add_parser("verify", help="Comprueba el PDF ATS")
    p_verify.add_argument("pdf", nargs="?", type=Path)
    p_verify.add_argument("--out", type=Path)

    p_sal = sub.add_parser("salary", help="Sugiere rango salarial para respuestas")
    p_sal.add_argument("--familia", required=True)
    p_sal.add_argument("--oferta-min", type=int)
    p_sal.add_argument("--oferta-max", type=int)

    p_base = sub.add_parser("basename", help="Nombre de archivo de envío")
    p_base.add_argument("--puesto", required=True)
    p_base.add_argument("--empresa", required=True)

    p_tab = sub.add_parser("tablero", help="Lista o actualiza el tablero")
    p_tab.add_argument("accion", choices=("list", "set"))
    p_tab.add_argument("--slug")
    p_tab.add_argument("--estado")
    p_tab.add_argument("--empresa")
    p_tab.add_argument("--puesto")
    p_tab.add_argument("--enviada")
    p_tab.add_argument("--seguimiento")
    p_tab.add_argument("--notas")

    args = parser.parse_args()
    if args.cmd == "tablero" and args.accion == "set":
        if not args.slug or not args.estado:
            raise SystemExit("tablero set requiere --slug y --estado")

    dispatch = {
        "validate": cmd_validate,
        "render": cmd_render,
        "match": cmd_match,
        "copy": cmd_copy,
        "respuestas": cmd_respuestas,
        "verify": cmd_verify,
        "test": cmd_test,
        "salary": cmd_salary,
        "scaffold": cmd_scaffold,
        "init": cmd_init,
        "status": cmd_status,
        "doctor": cmd_doctor,
        "basename": cmd_basename,
        "tablero": cmd_tablero,
    }
    return dispatch[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
