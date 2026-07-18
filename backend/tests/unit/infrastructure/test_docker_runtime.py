"""Unit tests for the Docker runtime adapter, without Docker.

Every Docker call goes through the injectable `DockerCli` seam, so these tests
drive build/start/stop/inspect/reconcile with a scripted fake CLI and assert the
argument building, output parsing, and failure classification directly. The real
daemon is exercised separately by the disposable-Docker integration tests.
"""

from __future__ import annotations

import io
import json
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import BinaryIO
from uuid import UUID, uuid4

import pytest

from forgeml.core.config import PackageLimits
from forgeml.domain.deployment.models import ResourcePolicy
from forgeml.domain.deployment.ports import (
    BuiltImage,
    RuntimeExecutionError,
    RuntimeStatus,
    RuntimeUnavailable,
)
from forgeml.domain.package.generator import generate
from forgeml.domain.package.models import InferenceContract
from forgeml.infrastructure.package.zip_archive import ZipArchiveReader
from forgeml.infrastructure.runtime.docker import (
    LABEL_MANAGED,
    LABEL_VERSION,
    CliResult,
    DockerRuntimeManager,
    RuntimeSettings,
    container_name,
    image_ref,
    looks_unavailable,
    run_args,
    status_from_inspect,
)
from tests.packages import build_forge

Handler = Callable[[list[str]], CliResult]


def ok(stdout: bytes = b"", stderr: bytes = b"") -> CliResult:
    return CliResult(returncode=0, stdout=stdout, stderr=stderr)


def err(stderr: bytes, returncode: int = 1) -> CliResult:
    return CliResult(returncode=returncode, stdout=b"", stderr=stderr)


class FakeCli:
    def __init__(self, handler: Handler) -> None:
        self._handler = handler
        self.calls: list[list[str]] = []

    def run(self, args: Sequence[str], *, timeout: float) -> CliResult:
        call = list(args)
        self.calls.append(call)
        return self._handler(call)

    def commands(self) -> list[str]:
        return [call[0] for call in self.calls]


class FakeStore:
    def __init__(self, data: bytes) -> None:
        self._data = data

    def open(self, sha256: str) -> BinaryIO:
        return io.BytesIO(self._data)


def inspect_json(
    *, running: bool = True, health: str | None = "healthy", restart_count: int = 0
) -> bytes:
    state: dict[str, object] = {"Running": running}
    if health is not None:
        state["Health"] = {"Status": health}
    obj = {"Id": "full-container-id", "State": state, "RestartCount": restart_count}
    return json.dumps([obj]).encode("utf-8")


def make_manager(
    handler: Handler, *, data: bytes | None = None
) -> tuple[DockerRuntimeManager, FakeCli]:
    cli = FakeCli(handler)
    manager = DockerRuntimeManager(
        store=FakeStore(data or build_forge()),
        reader=ZipArchiveReader(),
        limits=PackageLimits(),
        settings=RuntimeSettings(poll_interval_seconds=1.0, start_timeout_seconds=3.0),
        cli=cli,
        sleep=lambda _seconds: None,
    )
    return manager, cli


def a_context() -> object:
    contract = InferenceContract(
        analyzer_version="1",
        framework="python-callable",
        python="3.11",
        entrypoint_module="model",
        entrypoint_callable="predict",
        dependencies=(),
        input_schema={"type": "object"},
        output_schema={"type": "object"},
        model_name="m",
        model_version="1.0.0",
    )
    return generate(contract, checksum="a" * 64)


# -- pure helpers ---------------------------------------------------------------


def test_container_name_and_image_ref_are_deterministic() -> None:
    version = UUID("11111111-1111-1111-1111-111111111111")
    assert container_name(version) == "forgeml-11111111-1111-1111-1111-111111111111"
    assert image_ref("abcdef0123456789") == "forgeml/abcdef012345"


def test_looks_unavailable_detects_daemon_down() -> None:
    assert looks_unavailable(b"Cannot connect to the Docker daemon at unix://...")
    assert not looks_unavailable(b"pip install failed: no matching distribution")


def test_run_args_are_hardened_and_use_the_policy() -> None:
    version = uuid4()
    args = run_args(
        version,
        BuiltImage(image_ref="forgeml/img"),
        ResourcePolicy(cpu_millicores=500, memory_mib=256, pids_limit=64),
        RuntimeSettings(),
    )
    assert args[0] == "run" and "-d" in args
    for flag in ("--read-only", "--cap-drop", "--security-opt"):
        assert flag in args
    assert "no-new-privileges" in args
    assert args[args.index("--cpus") + 1] == "0.500"
    assert args[args.index("--memory") + 1] == "256m"
    assert args[args.index("--pids-limit") + 1] == "64"
    assert args[args.index("--network") + 1] == "forgeml-runtime"
    assert f"{LABEL_VERSION}={version}" in args
    assert args[-1] == "forgeml/img"


