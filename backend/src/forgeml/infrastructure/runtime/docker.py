"""The real `RuntimeManager`: a Docker adapter driven through the CLI.

Module 5 froze the `RuntimeManager` port and drove it against a fake; Module 6
implements it against Docker so nothing above the port changes. The control
plane speaks to the Docker daemon through its command-line interface rather than
an SDK: it adds no pinned runtime dependency, and the daemon is reached the same
way either approach would reach it. Every call to the CLI goes through the
`DockerCli` seam, which is the *only* code here that touches `subprocess` -- the
rest is pure argument building and output parsing, unit-tested with a scripted
fake CLI, and exercised end to end by the disposable-Docker integration tests.

Isolation follows ADR-001: containers run non-root, read-only, with all
capabilities dropped, no new privileges, no host networking, resource limits,
and no Docker socket. Every managed resource is labelled so reconciliation
(ADR-004) can enumerate exactly what the platform owns and nothing else.
"""

from __future__ import annotations

import contextlib
import json
import shutil
import subprocess
import tempfile
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Protocol
from uuid import UUID

from forgeml.core.config import PackageLimits
from forgeml.domain.deployment.models import ResourcePolicy
from forgeml.domain.deployment.ports import (
    BuiltImage,
    ManagedRuntime,
    RunningContainer,
    RuntimeExecutionError,
    RuntimeStatus,
    RuntimeUnavailable,
)
from forgeml.domain.operations.models import OperationFailure
from forgeml.domain.package.generator import GeneratedBuildContext
from forgeml.infrastructure.runtime.serving import (
    FORGE_SERVER_SOURCE,
    RUNTIME_PORT,
    augment_dockerfile,
)

LABEL_MANAGED = "forgeml.managed"
LABEL_VERSION = "forgeml.version_id"
LABEL_IDENTITY = "forgeml.image_identity"


@dataclass(frozen=True, slots=True)
class RuntimeSettings:
    """Operator policy for the Docker runtime.

    Defaulted so the runtime is usable on a single host without extra
    configuration; making these environment-overridable is a small additive
    follow-up, not a contract change.
    """

    network: str = "forgeml-runtime"
    run_user: str = "65532:65532"
    build_timeout_seconds: float = 600.0
    start_timeout_seconds: float = 120.0
    stop_timeout_seconds: float = 30.0
    poll_interval_seconds: float = 0.5
    default_cpu_millicores: int = 1000
    default_memory_mib: int = 512
    default_pids_limit: int = 256


@dataclass(frozen=True, slots=True)
class CliResult:
    """The outcome of one Docker CLI invocation."""

    returncode: int
    stdout: bytes
    stderr: bytes


class DockerCli(Protocol):
    """The one seam that runs Docker. Everything else here is pure."""

    def run(self, args: Sequence[str], *, timeout: float) -> CliResult:
        """Run `docker <args>`. Raise RuntimeUnavailable if docker is absent,
        TimeoutError if it exceeds `timeout`."""


class SubprocessDockerCli:
    """Runs the real `docker` binary via subprocess."""

    def __init__(self, binary: str = "docker") -> None:
        self._binary = binary

    def run(self, args: Sequence[str], *, timeout: float) -> CliResult:
        try:
            completed = subprocess.run(  # noqa: S603 - fixed argv, no shell
                [self._binary, *args],
                capture_output=True,
                timeout=timeout,
                check=False,
            )
        except FileNotFoundError as error:
            raise RuntimeUnavailable("the docker CLI is not installed") from error
        except subprocess.TimeoutExpired as error:
            raise TimeoutError(f"docker {args[0]} timed out") from error
        return CliResult(completed.returncode, completed.stdout, completed.stderr)


class _ArtifactSource(Protocol):
    def open(self, sha256: str) -> BinaryIO: ...


class _ArchiveExtractor(Protocol):
    def extract(
        self, stream: BinaryIO, destination: str, limits: PackageLimits
    ) -> None: ...


# -- pure helpers ---------------------------------------------------------------


def container_name(version_id: UUID) -> str:
    """The deterministic container name for a version (also its DNS name)."""

    return f"forgeml-{version_id}"


def image_ref(identity: str) -> str:
    """The deterministic image tag for a build-context identity."""

    return f"forgeml/{identity[:12]}"


def looks_unavailable(stderr: bytes) -> bool:
    """Whether a CLI failure means the daemon is unreachable (retriable)."""

    # ponytail: string match on the daemon-connectivity message; Docker has no
    # stable exit code that distinguishes "daemon down" from "command failed".
    text = stderr.decode("utf-8", "replace").lower()
    return (
        "cannot connect to the docker daemon" in text
        or "is the docker daemon running" in text
    )


