"""
models.py — The blueprint for our PostgreSQL tables.

SQLAlchemy reads these Python classes and knows exactly what columns to
create in Postgres. Think of this file like the architect's floor plan —
the actual building (real table in Postgres) gets constructed from it
when the app starts up.

We use one application table here:
  - `scans` stores one complete domain scan per row

Authentication users live in app.auth.users.AuthUser because FastAPI Users
owns that table shape.
"""

from datetime import datetime
from sqlalchemy import Column, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Base is the starting point every table class must inherit from.
    SQLAlchemy uses it to track all the tables we've defined so it
    knows what to create in the database.

    Think of Base like a school register — every class (table) signs in
    here so SQLAlchemy knows they exist.
    """
    pass


class ScanRecord(Base):
    """
    Maps directly to the `scans` table in PostgreSQL.

    Column breakdown:
    ─────────────────────────────────────────────────────────────────
    id           → the scan's UUID (primary key — unique identifier,
                   like a student ID number, no two are the same)

    domain       → the target domain e.g. "google.com"
                   index=True builds a lookup shortcut so queries like
                   "find all scans for google.com" run in microseconds
                   instead of reading every row

    status       → "running" | "complete" | "failed"
                   tells the frontend what state the scan is in

    started_at   → UTC datetime the scan kicked off

    completed_at → UTC datetime the scan finished (None while running)

    duration_ms  → how many milliseconds the full scan took
                   (None while running, set on completion)

    result_json  → the ENTIRE ScanResult object serialised to a JSON
                   string. Storing it here means one DB read gives us
                   everything — no joins, no extra queries.
                   Text column = unlimited length (unlike VARCHAR)
    ─────────────────────────────────────────────────────────────────

    __table_args__ adds a COMPOSITE INDEX on (domain, started_at).
    Composite = multiple columns together. This turbocharges the
    most common real-world query: "show me all scans for X, newest first".
    Without it Postgres reads every row. With it, it jumps straight there.
    """

    __tablename__ = "scans"

    id           = Column(String(36),  primary_key=True, nullable=False)
    domain       = Column(String(255), nullable=False,   index=True)
    status       = Column(String(20),  nullable=False,   default="running")
    started_at   = Column(DateTime,    nullable=False,   default=datetime.utcnow)
    completed_at = Column(DateTime,    nullable=True)
    duration_ms  = Column(Integer,     nullable=True)
    result_json  = Column(Text,        nullable=False,   default="{}")

    # Composite index: speeds up "give me scans for domain X, ordered newest first"
    # This is the #1 query pattern for the history sidebar in the frontend.
    __table_args__ = (
        Index("ix_scans_domain_started_at", "domain", "started_at"),
    )

    def __repr__(self) -> str:
        """Friendly string when you print a ScanRecord — useful for debugging."""
        return (
            f"<ScanRecord id={self.id!r} domain={self.domain!r} "
            f"status={self.status!r}>"
        )
