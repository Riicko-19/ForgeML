"""Translation between ORM rows and immutable domain records.

This is the membrane. Every value crossing out of infrastructure is rebuilt as a
frozen domain record here, which is what keeps SQLAlchemy out of the domain
without relying on anybody's discipline.
"""

from __future__ import annotations

import copy
from typing import Any

from forgeml.core.errors import ErrorDetail
from forgeml.domain.audit.models import ActorType, AuditEvent
from forgeml.domain.deployment.models import (
    Deployment,
    DeploymentVersion,
    DesiredState,
    ResourcePolicy,
    VersionState,
)
from forgeml.domain.operations.models import (
    Operation,
    OperationFailure,
    OperationState,
    OperationType,
)
from forgeml.domain.package.models import (
    InferenceContract,
    ManifestV1,
    Package,
    PackageState,
    PackageValidation,
    ValidationState,
)
from forgeml.infrastructure.database.models import (
    AuditEventRow,
    DeploymentRow,
    DeploymentVersionRow,
    OperationRow,
    PackageRow,
    PackageValidationRow,
)


def finding_to_json(detail: ErrorDetail) -> dict[str, Any]:
    return {
        "code": detail.code,
        "message": detail.message,
        "path": list(detail.path) if detail.path is not None else None,
    }


def finding_from_json(document: dict[str, Any]) -> ErrorDetail:
    path = document.get("path")
    return ErrorDetail(
        code=document["code"],
        message=document["message"],
        path=tuple(path) if path is not None else None,
    )


def to_package(row: PackageRow) -> Package:
    return Package(
        id=row.id,
        sha256=row.sha256,
        filename=row.filename,
        size_bytes=row.size_bytes,
        manifest_version=row.manifest_version,
        state=PackageState(row.state),
        artifact_uri=row.artifact_uri,
        created_at=row.created_at,
        updated_at=row.updated_at,
        manifest=ManifestV1.model_validate(row.manifest) if row.manifest else None,
    )


def to_validation(row: PackageValidationRow) -> PackageValidation:
    return PackageValidation(
        state=ValidationState(row.state),
        validator_version=row.validator_version,
        findings=tuple(finding_from_json(item) for item in row.findings),
        manifest=ManifestV1.model_validate(row.manifest) if row.manifest else None,
        contract=contract_from_json(row.contract),
    )


def to_operation(row: OperationRow) -> Operation:
    failure = row.failure
    # deepcopy: row.result is a live mutable dict still attached to the session.
    # Handing it out would let a caller mutate persisted state through a record
    # that is otherwise frozen.
    return Operation(
        id=row.id,
        idempotency_key=row.idempotency_key,
        type=OperationType(row.type),
        target_id=row.target_id,
        request_fingerprint=row.request_fingerprint,
        state=OperationState(row.state),
        correlation_id=row.correlation_id,
        attempts=row.attempts,
        created_at=row.created_at,
        updated_at=row.updated_at,
        claimed_at=row.claimed_at,
        completed_at=row.completed_at,
        result=copy.deepcopy(row.result),
        failure=(
            OperationFailure(code=failure["code"], message=failure["message"])
            if failure
            else None
        ),
    )


def to_audit_event(row: AuditEventRow) -> AuditEvent:
    return AuditEvent(
        actor_type=ActorType(row.actor_type),
        action=row.action,
        target_type=row.target_type,
        target_id=row.target_id,
        correlation_id=row.correlation_id,
        metadata=dict(row.event_metadata),
        id=row.id,
        occurred_at=row.occurred_at,
    )


def manifest_to_json(manifest: ManifestV1 | None) -> dict[str, Any] | None:
    # by_alias keeps `schema` as the wire name; round-tripping through the field
    # name would produce a manifest the frozen model refuses to read back.
    return manifest.model_dump(mode="json", by_alias=True) if manifest else None


def contract_to_json(contract: InferenceContract | None) -> dict[str, Any] | None:
    if contract is None:
        return None
    return {
        "analyzer_version": contract.analyzer_version,
        "framework": contract.framework,
        "python": contract.python,
        "entrypoint_module": contract.entrypoint_module,
        "entrypoint_callable": contract.entrypoint_callable,
        "dependencies": list(contract.dependencies),
        "input_schema": copy.deepcopy(dict(contract.input_schema)),
        "output_schema": copy.deepcopy(dict(contract.output_schema)),
        "model_name": contract.model_name,
        "model_version": contract.model_version,
    }


def to_deployment(row: DeploymentRow) -> Deployment:
    return Deployment(
        id=row.id,
        name=row.name,
        desired_state=DesiredState(row.desired_state),
        active_version_id=row.active_version_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def to_version(row: DeploymentVersionRow) -> DeploymentVersion:
    policy = row.resource_policy or {}
    failure = row.failure
    return DeploymentVersion(
        id=row.id,
        deployment_id=row.deployment_id,
        package_id=row.package_id,
        attempt=row.attempt,
        state=VersionState(row.state),
        resource_policy=ResourcePolicy(
            cpu_millicores=policy.get("cpu_millicores"),
            memory_mib=policy.get("memory_mib"),
            pids_limit=policy.get("pids_limit"),
        ),
        image_ref=row.image_ref,
        container_id=row.container_id,
        endpoint=row.endpoint,
        failure=(
            OperationFailure(code=failure["code"], message=failure["message"])
            if failure
            else None
        ),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def resource_policy_to_json(policy: ResourcePolicy) -> dict[str, Any]:
    return {
        "cpu_millicores": policy.cpu_millicores,
        "memory_mib": policy.memory_mib,
        "pids_limit": policy.pids_limit,
    }


def failure_to_json(failure: OperationFailure | None) -> dict[str, Any] | None:
    if failure is None:
        return None
    return {"code": failure.code, "message": failure.message}


def contract_from_json(document: dict[str, Any] | None) -> InferenceContract | None:
    if document is None:
        return None
    return InferenceContract(
        analyzer_version=document["analyzer_version"],
        framework=document["framework"],
        python=document["python"],
        entrypoint_module=document["entrypoint_module"],
        entrypoint_callable=document["entrypoint_callable"],
        dependencies=tuple(document["dependencies"]),
        input_schema=document["input_schema"],
        output_schema=document["output_schema"],
        model_name=document["model_name"],
        model_version=document["model_version"],
    )
