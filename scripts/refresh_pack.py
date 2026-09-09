from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from basename import send_basename
from common import dump_yaml, is_placeholder, load_yaml
from factcheck import run_factcheck
from match import run_match
from pack_cv import pack
from paths import BASE, is_allowed_output
from render_cv import apply_perfil, to_docx, to_markdown, to_pdf
from render_respuestas import render_respuestas
from verify_pdf import extract, verify_ats


def _meta_puesto_empresa(pack_dir: Path) -> tuple[str, str]:
    puesto = ""
    empresa = ""
    meta_path = pack_dir / "meta.yaml"
    if meta_path.exists():
        meta = load_yaml(meta_path)
        puesto = str(meta.get("puesto") or "")
        empresa = str(meta.get("empresa") or "")
    jd_path = pack_dir / "jd.yaml"
    if jd_path.exists():
        jd = load_yaml(jd_path)
        if not puesto:
            puesto = str(jd.get("titulo") or "")
        if not empresa:
            empresa = str(jd.get("empresa") or "")
    return puesto or "Puesto", empresa or "Empresa"


def _mark_editado(pack_dir: Path) -> None:
    meta_path = pack_dir / "meta.yaml"
    meta = load_yaml(meta_path) if meta_path.exists() else {}
    meta["pack_estado"] = "editado"
    meta["listo_para_enviar"] = False
    dump_yaml(meta_path, meta)


def refresh_pack(pack_dir: Path, base: Path | None = None) -> dict:
    """Re-empaqueta el pack tras una edición HITL. Deja pack_estado=editado."""
    base = base or BASE
    pack_dir = Path(pack_dir)
    cv_path = pack_dir / "cv.yaml"
    if not cv_path.exists():
        raise SystemExit(f"refresh: no existe {cv_path}")

    perfil = load_yaml(base / "perfil.yaml")
    cv = apply_perfil(load_yaml(cv_path), base=base)

    gaps_path = pack_dir / "gaps.yaml"
    gaps = load_yaml(gaps_path) if gaps_path.exists() else None
    aliases_path = base / "aliases.yaml"
    aliases = load_yaml(aliases_path) if aliases_path.exists() else {}

    packed, report = pack(cv, gaps=gaps, aliases=aliases)
    dump_yaml(cv_path, packed)
    dump_yaml(pack_dir / "pack_report.yaml", report)

    md_path = pack_dir / "curriculum.md"
    pdf_path = pack_dir / "curriculum.pdf"
    docx_path = pack_dir / "curriculum.docx"
    md_path.write_text(to_markdown(packed), encoding="utf-8")
    to_pdf(packed, pdf_path)
    to_docx(packed, docx_path)

    nombre = perfil.get("nombre") or ""
    if not is_placeholder(nombre):
        puesto, empresa = _meta_puesto_empresa(pack_dir)
        send = send_basename(str(nombre), puesto, empresa)
        for ext in (".pdf", ".docx", ".md"):
            src = pack_dir / f"curriculum{ext}"
            if src.exists():
                shutil.copy2(src, pack_dir / f"{send}{ext}")

    extract_path = pack_dir / "_extract.txt"
    try:
        extract_path.write_text(extract(pdf_path), encoding="utf-8")
    except Exception:  # noqa: BLE001 — PDF corrupto / ilegible
        extract_path.write_text("", encoding="utf-8")

    verify_errors = verify_ats(pdf_path, perfil)
    if verify_errors:
        _mark_editado(pack_dir)
        raise SystemExit(
            "refresh: verify falló:\n" + "\n".join(f"  - {e}" for e in verify_errors)
        )

    jd_path = pack_dir / "jd.yaml"
    if jd_path.exists():
        jd = load_yaml(jd_path)
        forzar = False
        ver_prev = pack_dir / "veredicto.yaml"
        if ver_prev.exists():
            forzar = bool(load_yaml(ver_prev).get("forzar"))
        gaps_new, veredicto = run_match(
            jd, cv=packed, base_dir=base, forzar=forzar
        )
        dump_yaml(gaps_path, gaps_new)
        dump_yaml(pack_dir / "veredicto.yaml", veredicto)

    resp_data = pack_dir / "respuestas_data.yaml"
    if resp_data.exists():
        text = render_respuestas(load_yaml(resp_data))
        (pack_dir / "respuestas.md").write_text(text, encoding="utf-8")

    fc = run_factcheck(pack_dir, base)
    dump_yaml(pack_dir / "factcheck.yaml", fc)
    _mark_editado(pack_dir)

    return {
        "pack_estado": "editado",
        "factcheck_ok": bool(fc.get("ok")),
        "pages": report.get("pages"),
        "pdf": str(pdf_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Re-empaqueta candidaturas/<slug>/ tras editar "
            "(pack→render→verify→match→respuestas→factcheck; HITL → editado)"
        )
    )
    parser.add_argument("--dir", required=True, type=Path, help="Carpeta de la candidatura")
    parser.add_argument("--base", type=Path, help="Vault alternativo (tests)")
    args = parser.parse_args()
    if not is_allowed_output(args.dir):
        print("refresh: --dir fuera del repo o tmp", file=sys.stderr)
        return 1
    result = refresh_pack(args.dir, args.base)
    status = "ok" if result["factcheck_ok"] else "FAIL"
    print(
        f"refresh: DONE  pack_estado={result['pack_estado']}  "
        f"páginas={result.get('pages')}  "
        f"factcheck={status}"
    )
    print(f"escrito {result['pdf']}")
    return 0 if result["factcheck_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
