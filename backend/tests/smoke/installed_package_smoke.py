"""Installed-wheel smoke verification."""

from ipaddress import IPv4Address

from forgeml.core.composition import create_application
from forgeml.core.config import AppSettings, Environment, LogLevel

settings = AppSettings(
    environment=Environment.TEST,
    log_level=LogLevel.INFO,
    bind_host=IPv4Address("127.0.0.1"),
    bind_port=8000,
    graceful_shutdown_seconds=30,
    service_version="0.1.0",
)
application = create_application(settings)

assert application.title == "ForgeML Control Plane"
assert {"/healthz", "/readyz", "/v1/packages", "/v1/operations/{operation_id}"} <= set(
    application.openapi()["paths"]
)
