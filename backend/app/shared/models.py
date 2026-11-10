from datetime import datetime, timezone

from ..extensions import db


def utcnow():
    """UTC naive, seguro para columnas DATETIME de MySQL."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TimestampMixin:
    """Añade created_at / updated_at a cualquier modelo."""

    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )