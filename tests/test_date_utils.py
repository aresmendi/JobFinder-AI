from datetime import date

from services.date_utils import parse_posted_date

TODAY = date(2026, 6, 17)


def test_none_text():
    assert parse_posted_date(None) == (None, None)


def test_today():
    raw, days = parse_posted_date("Hoy", today=TODAY)
    assert days == 0


def test_yesterday():
    raw, days = parse_posted_date("Ayer", today=TODAY)
    assert days == 1


def test_absolute_date_same_day():
    raw, days = parse_posted_date("17/06/2026", today=TODAY)
    assert raw == "17/06/2026"
    assert days == 0


def test_absolute_date_past():
    raw, days = parse_posted_date("10/06/2026", today=TODAY)
    assert days == 7


def test_relative_days_spanish():
    raw, days = parse_posted_date("Hace 3 días", today=TODAY)
    assert days == 3


def test_relative_days_english():
    raw, days = parse_posted_date("3 days ago", today=TODAY)
    assert days == 3


def test_relative_weeks():
    raw, days = parse_posted_date("Hace 2 semanas", today=TODAY)
    assert days == 14


def test_relative_hours_counts_as_today():
    raw, days = parse_posted_date("Hace 5 horas", today=TODAY)
    assert days == 0


def test_unrecognized_format_keeps_raw_text():
    raw, days = parse_posted_date("Fecha desconocida", today=TODAY)
    assert raw == "Fecha desconocida"
    assert days is None
