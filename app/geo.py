"""Zonas aproximadas (alcaldías) y radio de descubrimiento. Sin domicilio exacto."""

from __future__ import annotations

import math
import unicodedata
from typing import Iterable

# Centroides aproximados de alcaldías de la CDMX. No son un domicilio.
ZONES: dict[str, tuple[float, float]] = {
    "Álvaro Obregón": (19.3570, -99.2030),
    "Azcapotzalco": (19.4870, -99.1860),
    "Benito Juárez": (19.3720, -99.1610),
    "Coyoacán": (19.3467, -99.1617),
    "Cuajimalpa": (19.3570, -99.3000),
    "Cuauhtémoc": (19.4420, -99.1450),
    "Gustavo A. Madero": (19.4830, -99.1110),
    "Iztacalco": (19.3960, -99.0980),
    "Iztapalapa": (19.3570, -99.0930),
    "La Magdalena Contreras": (19.3220, -99.2410),
    "Miguel Hidalgo": (19.4070, -99.1910),
    "Milpa Alta": (19.1920, -99.0230),
    "Tláhuac": (19.2700, -99.0050),
    "Tlalpan": (19.2880, -99.1670),
    "Venustiano Carranza": (19.4190, -99.1140),
    "Xochimilco": (19.2570, -99.1040),
}

MIN_DISTANCE_KM = 2
MAX_DISTANCE_KM = 50
DEFAULT_DISTANCE_KM = 15


def slug(value: str | None) -> str:
    nfkd = unicodedata.normalize("NFKD", value or "")
    stripped = "".join(ch for ch in nfkd if not unicodedata.combining(ch))
    return " ".join(stripped.casefold().split())


_SLUGS = {slug(name): name for name in ZONES}


def canonical_zone(value: str | None) -> str | None:
    if not value or not value.strip():
        return None
    known = _SLUGS.get(slug(value))
    if known:
        return known
    cleaned = " ".join(value.split())
    return cleaned[:160] if cleaned else None


def zone_catalog() -> list[dict]:
    return [{"id": name, "label": name} for name in ZONES]


def coords(value: str | None) -> tuple[float, float] | None:
    name = _SLUGS.get(slug(value))
    if name is None:
        return None
    return ZONES[name]


def haversine_km(origin: tuple[float, float], target: tuple[float, float]) -> float:
    lat1, lon1 = origin
    lat2, lon2 = target
    radius = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlamb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlamb / 2) ** 2
    return round(2 * radius * math.asin(math.sqrt(a)), 1)


def min_distance_km(origin: str | None, coverage: Iterable[str]) -> float | None:
    start = coords(origin)
    zones = list(coverage)
    if start is None:
        if origin and any(slug(item) == slug(origin) for item in zones):
            return 0.0
        return None
    distances = []
    for item in zones:
        point = coords(item)
        if point is None:
            if slug(item) == slug(origin):
                distances.append(0.0)
            continue
        distances.append(haversine_km(start, point))
    if not distances:
        return None
    return min(distances)


def within_radius(
    origin: str | None, radius_km: int, coverage: Iterable[str]
) -> tuple[bool, float | None]:
    if not origin:
        return True, None
    distance = min_distance_km(origin, coverage)
    if distance is None:
        return False, None
    return distance <= radius_km, distance


def clamp_radius(value: int | None) -> int:
    if value is None:
        return DEFAULT_DISTANCE_KM
    return max(MIN_DISTANCE_KM, min(MAX_DISTANCE_KM, int(value)))