def run_args(
    version_id: UUID,
    image: BuiltImage,
    policy: ResourcePolicy,
    settings: RuntimeSettings,
) -> list[str]:
    """The `docker run` argv for a hardened, labelled runtime container (ADR-001)."""

    cpu = (policy.cpu_millicores or settings.default_cpu_millicores) / 1000
    memory = policy.memory_mib or settings.default_memory_mib
    pids = policy.pids_limit or settings.default_pids_limit
    return [
        "run",
        "-d",
        "--name",
        container_name(version_id),
        "--label",
        f"{LABEL_MANAGED}=true",
        "--label",
        f"{LABEL_VERSION}={version_id}",
        "--label",
        f"{LABEL_IDENTITY}={image.image_ref}",
        "--restart",
        "no",
        "--network",
        settings.network,
        "--user",
        settings.run_user,
        "--read-only",
        "--tmpfs",
        "/tmp:rw,noexec,nosuid,size=64m",  # noqa: S108 - container-internal tmpfs
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--pids-limit",
        str(pids),
        "--memory",
        f"{memory}m",
        "--cpus",
        f"{cpu:.3f}",
        image.image_ref,
    ]


def status_from_inspect(obj: object) -> RuntimeStatus:
    """Parse one `docker inspect` object into a provider-neutral status."""

    record = obj if isinstance(obj, dict) else {}
    state = record.get("State")
    state_map = state if isinstance(state, dict) else {}
    running = bool(state_map.get("Running"))
    health = state_map.get("Health")
    health_status = health.get("Status") if isinstance(health, dict) else None
    # A container with a health check is healthy only when Docker says so; one
    # without (there should be none here) falls back to "is it running".
    healthy = (health_status == "healthy") if health_status else running
    restart_count = record.get("RestartCount")
    return RuntimeStatus(
        present=True,
        running=running,
        healthy=healthy,
        restart_count=int(restart_count) if isinstance(restart_count, int) else 0,
    )


def _labels_of(obj: object) -> dict[str, str]:
    record = obj if isinstance(obj, dict) else {}
    config = record.get("Config")
    labels = config.get("Labels") if isinstance(config, dict) else None
    if not isinstance(labels, dict):
        return {}
    return {str(k): str(v) for k, v in labels.items()}


def _version_id_of(obj: object) -> UUID | None:
    raw = _labels_of(obj).get(LABEL_VERSION)
    if raw is None:
        return None
    try:
        return UUID(raw)
    except ValueError:
        return None


# -- the adapter ----------------------------------------------------------------


