"""The SQLAlchemy unit of work: one session, one transaction, three repositories."""

from __future__ import annotations

from types import TracebackType

from sqlalchemy.orm import Session, sessionmaker

from forgeml.application.unit_of_work import UnitOfWork
from forgeml.infrastructure.database.repositories import (
    SqlAlchemyAuditLog,
    SqlAlchemyDeploymentRepository,
    SqlAlchemyOperationStore,
    SqlAlchemyPackageCatalog,
)


class SqlAlchemyUnitOfWork(UnitOfWork):
    """One atomic metadata transaction.

    All three repositories are built from the same Session, which is what makes
    "persist the validation, transition the package, and append the audit event"
    a single transaction rather than three writes that can partially succeed.

    Exiting without committing rolls back. That is the safe default: a use case
    that raises halfway through must leave no trace, and a use case that simply
    forgets to commit must not silently persist.
    """

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory
        self._session: Session | None = None

    def __enter__(self) -> SqlAlchemyUnitOfWork:
        self._session = self._session_factory()
        self.packages = SqlAlchemyPackageCatalog(self._session)
        self.operations = SqlAlchemyOperationStore(self._session)
        self.audit = SqlAlchemyAuditLog(self._session)
        self.deployments = SqlAlchemyDeploymentRepository(self._session)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        try:
            self.rollback()
        finally:
            self._active.close()
            self._session = None

    def commit(self) -> None:
        self._active.commit()

    def rollback(self) -> None:
        self._active.rollback()

    @property
    def _active(self) -> Session:
        if self._session is None:
            raise RuntimeError("the unit of work is not open")
        return self._session
