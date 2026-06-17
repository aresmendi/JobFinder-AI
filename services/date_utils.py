import re
from datetime import date
from typing import Optional, Tuple

_ABSOLUTE = re.compile(r"(\d{2})/(\d{2})/(\d{4})")
_RELATIVE = re.compile(
    r"(?:hace\s+)?(\d+)?\s*"
    r"(hora|horas|hour|hours|d[ií]a|d[ií]as|day|days|semana|semanas|week|weeks|mes|meses|month|months)"
    r"(?:\s+ago)?",
    re.IGNORECASE,
)
_UNIT_TO_DAYS = {
    "hora": 0, "horas": 0, "hour": 0, "hours": 0,
    "día": 1, "dia": 1, "días": 1, "dias": 1, "day": 1, "days": 1,
    "semana": 7, "semanas": 7, "week": 7, "weeks": 7,
    "mes": 30, "meses": 30, "month": 30, "months": 30,
}

# Patrón estricto para buscar una frase de fecha dentro de un bloque de texto
# arbitrario (p. ej. el texto completo de una card), exigiendo "hace"/"ago" o
# "hoy"/"ayer" para evitar falsos positivos con números sueltos (salarios, etc.)
_PHRASE_IN_TEXT = re.compile(
    r"\d{2}/\d{2}/\d{4}"
    r"|hace\s+\d*\s*(?:hora|horas|d[ií]as?|semanas?|mes(?:es)?)"
    r"|\d+\s*(?:hours?|days?|weeks?|months?)\s+ago"
    r"|\b(?:hoy|today|ayer|yesterday)\b",
    re.IGNORECASE,
)


def find_posted_phrase(text: Optional[str]) -> Optional[str]:
    """Busca una frase de fecha reconocible dentro de un texto largo (p. ej. una
    card completa). Devuelve solo la frase encontrada, no el texto entero, para no
    contaminar posted_raw con contenido no relacionado con la fecha."""
    if not text:
        return None
    m = _PHRASE_IN_TEXT.search(text)
    return m.group(0) if m else None


def parse_posted_date(text: Optional[str], today: Optional[date] = None) -> Tuple[Optional[str], Optional[int]]:
    """Parsea un texto de fecha de oferta (absoluta dd/mm/aaaa o relativa "hace N días").

    Devuelve (texto_original, dias_transcurridos). Si no se reconoce el formato,
    dias_transcurridos es None (no se descarta la oferta, queda como fecha desconocida).
    """
    if not text:
        return None, None
    today = today or date.today()
    raw = text.strip()
    lowered = raw.lower()

    if "hoy" in lowered or "today" in lowered:
        return raw, 0
    if "ayer" in lowered or "yesterday" in lowered:
        return raw, 1

    m = _ABSOLUTE.search(raw)
    if m:
        day, month, year = (int(g) for g in m.groups())
        try:
            posted = date(year, month, day)
        except ValueError:
            return raw, None
        return raw, max((today - posted).days, 0)

    m = _RELATIVE.search(lowered)
    if m:
        amount = int(m.group(1)) if m.group(1) else 1
        unit_days = _UNIT_TO_DAYS.get(m.group(2))
        if unit_days is not None:
            return raw, amount * unit_days

    return raw, None
