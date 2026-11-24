"""Búsqueda local del índice: nombre, oficio, zona y texto de obra."""

from __future__ import annotations

import re
import unicodedata

from .catalog import ALLOWED_TRADES

TRADE_LABELS: dict[str, str] = {
    "albanileria": "albañilería albaileria albañil albañiles muro aplanado",
    "plomeria": "plomería plomeria plomero plomeros fuga tinaco tinacos",
    "electricidad": "electricidad eléctrico electrico electricista short instalación",
    "carpinteria": "carpintería carpinteria carpintero mueble madera",
    "herreria": "herrería herreria herrero reja cancel soldadura",
    "pintura": "pintura pintor pintar impermeable",
    "pisos_azulejos": "pisos azulejos loseta ceramica cerámica",
    "vidrieria_canceleria": "vidriería vidrieria cancelería canceleria cristal ventana",
    "tablaroca": "tablaroca drywall plafón plafon",
    "impermeabilizacion": "impermeabilización impermeabilizacion filtración filtracion azotea",
}

_TOKEN = re.compile(r"[a-z0-9ñ]+", re.IGNORECASE)


def normalize(text: str | None) -> str:
    raw = (text or "").strip().lower()
    if not raw:
        return ""
    folded = unicodedata.normalize("NFKD", raw)
    without_marks = "".join(ch for ch in folded if not unicodedata.combining(ch))
    return without_marks.replace("ñ", "n")


def tokens(text: str | None) -> list[str]:
    return _TOKEN.findall(normalize(text))


def trade_haystack(trade_ids: list[str] | tuple[str, ...] | set[str]) -> str:
    parts = []
    for trade in trade_ids:
        parts.append(trade)
        parts.append(TRADE_LABELS.get(trade, ""))
    return " ".join(parts)


def matches_query(query: str | None, *fields: str | None) -> bool:
    """True si todos los tokens de la consulta aparecen en el texto unido de los campos."""
    needle = tokens(query)
    if not needle:
        return True
    haystack = normalize(" ".join(field or "" for field in fields))
    return all(token in haystack for token in needle)


def provider_matches(query: str | None, provider) -> bool:
    trade_ids = [item.trade for item in provider.trades]
    zones = [item.zone for item in provider.coverage]
    return matches_query(
        query,
        provider.name,
        provider.general_availability,
        provider.modality.value if getattr(provider, "modality", None) else "",
        " ".join(zones),
        trade_haystack(trade_ids),
        " ".join(trade_ids),
    )


def work_matches(query: str | None, work: dict) -> bool:
    provider = work.get("provider") or {}
    return matches_query(
        query,
        work.get("expectedOutcome"),
        work.get("approximateZone"),
        work.get("trade"),
        trade_haystack([work.get("trade") or ""]),
        provider.get("name"),
        " ".join(provider.get("coverage") or []),
        trade_haystack(provider.get("trades") or []),
    )


def resolve_trade_hint(query: str | None) -> str | None:
    """Si la consulta apunta a un solo oficio del catálogo, lo sugiere (opcional)."""
    needle = normalize(query)
    if not needle:
        return None
    hits = [
        trade
        for trade in ALLOWED_TRADES
        if trade in needle or any(token in needle for token in tokens(TRADE_LABELS.get(trade, "")))
    ]
    return hits[0] if len(hits) == 1 else None
