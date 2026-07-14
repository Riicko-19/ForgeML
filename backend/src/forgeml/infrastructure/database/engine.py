"""Engine and session factory for the metadata database (ADR-009)."""

from __future__ import annotations

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from forgeml.core.config import AppSettings


def create_database_engine(settings: AppSettings) -> Engine:
    """Build the metadata engine from typed settings.

    `pool_pre_ping` costs one round trip per checkout and buys immunity to
    connections killed by a restarted database or an idle-timeout proxy, which
    is the difference between a self-healing control plane and one that serves
    stale-connection errors until it is restarted.
    """

    return create_engine(
        settings.require_database_url(),
        pool_size=settings.database_pool_size,
        pool_pre_ping=True,
        future=True,
        connect_args={
            # A pathological query cannot pin a control-plane connection forever.
            "options": f"-c statement_timeout={settings.database_statement_timeout_ms}"
        },
    )


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Session factory for the unit of work.

    `expire_on_commit=False` is deliberate: repositories map rows to immutable
    domain records before returning them, so nothing outside this package holds
    an ORM object that could emit a lazy load after commit.
    """

    return sessionmaker(bind=engine, expire_on_commit=False, future=True)
