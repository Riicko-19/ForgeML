"""In-process OpenAPI contract tests.

The published schema is the API's source of truth (docs 12). These tests pin the
surface so a route, a status code, or a response field cannot change shape
without someone deciding to change it.
"""

from forgeml.core.composition import create_application
from forgeml.core.config import AppSettings

EXPECTED_PATHS = {
    "/healthz",
    "/readyz",
    "/v1/packages",
    "/v1/packages/{package_id}",
    "/v1/operations/{operation_id}",
    # Module 6 mounts the deployment surface Module 5 defined but left unwired.
    "/v1/deployments",
    "/v1/deployments/{deployment_id}",
    "/v1/deployments/{deployment_id}/versions",
    "/v1/deployments/{deployment_id}/versions/{version_id}",
    "/v1/deployments/{deployment_id}/versions/{version_id}/activate",
    "/v1/deployments/{deployment_id}/versions/{version_id}/stop",
    # Module 7 platform prediction route, addressed by deployment name.
    "/v1/deployments/{name}/predict",
    "/v1/admin/reconcile",
}


def test_openapi_publishes_exactly_the_v1_surface(settings: AppSettings) -> None:
    schema = create_application(settings).openapi()

    assert set(schema["paths"]) == EXPECTED_PATHS
    assert schema["info"]["title"] == "ForgeML Control Plane"
    assert schema["info"]["version"] == "0.1.0"


def test_upload_returns_an_operation_not_a_package(settings: AppSettings) -> None:
    # Docs 12: a long-running command returns 202 and an operation resource.
    # Returning the package directly would promise a verdict the platform has
    # not reached yet, and would break the day validation moves to the worker.
    upload = create_application(settings).openapi()["paths"]["/v1/packages"]["post"]

    assert set(upload["responses"]) >= {"202", "400", "409", "422", "503"}
    schema = upload["responses"]["202"]["content"]["application/json"]["schema"]
    assert schema["$ref"].endswith("/OperationResource")


def test_response_schemas_forbid_extra_fields(settings: AppSettings) -> None:
    components = create_application(settings).openapi()["components"]["schemas"]

    for model in (
        "HealthResponse",
        "ErrorEnvelope",
        "ErrorDetailResponse",
        "PackageResource",
        "PackageSummary",
        "PackageListResponse",
        "OperationResource",
    ):
        assert components[model]["additionalProperties"] is False


def test_every_error_response_uses_the_frozen_envelope(settings: AppSettings) -> None:
    paths = create_application(settings).openapi()["paths"]

    for path, operations in paths.items():
        for method, operation in operations.items():
            for status, response in operation["responses"].items():
                if not status.startswith(("4", "5")):
                    continue
                content = response.get("content")
                if content is None:  # 422 defaults declared without a body
                    continue
                schema = content["application/json"]["schema"]
                assert schema["$ref"].endswith(
                    "/ErrorEnvelope"
                ), f"{method.upper()} {path} -> {status} does not use ErrorEnvelope"
