"""Bootstrap and composition integration tests."""

import json
import logging
import runpy
from typing import cast

import pytest
import uvicorn

from forgeml import bootstrap
from forgeml.core.composition import create_application
from forgeml.core.config import AppSettings, ConfigurationFailure
from forgeml.core.logging import LoggingConfigurationConflict


class FakeServer:
    def __init__(
        self, _: object, *, started: bool = True, failure: BaseException | None = None
    ) -> None:
        self.started = started
        self._failure = failure

    def run(self) -> None:
        if self._failure is not None:
            raise self._failure


def test_sigterm_adapter_raises_internal_shutdown_signal() -> None:
    with pytest.raises(bootstrap._ShutdownRequested):
        bootstrap._raise_shutdown_requested(15, None)


def test_module_entrypoint_returns_bootstrap_exit_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(bootstrap, "main", lambda: 7)

    with pytest.raises(SystemExit) as captured:
        runpy.run_module("forgeml", run_name="__main__")

    assert captured.value.code == 7


def test_multiple_applications_are_isolated(settings: AppSettings) -> None:
    first = create_application(settings)
    second = create_application(settings)

    assert first is not second
    assert first.user_middleware is not second.user_middleware


def test_configuration_failure_is_safe_and_exits_two(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        bootstrap,
        "load_settings",
        lambda: (_ for _ in ()).throw(ConfigurationFailure("configuration_invalid")),
    )

    assert bootstrap.main() == 2
    payload = json.loads(capsys.readouterr().err)
    assert payload["event"] == "configuration_invalid"
    assert payload["code"] == "configuration_invalid"
    assert "Traceback" not in str(payload)


def test_logging_conflict_exits_one(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    settings: AppSettings,
) -> None:
    monkeypatch.setattr(bootstrap, "load_settings", lambda: settings)
    monkeypatch.setattr(
        bootstrap,
        "configure_logging",
        lambda _: (_ for _ in ()).throw(LoggingConfigurationConflict()),
    )

    assert bootstrap.main() == 1
    assert "logging_configuration_conflict" in capsys.readouterr().err


def test_unexpected_logging_failure_is_safe(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    settings: AppSettings,
) -> None:
    monkeypatch.setattr(bootstrap, "load_settings", lambda: settings)
    monkeypatch.setattr(
        bootstrap,
        "configure_logging",
        lambda _: (_ for _ in ()).throw(RuntimeError("secret")),
    )

    assert bootstrap.main() == 1
    output = capsys.readouterr().err
    assert "logging_configuration_failed" in output
    assert "secret" not in output


@pytest.mark.parametrize(
    ("started", "failure", "expected"),
    [
        (True, None, 0),
        (False, None, 1),
        (False, KeyboardInterrupt(), 0),
        (False, OSError("secret"), 1),
        (False, ValueError("secret"), 1),
        (False, SystemExit(1), 1),
    ],
)
def test_server_exit_behavior(
    monkeypatch: pytest.MonkeyPatch,
    settings: AppSettings,
    started: bool,
    failure: BaseException | None,
    expected: int,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setattr(bootstrap, "load_settings", lambda: settings)
    monkeypatch.setattr(bootstrap, "configure_logging", lambda _: None)
    monkeypatch.setattr(
        uvicorn,
        "Server",
        lambda _: FakeServer(None, started=started, failure=failure),
    )

    with caplog.at_level(logging.ERROR):
        result = bootstrap.main()

    assert result == expected
    assert "secret" not in caplog.text
    if started is False and failure is None:
        assert any(
            getattr(record, "event", None) == "server_startup_failed"
            for record in caplog.records
        )


@pytest.mark.parametrize("boundary", ["composition", "config", "server"])
def test_post_logging_startup_boundaries_fail_safely(
    monkeypatch: pytest.MonkeyPatch,
    settings: AppSettings,
    boundary: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setattr(bootstrap, "load_settings", lambda: settings)
    monkeypatch.setattr(bootstrap, "configure_logging", lambda _: None)

    def fail(*_: object, **__: object) -> None:
        raise RuntimeError("secret /host/path")

    if boundary == "composition":
        monkeypatch.setattr(bootstrap, "create_application", fail)
    elif boundary == "config":
        monkeypatch.setattr(uvicorn, "Config", fail)
    else:
        monkeypatch.setattr(uvicorn, "Server", fail)

    with caplog.at_level(logging.ERROR):
        result = bootstrap.main()

    assert result == 1
    assert any(
        getattr(record, "event", None) == "server_startup_failed"
        for record in caplog.records
    )
    assert "secret" not in caplog.text


def test_uvicorn_configuration_is_single_worker_and_hardened(
    monkeypatch: pytest.MonkeyPatch,
    settings: AppSettings,
) -> None:
    captured: dict[str, object] = {}

    class CapturingServer:
        started = True

        def __init__(self, config: object) -> None:
            captured["config"] = config

        def run(self) -> None:
            return None

    monkeypatch.setattr(bootstrap, "load_settings", lambda: settings)
    monkeypatch.setattr(bootstrap, "configure_logging", lambda _: None)
    monkeypatch.setattr(uvicorn, "Server", CapturingServer)

    assert bootstrap.main() == 0
    config = cast(uvicorn.Config, captured["config"])
    assert config.workers == 1
    assert config.reload is False
    assert config.proxy_headers is False
    assert config.access_log is False
