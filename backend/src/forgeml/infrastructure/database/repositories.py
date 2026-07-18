"""PostgreSQL implementations of the package, operation, and audit ports.

Concurrency is delegated to PostgreSQL, never to application checks. Two
concurrent uploads of identical bytes both pass a "does it exist?" test and both
insert; only a unique index can arbitrate. Every idempotent write below is
therefore an insert that expects to lose the race sometimes, catches the
constraint violation on a savepoint, and reads the winner's row.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, literal, select, tuple_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from forgeml.core.errors import AppError, ErrorCategory
from forgeml.domain.audit.models import AuditEvent
from forgeml.domain.deployment.models import (
    Deployment,
    DeploymentVersion,
    DesiredState,
)
from forgeml.domain.deployment.ports import DeploymentPage
from forgeml.domain.identity.models import ApiKey
from forgeml.domain.operations.models import (
    MAX_ATTEMPTS,
    Operation,
    OperationFailure,
    OperationState,
    OperationType,
)
from forgeml.domain.package.models import (
    Package,
    PackageState,
    PackageValidation,
)
from forgeml.domain.package.ports import PackagePage
from forgeml.infrastructure.database import mappers
from forgeml.infrastructure.database.models import (
    ApiKeyRow,
    AuditEventRow,
    DeploymentRow,
    DeploymentVersionRow,
    OperationRow,
    PackageRow,
    PackageValidationRow,
)

ABANDONED = "operation_abandoned"


def _not_found(what: str) -> AppError:
    return AppError(
        category=ErrorCategory.NOT_FOUND,
        code=f"{what}_not_found",
        message=f"the referenced {what.replace('_', ' ')} does not exist",
    )


def _conflict(code: str, message: str) -> AppError:
    return AppError(category=ErrorCategory.CONFLICT, code=code, message=message)


def _encode_cursor(created_at: datetime, identifier: UUID) -> str:
    return f"{created_at.isoformat()}|{identifier}"


def _decode_cursor(cursor: str) -> tuple[datetime, UUID]:
    try:
        timestamp, identifier = cursor.split("|", 1)
        return datetime.fromisoformat(timestamp), UUID(identifier)
    except ValueError as error:
        raise AppError(
            category=ErrorCategory.BAD_REQUEST,
            code="cursor_invalid",
            message="the supplied pagination cursor is not valid",
        ) from error


class SqlAlchemyPackageCatalog:
    """Package records backed by PostgreSQL."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_or_create(
        self, sha256: str, filename: str, size_bytes: int, artifact_uri: str
    ) -> Package:
        existing = self._by_checksum(sha256)
        if existing is not None:
            return mappers.to_package(existing)

        row = PackageRow(
            id=uuid4(),
            sha256=sha256,
            filename=filename,
            size_bytes=size_bytes,
            manifest_version=None,
            state=PackageState.DRAFT.value,
            artifact_uri=artifact_uri,
        )
        try:
            with self._session.begin_nested():
                self._session.add(row)
        except IntegrityError:
            # Another transaction inserted the same checksum between our read
            # and our write. The unique index arbitrated; read the winner.
            winner = self._by_checksum(sha256)
            if winner is None:  # pragma: no cover - unreachable under the index
                raise
            return mappers.to_package(winner)
        return mappers.to_package(row)

    def find_by_id(self, package_id: UUID) -> Package | None:
        row = self._session.get(PackageRow, package_id)
        return mappers.to_package(row) if row else None

    def find_by_checksum(self, sha256: str) -> Package | None:
        row = self._by_checksum(sha256)
        return mappers.to_package(row) if row else None

    def save_validation(self, package_id: UUID, validation: PackageValidation) -> None:
        package = self._session.get(PackageRow, package_id)
        if package is None:
            raise _not_found("package")

        findings = [mappers.finding_to_json(item) for item in validation.findings]
        manifest = mappers.manifest_to_json(validation.manifest)
        contract = mappers.contract_to_json(validation.contract)

        existing = self._session.execute(
            select(PackageValidationRow).where(
                PackageValidationRow.package_id == package_id,
                PackageValidationRow.validator_version == validation.validator_version,
            )
        ).scalar_one_or_none()

        if existing is None:
            self._session.add(
                PackageValidationRow(
                    id=uuid4(),
                    package_id=package_id,
                    validator_version=validation.validator_version,
                    state=validation.state.value,
                    findings=findings,
                    manifest=manifest,
                    contract=contract,
                )
            )
        else:
            # Re-running the same validator on the same package is idempotent:
            # it restates the verdict rather than accumulating history.
            existing.state = validation.state.value
            existing.findings = findings
            existing.manifest = manifest
            existing.contract = contract
            existing.completed_at = datetime.now(tz=UTC)

        package.state = PackageState.from_validation(validation.state).value
        package.manifest = manifest
        if validation.manifest is not None:
            # Only now has anything actually read the archive's format version.
            package.manifest_version = validation.manifest.forge_version
        self._session.flush()

    def list(self, limit: int, cursor: str | None = None) -> PackagePage:
        query = select(PackageRow).order_by(
            PackageRow.created_at.desc(), PackageRow.id.desc()
        )
        if cursor is not None:
            created_at, identifier = _decode_cursor(cursor)
            # Row-value comparison, not two ANDed predicates: it is the only
            # form that keeps the keyset stable when two packages share a
            # created_at, and it matches the composite ORDER BY exactly.
            query = query.where(
                tuple_(PackageRow.created_at, PackageRow.id)
                < tuple_(literal(created_at), literal(identifier))
            )
        rows = list(self._session.execute(query.limit(limit + 1)).scalars())

        has_more = len(rows) > limit
        page = rows[:limit]
        next_cursor = (
            _encode_cursor(page[-1].created_at, page[-1].id) if has_more else None
        )
        return PackagePage(
            items=tuple(mappers.to_package(row) for row in page),
            next_cursor=next_cursor,
        )

    def findings_for(self, package_id: UUID) -> Sequence[PackageValidation]:
        rows = self._session.execute(
            select(PackageValidationRow)
            .where(PackageValidationRow.package_id == package_id)
            .order_by(PackageValidationRow.completed_at.desc())
        ).scalars()
        return [mappers.to_validation(row) for row in rows]

    def _by_checksum(self, sha256: str) -> PackageRow | None:
        return self._session.execute(
            select(PackageRow).where(PackageRow.sha256 == sha256)
        ).scalar_one_or_none()