class DockerRuntimeManager:
    """`RuntimeManager` implemented against the Docker CLI."""

    def __init__(
        self,
        store: _ArtifactSource,
        reader: _ArchiveExtractor,
        limits: PackageLimits,
        settings: RuntimeSettings | None = None,
        cli: DockerCli | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._store = store
        self._reader = reader
        self._limits = limits
        self._settings = settings or RuntimeSettings()
        self._cli = cli or SubprocessDockerCli()
        self._sleep = sleep

    def build(
        self,
        version_id: UUID,
        context: GeneratedBuildContext,
        artifact_sha256: str,
        policy: ResourcePolicy,
    ) -> BuiltImage:
        build_dir = Path(tempfile.mkdtemp(prefix="forgeml-build-"))
        try:
            self._assemble_context(build_dir, context, artifact_sha256)
            ref = image_ref(context.identity)
            result = self._cli.run(
                [
                    "build",
                    "-t",
                    ref,
                    "--label",
                    f"{LABEL_MANAGED}=true",
                    "--label",
                    f"{LABEL_IDENTITY}={context.identity}",
                    str(build_dir),
                ],
                timeout=self._settings.build_timeout_seconds,
            )
            if result.returncode != 0:
                raise self._failure(result, "runtime_build_failed", "image build")
            return BuiltImage(image_ref=ref)
        except TimeoutError as error:
            raise RuntimeExecutionError(
                OperationFailure(
                    code="runtime_build_failed",
                    message="the runtime image build did not finish in time",
                )
            ) from error
        finally:
            shutil.rmtree(build_dir, ignore_errors=True)

    def _assemble_context(
        self, build_dir: Path, context: GeneratedBuildContext, artifact_sha256: str
    ) -> None:
        # The package archive supplies src/; the generated files supply the
        # Dockerfile, requirements, and adapter; we supply the serving harness
        # and the CMD/healthcheck the frozen generator left to Module 6.
        with self._store.open(artifact_sha256) as stream:
            self._reader.extract(stream, str(build_dir), self._limits)
        for name, content in context.files.items():
            text = augment_dockerfile(content) if name == "Dockerfile" else content
            (build_dir / name).write_text(text, encoding="utf-8")
        (build_dir / "forge_server.py").write_text(
            FORGE_SERVER_SOURCE, encoding="utf-8"
        )

    def start(
        self, version_id: UUID, image: BuiltImage, policy: ResourcePolicy
    ) -> RunningContainer:
        name = container_name(version_id)
        # A retry reuses the deterministic name; clear any stale container first
        # so `run --name` cannot collide.
        self._safe_remove(name)
        try:
            result = self._cli.run(
                run_args(version_id, image, policy, self._settings),
                timeout=self._settings.start_timeout_seconds,
            )
        except TimeoutError as error:
            self._safe_remove(name)
            raise self._timeout_failure() from error
        if result.returncode != 0:
            raise self._failure(result, "runtime_start_failed", "container start")

        container_id = result.stdout.decode("utf-8").strip()
        self._await_ready(name, container_id)
        return RunningContainer(
            container_id=container_id,
            endpoint=f"http://{name}:{RUNTIME_PORT}",
        )

    def _await_ready(self, name: str, container_id: str) -> None:
        interval = self._settings.poll_interval_seconds
        attempts = max(1, int(self._settings.start_timeout_seconds / interval))
        for _ in range(attempts):
            status = self.inspect(container_id)
            if status.running and status.healthy:
                return
            if status.present and not status.running:
                self._safe_remove(name)
                raise RuntimeExecutionError(
                    OperationFailure(
                        code="runtime_start_failed",
                        message="the runtime container exited before becoming ready",
                    )
                )
            self._sleep(interval)
        self._safe_remove(name)
        raise self._timeout_failure()

    def stop(self, container_id: str) -> None:
        result = self._cli.run(
            ["rm", "-f", container_id], timeout=self._settings.stop_timeout_seconds
        )
        if result.returncode != 0 and looks_unavailable(result.stderr):
            raise RuntimeUnavailable("the docker daemon is unreachable")
        # Removing an absent container is not an error (docs: idempotent stop).

    def inspect(self, container_id: str) -> RuntimeStatus:
        result = self._cli.run(
            ["inspect", container_id], timeout=self._settings.stop_timeout_seconds
        )
        if result.returncode != 0:
            if looks_unavailable(result.stderr):
                raise RuntimeUnavailable("the docker daemon is unreachable")
            return RuntimeStatus(
                present=False, running=False, healthy=False, restart_count=0
            )
        objects = json.loads(result.stdout)
        return status_from_inspect(objects[0] if objects else {})

    def reconcile(self) -> tuple[ManagedRuntime, ...]:
        result = self._cli.run(
            ["ps", "-aq", "--filter", f"label={LABEL_MANAGED}=true"],
            timeout=self._settings.stop_timeout_seconds,
        )
        if result.returncode != 0:
            if looks_unavailable(result.stderr):
                raise RuntimeUnavailable("the docker daemon is unreachable")
            raise RuntimeExecutionError(
                OperationFailure(
                    code="runtime_reconcile_failed",
                    message="the runtime inventory could not be read",
                )
            )
        ids = result.stdout.decode("utf-8").split()
        managed: list[ManagedRuntime] = []
        for cid in ids:
            detail = self._cli.run(
                ["inspect", cid], timeout=self._settings.stop_timeout_seconds
            )
            if detail.returncode != 0:
                continue  # vanished between ps and inspect; nothing to report
            objects = json.loads(detail.stdout)
            obj = objects[0] if objects else {}
            managed.append(
                ManagedRuntime(
                    container_id=(
                        str(obj.get("Id", cid)) if isinstance(obj, dict) else cid
                    ),
                    version_id=_version_id_of(obj),
                    status=status_from_inspect(obj),
                )
            )
        return tuple(managed)

    def _safe_remove(self, reference: str) -> None:
        # Best-effort cleanup; the caller already has a terminal outcome.
        with contextlib.suppress(RuntimeUnavailable, TimeoutError):
            self._cli.run(
                ["rm", "-f", reference], timeout=self._settings.stop_timeout_seconds
            )

    def _failure(
        self, result: CliResult, code: str, what: str
    ) -> RuntimeExecutionError | RuntimeUnavailable:
        if looks_unavailable(result.stderr):
            return RuntimeUnavailable("the docker daemon is unreachable")
        # Never surface raw docker/build output (docs 07: no host paths, no raw
        # provider errors). The classified code is the diagnosis; full logs are
        # Module 8's concern.
        return RuntimeExecutionError(
            OperationFailure(code=code, message=f"the runtime {what} failed")
        )

    @staticmethod
    def _timeout_failure() -> RuntimeExecutionError:
        return RuntimeExecutionError(
            OperationFailure(
                code="runtime_readiness_timeout",
                message="the runtime did not become ready in time",
            )
        )
