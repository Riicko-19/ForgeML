"""Shared Module 0 test fixtures."""

from ipaddress import IPv4Address

import pytest

from forgeml.core.config import AppSettings, Environment, LogLevel


@pytest.fixture
def settings() -> AppSettings:
    return AppSettings(
        environment=Environment.TEST,
        log_level=LogLevel.INFO,
        bind_host=IPv4Address("127.0.0.1"),
        bind_port=8000,
        graceful_shutdown_seconds=30,
        service_version="0.1.0",
    )