class SqlAlchemyOperationStore:
    """Durable operations, claimed with row locking (ADR-010, ADR-016)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def begin(
        self,
        idempotency_key: str,
        type: OperationType,
        target_id: str,
        request_fingerprint: str,
        correlation_id: UUID,
    ) -> Operation:
        existing = self._by_key(idempotency_key, type, target_id)
        if existing is not None:
            return self._reuse(existing, request_fingerprint)

        row = OperationRow(
            id=uuid4(),
            idempotency_key=idempotency_key,
            type=type.value,
            target_id=target_id,
            request_fingerprint=request_fingerprint,
            state=OperationState.PENDING.value,
            correlation_id=correlation_id,
            attempts=0,
        )
        try:
            with self._session.begin_nested():
                self._session.add(row)
        except IntegrityError:
            # Two concurrent retries of the same request. The unique index
            # arbitrated; the loser must return the winner's operation, not a
            # second one, or the caller would perform the work twice.
            winner = self._by_key(idempotency_key, type, target_id)
            if winner is None:  # pragma: no cover - unreachable under the index
                raise
            return self._reuse(winner, request_fingerprint)
        return mappers.to_operation(row)

    def get(self, operation_id: UUID) -> Operation | None:
        row = self._session.get(OperationRow, operation_id)
        return mappers.to_operation(row) if row else None

    def claim_next(
        self, types: tuple[OperationType, ...] | None = None
    ) -> Operation | None:
        query = (
            select(OperationRow)
            .where(OperationRow.state == OperationState.PENDING.value)
            .order_by(OperationRow.created_at)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        if types is not None:
            # `is not None`, not truthiness: an empty lane selection must select
            # nothing. Treating () as "no filter" would make a worker that asked
            # for no lanes claim every lane.
            query = query.where(OperationRow.type.in_([item.value for item in types]))

        row = self._session.execute(query).scalar_one_or_none()
        if row is None:
            return None

        row.state = OperationState.RUNNING.value
        row.claimed_at = datetime.now(tz=UTC)
        row.attempts += 1
        self._session.flush()
        return mappers.to_operation(row)

    def claim(self, operation_id: UUID) -> Operation | None:
        row = self._session.execute(
            select(OperationRow)
            .where(
                OperationRow.id == operation_id,
                OperationRow.state == OperationState.PENDING.value,
            )
            .with_for_update(skip_locked=True)
        ).scalar_one_or_none()
        if row is None:
            return None

        row.state = OperationState.RUNNING.value
        row.claimed_at = datetime.now(tz=UTC)
        row.attempts += 1
        self._session.flush()
        return mappers.to_operation(row)

    def complete(self, operation_id: UUID, result: dict[str, Any]) -> Operation:
        row = self._running(operation_id)
        row.state = OperationState.SUCCEEDED.value
        row.result = result
        row.completed_at = datetime.now(tz=UTC)
        self._session.flush()
        return mappers.to_operation(row)

    def fail(self, operation_id: UUID, failure: OperationFailure) -> Operation:
        row = self._running(operation_id)
        row.state = OperationState.FAILED.value
        row.failure = {"code": failure.code, "message": failure.message}
        row.completed_at = datetime.now(tz=UTC)
        self._session.flush()
        return mappers.to_operation(row)

    def recover_orphaned(self) -> int:
        """Reclaim work abandoned by a dead worker (ADR-016).

        ADR-010 supervises exactly one worker, so every RUNNING row at startup
        belongs to the process that died. Without this, such a row stays RUNNING
        forever, `claim_next` never sees it again, and the client polls an
        operation that can never reach a terminal state.
        """

        rows = list(
            self._session.execute(
                select(OperationRow).where(
                    OperationRow.state == OperationState.RUNNING.value
                )
            ).scalars()
        )
        now = datetime.now(tz=UTC)
        for row in rows:
            if row.attempts >= MAX_ATTEMPTS:
                row.state = OperationState.FAILED.value
                row.failure = {
                    "code": ABANDONED,
                    "message": "the operation was abandoned after repeated failures",
                }
                row.completed_at = now
            else:
                row.state = OperationState.PENDING.value
                row.claimed_at = None
        self._session.flush()
        return len(rows)

    def _running(self, operation_id: UUID) -> OperationRow:
        row = self._session.get(OperationRow, operation_id)
        if row is None:
            raise _not_found("operation")
        state = OperationState(row.state)
        if state is not OperationState.RUNNING:
            # Terminal operations are immutable (docs 04); a completed operation
            # cannot be completed again with a different answer.
            raise _conflict(
                "invalid_state_transition",
                f"an operation in state {state.value} cannot be completed",
            )
        return row

    def _reuse(self, row: OperationRow, request_fingerprint: str) -> Operation:
        if row.request_fingerprint != request_fingerprint:
            raise _conflict(
                "idempotency_conflict",
                "this idempotency key was already used for a different request",
            )
        return mappers.to_operation(row)

    def _by_key(
        self, idempotency_key: str, type: OperationType, target_id: str
    ) -> OperationRow | None:
        return self._session.execute(
            select(OperationRow).where(
                OperationRow.idempotency_key == idempotency_key,
                OperationRow.type == type.value,
                OperationRow.target_id == target_id,
            )
        ).scalar_one_or_none()


class SqlAlchemyAuditLog:
    """Append-only audit trail enlisted in the caller's transaction."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def record(self, event: AuditEvent) -> None:
        self._session.add(
            AuditEventRow(
                id=uuid4(),
                actor_type=event.actor_type.value,
                actor_id=event.actor_id,
                action=event.action,
                target_type=event.target_type,
                target_id=event.target_id,
                correlation_id=event.correlation_id,
                event_metadata=dict(event.metadata),
            )
        )

    def for_target(self, target_id: str, limit: int) -> Sequence[AuditEvent]:
        rows = self._session.execute(
            select(AuditEventRow)
            .where(AuditEventRow.target_id == target_id)
            .order_by(AuditEventRow.occurred_at.desc())
            .limit(limit)
        ).scalars()
        return [mappers.to_audit_event(row) for row in rows]

    def for_correlation(self, correlation_id: UUID) -> Sequence[AuditEvent]:
        rows = self._session.execute(
            select(AuditEventRow)
            .where(AuditEventRow.correlation_id == correlation_id)
            .order_by(AuditEventRow.occurred_at)
        ).scalars()
        return [mappers.to_audit_event(row) for row in rows]


