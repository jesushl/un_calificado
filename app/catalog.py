ALLOWED_TRADES = frozenset(
    {
        "albanileria",
        "plomeria",
        "electricidad",
        "carpinteria",
        "herreria",
        "pintura",
        "pisos_azulejos",
        "vidrieria_canceleria",
        "tablaroca",
        "impermeabilizacion",
    }
)

PHONE_PATTERN = r"(?:\+?\d[\d\s().-]{7,}\d)"
ACTIVE_PROJECT_STATUSES = {
    "CONFIRMADA",
    "PROGRAMADO",
    "EN_PROCESO",
    "TERMINADO",
}
STATUS_TRANSITIONS = {
    "BORRADOR": {"CONFIRMADA"},
    "CONFIRMADA": {"PROGRAMADO"},
    "PROGRAMADO": {"EN_PROCESO"},
    "EN_PROCESO": {"TERMINADO"},
    "TERMINADO": {"CONCLUIDO", "EN_PROCESO"},
    "CONCLUIDO": set(),
}