def test_run_args_fall_back_to_server_defaults() -> None:
    args = run_args(
        uuid4(), BuiltImage(image_ref="i"), ResourcePolicy(), RuntimeSettings()
    )
    assert args[args.index("--cpus") + 1] == "1.000"
    assert args[args.index("--memory") + 1] == "512m"
    assert args[args.index("--pids-limit") + 1] == "256"


def test_status_from_inspect_reads_running_and_health() -> None:
    obj = json.loads(inspect_json(running=True, health="healthy", restart_count=2))[0]
    status = status_from_inspect(obj)
    assert status == RuntimeStatus(
        present=True, running=True, healthy=True, restart_count=2
    )


def test_status_without_healthcheck_falls_back_to_running() -> None:
    obj = json.loads(inspect_json(running=True, health=None))[0]
    assert status_from_inspect(obj).healthy is True


def test_status_from_malformed_object_is_not_running() -> None:
    status = status_from_inspect("not-a-dict")
    assert status == RuntimeStatus(
        present=True, running=False, healthy=False, restart_count=0
    )


# -- build ----------------------------------------------------------------------


def test_build_assembles_context_and_tags_the_image() -> None:
    context = a_context()
    seen: dict[str, str] = {}

    def handler(call: list[str]) -> CliResult:
        assert call[0] == "build"
        build_dir = Path(call[-1])
        seen["dockerfile"] = (build_dir / "Dockerfile").read_text()
        seen["has_server"] = str((build_dir / "forge_server.py").exists())
        seen["has_src"] = str((build_dir / "src" / "model.py").exists())
        return ok()

    manager, _ = make_manager(handler)
    built = manager.build(uuid4(), context, "b" * 64, ResourcePolicy())  # type: ignore[arg-type]

    assert built.image_ref == image_ref(context.identity)  # type: ignore[attr-defined]
    assert seen["has_server"] == "True"
    assert seen["has_src"] == "True"
    # The frozen generated Dockerfile has no CMD; Module 6 appends the serving layer.
    assert "CMD" in seen["dockerfile"]
    assert "forge_server.py" in seen["dockerfile"]
    assert "HEALTHCHECK" in seen["dockerfile"]


def test_build_failure_is_terminal_and_leaks_no_output() -> None:
    manager, _ = make_manager(
        lambda call: err(b"pip: no matching distribution at /root/x")
    )
    with pytest.raises(RuntimeExecutionError) as caught:
        manager.build(uuid4(), a_context(), "b" * 64, ResourcePolicy())  # type: ignore[arg-type]
    assert caught.value.failure.code == "runtime_build_failed"
    assert "/root/x" not in caught.value.failure.message


def test_build_when_daemon_down_is_retriable() -> None:
    manager, _ = make_manager(lambda call: err(b"Cannot connect to the Docker daemon"))
    with pytest.raises(RuntimeUnavailable):
        manager.build(uuid4(), a_context(), "b" * 64, ResourcePolicy())  # type: ignore[arg-type]


def test_build_timeout_is_terminal() -> None:
    def handler(call: list[str]) -> CliResult:
        raise TimeoutError("build timed out")

    manager, _ = make_manager(handler)
    with pytest.raises(RuntimeExecutionError) as caught:
        manager.build(uuid4(), a_context(), "b" * 64, ResourcePolicy())  # type: ignore[arg-type]
    assert caught.value.failure.code == "runtime_build_failed"


# -- start ----------------------------------------------------------------------


def test_start_runs_and_waits_for_health() -> None:
    version = uuid4()

    def handler(call: list[str]) -> CliResult:
        if call[0] == "rm":
            return ok()
        if call[0] == "run":
            return ok(stdout=b"the-container-id\n")
        if call[0] == "inspect":
            return ok(stdout=inspect_json(running=True, health="healthy"))
        raise AssertionError(call)

    manager, _ = make_manager(handler)
    running = manager.start(
        version, BuiltImage(image_ref="forgeml/i"), ResourcePolicy()
    )
    assert running.container_id == "the-container-id"
    assert running.endpoint == f"http://{container_name(version)}:8000"


def test_start_polls_until_healthy() -> None:
    statuses = [
        inspect_json(running=True, health="starting"),
        inspect_json(running=True, health="healthy"),
    ]

    def handler(call: list[str]) -> CliResult:
        if call[0] == "run":
            return ok(stdout=b"cid\n")
        if call[0] == "inspect":
            return ok(stdout=statuses.pop(0))
        return ok()

    manager, _ = make_manager(handler)
    running = manager.start(uuid4(), BuiltImage(image_ref="i"), ResourcePolicy())
    assert running.container_id == "cid"


