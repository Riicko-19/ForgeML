"""Reading durable operations (ADR-006: clients poll an operation resource)."""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from forgeml.application.unit_of_work import UnitOfWork
from forgeml.core.errors import AppError, ErrorCategory
from forgeml.domain.operations.models import Operation

UnitOfWorkFactory = Callable[[], UnitOfWork]


class OperationService:
    """Reads operations for polling clients."""

    def __init__(self, unit_of_work: UnitOfWorkFactory) -> None:
        self._unit_of_work = unit_of_work

    def get(self, operation_id: UUID) -> Operation:
        with self._unit_of_work() as uow:
            operation = uow.operations.get(operation_id)
        if operation is None:
            raise AppError(
                category=ErrorCategory.NOT_FOUND,
                code="operation_not_found",
                message="the referenced operation does not exist",
            )
        return operation
