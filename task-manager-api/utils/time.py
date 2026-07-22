from datetime import UTC, datetime


def utc_now():
    return datetime.now(UTC)


def as_utc(value):
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def is_overdue(due_date, status, now=None):
    if due_date is None or status in {"done", "cancelled"}:
        return False
    return as_utc(due_date) < as_utc(now or utc_now())
