"""Version 1 wire schemas (docs 12).

Every model forbids unknown fields and is frozen. Additive response fields are
compatible; removing or renaming one requires a new API major version.
"""

from __future__ import annotations

import base64
import binascii
from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from forgeml.api.schemas import ErrorDetailResponse
from forgeml.application.package.services import PackageDetail
from forgeml.core.errors import AppError, ErrorCategory
from forgeml.domain.deployment.models import (
    Deployment,
    DeploymentVersion,
    ResourcePolicy,
)
from forgeml.domain.operations.models import Operation
from forgeml.domain.package.models import Package

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100

Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
IdempotencyKey = Annotated[str, Field(min_length=1, max_length=255)]
Cursor = Annotated[str, Field(min_length=1, max_length=256)]
PageLimit = Annotated[int, Field(ge=1, le=MAX_PAGE_SIZE)]


def encode_cursor(raw: str | None) -> str | None:
    """Make a keyset cursor opaque and URL-safe (docs 12).

    The repository's cursor is a timestamp and an id. Its raw form contains a
    `+` from the UTC offset, which a query string decodes as a space -- so
    pagination is simply broken unless it is encoded. Making it opaque is also
    what stops a client building one by hand and depending on our ordering keys.
    """

    if raw is None:
        return None
    return base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")


def decode_cursor(value: str | None) -> str | None:
    """Recover a keyset cursor, refusing anything we did not issue."""

    if value is None:
        return None
    padded = value + "=" * (-len(value) % 4)
    try:
        return base64.urlsafe_b64decode(padded).decode("utf-8")
    except (binascii.Error, ValueError) as error:
        raise AppError(
            category=ErrorCategory.BAD_REQUEST,
            code="cursor_invalid",
            message="The supplied pagination cursor is not valid.",
        ) from error


class _Wire(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class PackageResource(_Wire):
    """A package as clients see it (docs 12)."""

    id: UUID
    sha256: Sha256
    filename: str
    size_bytes: int
    manifest_version: int | None
    validation_state: Literal["draft", "validating", "validated", "rejected"]
    validation_findings: tuple[ErrorDetailResponse, ...] | None = None
    manifest: dict[str, Any] | None = None
    created_at: datetime

    @classmethod
    def of(cls, detail: PackageDetail) -> PackageResource:
        package = detail.package
        findings = (
            tuple(
                ErrorDetailResponse(
                    code=item.code, message=item.message, path=item.path
                )
                for item in detail.validation.findings
            )
            if detail.validation is not None and detail.validation.findings
            else None
        )
        return cls(
            id=package.id,
            sha256=package.sha256,
            filename=package.filename,
            size_bytes=package.size_bytes,
            manifest_version=package.manifest_version,
            validation_state=package.state.value,
            validation_findings=findings,
            manifest=(
                package.manifest.model_dump(mode="json", by_alias=True)
                if package.manifest is not None
                else None
            ),
            created_at=package.created_at,
        )


class PackageSummary(_Wire):
    """A package in a list. The manifest and findings are read individually."""

    id: UUID
    sha256: Sha256
    filename: str
    size_bytes: int
    validation_state: Literal["draft", "validating", "validated", "rejected"]
    created_at: datetime

    @classmethod
    def of(cls, package: Package) -> PackageSummary:
        return cls(
            id=package.id,
            sha256=package.sha256,
            filename=package.filename,
            size_bytes=package.size_bytes,
            validation_state=package.state.value,
            created_at=package.created_at,
        )


class PackageListResponse(_Wire):
    """One page of packages, newest first."""

    items: tuple[PackageSummary, ...]
    next_cursor: str | None = None


class OperationFailureResponse(_Wire):
    """A safe classified failure. Never a trace or a host path."""

    code: str
    message: str


class OperationResource(_Wire):
    """A durable operation as clients poll it (ADR-006)."""

    id: UUID
    type: Literal[
        "package_validate",
        "deployment_version_deploy",
        "deployment_version_stop",
        "deployment_version_activate",
        "deployment_reconcile",
    ]
    target: str
    state: Literal["pending", "running", "succeeded", "failed"]
    correlation_id: UUID
    result: dict[str, Any] | None = None
    failure: OperationFailureResponse | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None

    @classmethod
    def of(cls, operation: Operation) -> OperationResource:
        return cls(
            id=operation.id,
            type=operation.type.value,
            target=operation.target_id,
            state=operation.state.value,
            correlation_id=operation.correlation_id,
            result=operation.result,
            failure=(
                OperationFailureResponse(
                    code=operation.failure.code,
                    message=operation.failure.message,
                )
                if operation.failure is not None
                else None
            ),
            created_at=operation.created_at,
            updated_at=operation.updated_at,
            completed_at=operation.completed_at,
        )


DeploymentName = Annotated[str, Field(pattern=r"^[a-z][a-z0-9-]{0,62}$")]


class ResourcePolicyModel(_Wire):
    """Requested runtime resources, bounded by server policy at deploy time."""

    cpu_millicores: Annotated[int, Field(ge=1, le=64_000)] | None = None
    memory_mib: Annotated[int, Field(ge=1, le=1_048_576)] | None = None
    pids_limit: Annotated[int, Field(ge=1, le=32_768)] | None = None

    def to_domain(self) -> ResourcePolicy:
        return ResourcePolicy(
            cpu_millicores=self.cpu_millicores,
            memory_mib=self.memory_mib,
            pids_limit=self.pids_limit,
        )

    @classmethod
    def of(cls, policy: ResourcePolicy) -> ResourcePolicyModel:
        return cls(
            cpu_millicores=policy.cpu_millicores,
            memory_mib=policy.memory_mib,
            pids_limit=policy.pids_limit,
        )


class CreateDeploymentRequest(_Wire):
    """Create a named deployment (docs 12). The name is immutable."""

    name: DeploymentName


class CreateVersionRequest(_Wire):
    """Create a build/deploy attempt for an accepted package (docs 12)."""

    package_id: UUID
    resource_policy: ResourcePolicyModel | None = None


class DeploymentResource(_Wire):
    """A deployment as clients see it (docs 12)."""

    id: UUID
    name: str
    active_version_id: UUID | None
    desired_state: Literal["running", "stopped"]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def of(cls, deployment: Deployment) -> DeploymentResource:
        return cls(
            id=deployment.id,
            name=deployment.name,
            active_version_id=deployment.active_version_id,
            desired_state=deployment.desired_state.value,
            created_at=deployment.created_at,
            updated_at=deployment.updated_at,
        )


class DeploymentListResponse(_Wire):
    """One page of deployments, newest first."""

    items: tuple[DeploymentResource, ...]
    next_cursor: str | None = None


class VersionResource(_Wire):
    """A deployment version as clients see it (docs 12)."""

    id: UUID
    deployment_id: UUID
    package_id: UUID
    attempt: int
    state: Literal["building", "starting", "ready", "active", "failed", "stopped"]
    endpoint: str | None
    resource_policy: ResourcePolicyModel
    failure: OperationFailureResponse | None = None

    @classmethod
    def of(cls, version: DeploymentVersion) -> VersionResource:
        return cls(
            id=version.id,
            deployment_id=version.deployment_id,
            package_id=version.package_id,
            attempt=version.attempt,
            state=version.state.value,
            endpoint=version.endpoint,
            resource_policy=ResourcePolicyModel.of(version.resource_policy),
            failure=(
                OperationFailureResponse(
                    code=version.failure.code, message=version.failure.message
                )
                if version.failure is not None
                else None
            ),
        )