class SqlAlchemyDeploymentRepository:
    """Deployment and version records backed by PostgreSQL."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create_deployment(self, name: str, desired_state: DesiredState) -> Deployment:
        row = DeploymentRow(id=uuid4(), name=name, desired_state=desired_state.value)
        try:
            with self._session.begin_nested():
                self._session.add(row)
        except IntegrityError as error:
            # The unique name index arbitrated: the name is already taken.
            raise _conflict(
                "deployment_name_taken",
                "a deployment with this name already exists",
            ) from error
        return mappers.to_deployment(row)

    def find_deployment(self, deployment_id: UUID) -> Deployment | None:
        row = self._session.get(DeploymentRow, deployment_id)
        return mappers.to_deployment(row) if row else None

    def find_deployment_by_name(self, name: str) -> Deployment | None:
        row = self._session.execute(
            select(DeploymentRow).where(DeploymentRow.name == name)
        ).scalar_one_or_none()
        return mappers.to_deployment(row) if row else None

    def list_deployments(self, limit: int, cursor: str | None = None) -> DeploymentPage:
        query = select(DeploymentRow).order_by(
            DeploymentRow.created_at.desc(), DeploymentRow.id.desc()
        )
        if cursor is not None:
            created_at, identifier = _decode_cursor(cursor)
            query = query.where(
                tuple_(DeploymentRow.created_at, DeploymentRow.id)
                < tuple_(literal(created_at), literal(identifier))
            )
        rows = list(self._session.execute(query.limit(limit + 1)).scalars())
        has_more = len(rows) > limit
        page = rows[:limit]
        next_cursor = (
            _encode_cursor(page[-1].created_at, page[-1].id) if has_more else None
        )
        return DeploymentPage(
            items=tuple(mappers.to_deployment(row) for row in page),
            next_cursor=next_cursor,
        )

    def lock_deployment(self, deployment_id: UUID) -> Deployment | None:
        row = self._session.execute(
            select(DeploymentRow)
            .where(DeploymentRow.id == deployment_id)
            .with_for_update()
        ).scalar_one_or_none()
        return mappers.to_deployment(row) if row else None

    def save_deployment(self, deployment: Deployment) -> None:
        row = self._session.get(DeploymentRow, deployment.id)
        if row is None:
            raise _not_found("deployment")
        row.desired_state = deployment.desired_state.value
        row.active_version_id = deployment.active_version_id
        self._session.flush()

    def add_version(self, version: DeploymentVersion) -> None:
        self._session.add(
            DeploymentVersionRow(
                id=version.id,
                deployment_id=version.deployment_id,
                package_id=version.package_id,
                attempt=version.attempt,
                state=version.state.value,
                resource_policy=mappers.resource_policy_to_json(
                    version.resource_policy
                ),
                image_ref=version.image_ref,
                container_id=version.container_id,
                endpoint=version.endpoint,
                failure=mappers.failure_to_json(version.failure),
            )
        )
        self._session.flush()

    def find_version(self, version_id: UUID) -> DeploymentVersion | None:
        row = self._session.get(DeploymentVersionRow, version_id)
        return mappers.to_version(row) if row else None

    def list_versions(self, deployment_id: UUID) -> tuple[DeploymentVersion, ...]:
        rows = self._session.execute(
            select(DeploymentVersionRow)
            .where(DeploymentVersionRow.deployment_id == deployment_id)
            .order_by(DeploymentVersionRow.attempt.desc())
        ).scalars()
        return tuple(mappers.to_version(row) for row in rows)

    def save_version(self, version: DeploymentVersion) -> None:
        row = self._session.get(DeploymentVersionRow, version.id)
        if row is None:
            raise _not_found("deployment_version")
        row.state = version.state.value
        row.image_ref = version.image_ref
        row.container_id = version.container_id
        row.endpoint = version.endpoint
        row.failure = mappers.failure_to_json(version.failure)
        self._session.flush()

    def next_attempt(self, deployment_id: UUID, package_id: UUID) -> int:
        highest = self._session.execute(
            select(func.max(DeploymentVersionRow.attempt)).where(
                DeploymentVersionRow.deployment_id == deployment_id,
                DeploymentVersionRow.package_id == package_id,
            )
        ).scalar_one()
        return (highest or 0) + 1


class SqlAlchemyApiKeyStore:
    """API key records backed by PostgreSQL (ADR-024).

    No method returns or accepts a plaintext secret. `create` receives a record
    whose digest was computed in the domain, so the secret never reaches this
    layer in any code path -- which is what makes "the database cannot leak a
    working credential" a structural property rather than a convention.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_key_id(self, key_id: str) -> ApiKey | None:
        row = self._session.execute(
            select(ApiKeyRow).where(ApiKeyRow.key_id == key_id)
        ).scalar_one_or_none()
        return mappers.to_api_key(row) if row else None

    def create(self, key: ApiKey) -> None:
        self._session.add(
            ApiKeyRow(
                id=key.id,
                key_id=key.key_id,
                name=key.name,
                secret_sha256=key.secret_sha256,
                created_at=key.created_at,
                expires_at=key.expires_at,
            )
        )
        try:
            self._session.flush()
        except IntegrityError as exc:
            self._session.rollback()
            raise _conflict(
                "api_key_conflict", "an api key with this identifier already exists"
            ) from exc

    def list(self) -> Sequence[ApiKey]:
        rows = self._session.execute(
            select(ApiKeyRow).order_by(ApiKeyRow.created_at.desc())
        ).scalars()
        return [mappers.to_api_key(row) for row in rows]

    def revoke(self, key_id: str, revoked_at: datetime) -> bool:
        row = self._session.execute(
            select(ApiKeyRow).where(ApiKeyRow.key_id == key_id)
        ).scalar_one_or_none()
        if row is None:
            return False
        # An already-revoked key keeps its first timestamp: that is the moment
        # that mattered to the incident, and overwriting it would corrupt the
        # timeline the column exists to record.
        if row.revoked_at is None:
            row.revoked_at = revoked_at
        return True

    def touch_last_used(self, key_id: UUID, used_at: datetime) -> None:
        row = self._session.get(ApiKeyRow, key_id)
        if row is not None:
            row.last_used_at = used_at
