from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import yaml


def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"{path} no es un mapeo YAML")
    return data


def dump_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, allow_unicode=True, sort_keys=False)


def norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^a-z0-9+.# ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def tokens(text: str) -> list[str]:
    n = norm(text)
    return n.split() if n else []


def contains_seq(haystack: list[str], needle: list[str]) -> bool:
    if not needle or not haystack or len(needle) > len(haystack):
        return False
    n = len(needle)
    for i in range(len(haystack) - n + 1):
        if haystack[i : i + n] == needle:
            return True
    return False


def phrase_in_terms(phrase: str, terms: set[str]) -> bool:
    ptoks = tokens(phrase)
    if not ptoks:
        return False
    joined = " ".join(ptoks)
    if joined in terms:
        return True
    for term in terms:
        ttoks = term.split()
        if contains_seq(ttoks, ptoks) or contains_seq(ptoks, ttoks):
            return True
    return False


def phrase_in_text(phrase: str, text: str) -> bool:
    return contains_seq(tokens(text), tokens(phrase))


PLACEHOLDERS = {"", "pendiente", "null", "none"}


def is_placeholder(value) -> bool:
    if value is None:
        return True
    return str(value).strip().lower() in PLACEHOLDERS


def live_url(value) -> str | None:
    if is_placeholder(value):
        return None
    text = str(value).strip()
    return text or None


def contact_links(contacto: dict | None) -> list[str]:
    out: list[str] = []
    for key in ("linkedin", "github"):
        url = live_url((contacto or {}).get(key))
        if url:
            out.append(url)
    return out


def cert_label(item) -> str | None:
    """Etiqueta legible de una certificación (`nombre` canónico; `titulo` compat)."""
    if isinstance(item, str):
        text = item.strip()
        return None if is_placeholder(text) else text
    if not isinstance(item, dict):
        return None
    raw = item.get("nombre")
    if is_placeholder(raw):
        raw = item.get("titulo")
    if is_placeholder(raw):
        return None
    text = str(raw).strip()
    return text or None


def normalize_cert(item) -> dict | None:
    """Normaliza a `{nombre, entidad?}`; None si es placeholder o vacío."""
    label = cert_label(item)
    if not label:
        return None
    out: dict = {"nombre": label}
    if isinstance(item, dict):
        entidad = item.get("entidad")
        if entidad is not None and not is_placeholder(entidad):
            text = str(entidad).strip()
            if text:
                out["entidad"] = text
    return out


def normalize_certs(items) -> list[dict]:
    out: list[dict] = []
    for item in items or []:
        normalized = normalize_cert(item)
        if normalized:
            out.append(normalized)
    return out