def test_start_fails_when_the_container_exits() -> None:
    def handler(call: list[str]) -> CliResult:
        if call[0] == "run":
            return ok(stdout=b"cid\n")
        if call[0] == "inspect":
            return ok(stdout=inspect_json(running=False, health=None))
        return ok()

    manager, cli = make_manager(handler)
    with pytest.raises(RuntimeExecutionError) as caught:
        manager.start(uuid4(), BuiltImage(image_ref="i"), ResourcePolicy())
    assert caught.value.failure.code == "runtime_start_failed"
    assert "rm" in cli.commands()  # the exited container is cleaned up


def test_start_times_out_when_never_healthy() -> None:
    def handler(call: list[str]) -> CliResult:
        if call[0] == "run":
            return ok(stdout=b"cid\n")
        if call[0] == "inspect":
            return ok(stdout=inspect_json(running=True, health="starting"))
        return ok()

    manager, _ = make_manager(handler)
    with pytest.raises(RuntimeExecutionError) as caught:
        manager.start(uuid4(), BuiltImage(image_ref="i"), ResourcePolicy())
    assert caught.value.failure.code == "runtime_readiness_timeout"


def test_start_run_timeout_is_a_readiness_timeout() -> None:
    def handler(call: list[str]) -> CliResult:
        if call[0] == "rm":
            return ok()
        raise TimeoutError("run timed out")

    manager, _ = make_manager(handler)
    with pytest.raises(RuntimeExecutionError) as caught:
        manager.start(uuid4(), BuiltImage(image_ref="i"), ResourcePolicy())
    assert caught.value.failure.code == "runtime_readiness_timeout"


def test_start_when_daemon_down_is_retriable() -> None:
    def handler(call: list[str]) -> CliResult:
        if call[0] == "rm":
            return ok()
        return err(b"Cannot connect to the Docker daemon")

    manager, _ = make_manager(handler)
    with pytest.raises(RuntimeUnavailable):
        manager.start(uuid4(), BuiltImage(image_ref="i"), ResourcePolicy())


# -- stop / inspect -------------------------------------------------------------


def test_stop_ignores_an_absent_container() -> None:
    manager, _ = make_manager(lambda call: err(b"Error: No such container: cid"))
    manager.stop("cid")  # no raise


def test_stop_reports_daemon_unavailable() -> None:
    manager, _ = make_manager(lambda call: err(b"Cannot connect to the Docker daemon"))
    with pytest.raises(RuntimeUnavailable):
        manager.stop("cid")


def test_inspect_absent_container() -> None:
    manager, _ = make_manager(lambda call: err(b"No such object: cid"))
    assert manager.inspect("cid").present is False


def test_inspect_reports_daemon_unavailable() -> None:
    manager, _ = make_manager(lambda call: err(b"Cannot connect to the Docker daemon"))
    with pytest.raises(RuntimeUnavailable):
        manager.inspect("cid")


# -- reconcile ------------------------------------------------------------------


def test_reconcile_lists_and_inspects_managed_runtimes() -> None:
    version = uuid4()

    def handler(call: list[str]) -> CliResult:
        if call[0] == "ps":
            assert f"label={LABEL_MANAGED}=true" in call
            return ok(stdout=b"c1\nc2\n")
        obj = {
            "Id": "full-" + call[-1],
            "State": {"Running": True, "Health": {"Status": "healthy"}},
            "RestartCount": 0,
            "Config": {"Labels": {LABEL_VERSION: str(version)}},
        }
        return ok(stdout=json.dumps([obj]).encode())

    manager, _ = make_manager(handler)
    managed = manager.reconcile()
    assert len(managed) == 2
    assert managed[0].version_id == version
    assert managed[0].container_id == "full-c1"
    assert managed[0].status.healthy is True


def test_reconcile_skips_a_vanished_container() -> None:
    def handler(call: list[str]) -> CliResult:
        if call[0] == "ps":
            return ok(stdout=b"c1\n")
        return err(b"No such object: c1")

    manager, _ = make_manager(handler)
    assert manager.reconcile() == ()


def test_reconcile_tolerates_an_unlabelled_version() -> None:
    def handler(call: list[str]) -> CliResult:
        if call[0] == "ps":
            return ok(stdout=b"c1\n")
        obj = {"Id": "c1", "State": {"Running": True}, "Config": {"Labels": {}}}
        return ok(stdout=json.dumps([obj]).encode())

    manager, _ = make_manager(handler)
    managed = manager.reconcile()
    assert managed[0].version_id is None


def test_reconcile_daemon_down_is_retriable() -> None:
    manager, _ = make_manager(lambda call: err(b"Cannot connect to the Docker daemon"))
    with pytest.raises(RuntimeUnavailable):
        manager.reconcile()


def test_reconcile_other_error_is_execution_error() -> None:
    manager, _ = make_manager(lambda call: err(b"something else broke"))
    with pytest.raises(RuntimeExecutionError) as caught:
        manager.reconcile()
    assert caught.value.failure.code == "runtime_reconcile_failed"
