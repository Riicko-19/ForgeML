"""Lazy database lifecycle: engine, unit of work factory, and readiness.

The composition root wires this and never touches SQLAlchemy itself, which is
what keeps the ORM confined to this package (and the architecture test honest).

The engine is built on first use, not at import. Constructing the application
must not require a database -- the packaged wheel is smoke tested without one --
but any request that needs the metadata layer must fail closed when it is
absent rather than pretend to work.
"""

from __future__ import annotations

from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from forgeml.application.unit_of_work import UnitOfWork
from forgeml.core.config import AppSettings, ConfigurationFailure
from forgeml.core.errors import AppError, ErrorCategory
from forgeml.infrastructure.database.engine import (
    create_database_engine,
    create_session_factory,
)
from forgeml.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


def _unavailable(error: Exception) -> AppError:
    return AppError(
        category=ErrorCategory.DEPENDENCY_UNAVAILABLE,
        code="dependency_unavailable",
        message="The metadata database is unavailable.",
    )


class DatabaseProvider:
    """Owns the engine and hands out units of work."""

    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self._engine: Engine | None = None
        self._session_factory: sessionmaker[Session] | None = None

    def unit_of_work(self) -> UnitOfWork:
        return SqlAlchemyUnitOfWork(self._factory())

    def recover_orphaned_operations(self) -> int:
        """Return operations abandoned by a previous process to the queue.

        ADR-016. This is the only caller: recovery that never runs is a comment,
        and an operation stranded in RUNNING is one a client polls forever.
        """

        with self.unit_of_work() as uow:
            recovered = uow.operations.recover_orphaned()
            uow.commit()
        return recovered

    def check_readiness(self) -> None:
        """Prove the database answers, or refuse to report ready.

        A readiness probe that does not check its own database is a lie, and an
        operator who trusts it routes traffic at a control plane that cannot
        serve it.
        """

        try:
            with self._connect().connect() as connection:
                connection.execute(text("SELECT 1"))
        except (ConfigurationFailure, SQLAlchemyError, AppError) as error:
            raise _unavailable(error) from error

    def dispose(self) -> None:
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None

    def _factory(self) -> sessionmaker[Session]:
        if self._session_factory is None:
            self._session_factory = create_session_factory(self._connect())
        return self._session_factory

    def _connect(self) -> Engine:
        if self._engine is None:
            try:
                self._engine = create_database_engine(self._settings)
            except ConfigurationFailure as error:
                raise _unavailable(error) from error
        return self._engine
