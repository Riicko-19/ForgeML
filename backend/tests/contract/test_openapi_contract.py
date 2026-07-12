"""In-process OpenAPI contract tests."""

from forgeml.core.composition import create_application
from forgeml.core.config import AppSettings


def test_openapi_contains_only_health_paths(settings: AppSettings) -> None:
    schema = create_application(settings).openapi()

    assert set(schema["paths"]) == {"/healthz", "/readyz"}
    assert schema["info"]["title"] == "ForgeML Control Plane"
    assert schema["info"]["version"] == "0.1.0"


def test_response_schemas_forbid_extra_fields(settings: AppSettings) -> None:
    components = create_application(settings).openapi()["components"]["schemas"]

    assert components["HealthResponse"]["additionalProperties"] is False
    assert components["ErrorEnvelope"]["additionalProperties"] is False
    assert components["ErrorDetailResponse"]["additionalProperties"] is False
