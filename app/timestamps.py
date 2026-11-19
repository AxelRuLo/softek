"""UTC clock shared by ORM timestamp defaults and update hooks."""

from datetime import UTC, datetime


def utc_now() -> datetime:
    return datetime.now(UTC)
