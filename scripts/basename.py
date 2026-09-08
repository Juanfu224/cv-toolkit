from __future__ import annotations

import re
import unicodedata

PARTICLES = {"de", "del", "la", "las", "los", "y", "da", "do", "dos", "das", "van", "von"}


def strip_accents(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text or "")
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))


def pascal_nombre(nombre: str) -> str:
    words = re.findall(r"[A-Za-z]+", strip_accents(nombre))
    words = [w for w in words if w.lower() not in PARTICLES]
    if len(words) > 3:
        words = words[:3]
    return "".join(w[:1].upper() + w[1:] for w in words) or "Candidato"


def slug_part(text: str) -> str:
    s = strip_accents(text or "")
    s = re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")
    return s[:40] or "X"


def send_basename(nombre: str, puesto: str, empresa: str) -> str:
    return f"CV_{pascal_nombre(nombre)}_{slug_part(puesto)}_{slug_part(empresa)}"
