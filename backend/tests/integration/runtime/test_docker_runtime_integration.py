"""Disposable-Docker integration tests for the runtime adapter.

Roadmap phase 6 exit gate: a disposable Docker test proves labels, limits,
isolation, and cleanup. These build a real image, run a real container, drive
it to health, predict through it, reconcile it, and remove it -- against the
Docker daemon. They are skipped when Docker is unavailable.

Each build uses a package with no dependencies, so the image build is hermetic
and fast (no package index is contacted); the base image is the only pull.
"""

from __future__ import annotations

import io
import json
import subprocess
import uuid
from collections.abc import Iterator, Sequence
from pathlib import Path
from shutil import which

import pytest

from forgeml.core.config import PackageLimits
from forgeml.domain.deployment.models import ResourcePolicy
from forgeml.domain.package.analyzer import analyze
from forgeml.domain.package.generator import GeneratedBuildContext, generate
from forgeml.domain.package.models import ManifestV1
from forgeml.infrastructure.package.zip_archive import ZipArchiveReader
from forgeml.infrastructure.runtime.docker import (
    LABEL_MANAGED,
    DockerRuntimeManager,
    RuntimeSettings,
    image_ref,
)
from forgeml.infrastructure.storage.artifact_store import FilesystemArtifactStore
from tests.packages import build_forge
from tests.packages import manifest as make_manifest

_TEST_NETWORK = "forgeml-runtime-test"


def _docker_available() -> bool:
    if which("docker") is None:
        return False
    try:
        result = subprocess.run(
            ["docker", "info"],  # noqa: S607 - docker resolved from PATH by design
            capture_output=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


pytestmark = pytest.mark.skipif(
    not _docker_available(), reason="docker is not available"
)


def _docker(
    args: Sequence[str], timeout: float = 30.0
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["docker", *args],  # noqa: S607 - docker resolved from PATH by design
        capture_output=True,
        timeout=timeout,
        check=False,
    )


@pytest.fixture
def runtime(
    tmp_path: Path,
) -> Iterator[tuple[DockerRuntimeManager, str, GeneratedBuildContext]]:
    store = FilesystemArtifactStore(tmp_path / "artifacts")
    document = make_manifest(dependencies=[])
    stored = store.put(io.BytesIO(build_forge(document)), PackageLimits())
    manifest = ManifestV1.model_validate(document)
    context = generate(analyze(manifest), checksum=stored.sha256)
    settings = RuntimeSettings(start_timeout_seconds=90.0, network=_TEST_NETWORK)
    manager = DockerRuntimeManager(
        store=store,
        reader=ZipArchiveReader(),
        limits=PackageLimits(),
        settings=settings,
    )
    try:
        yield manager, stored.sha256, context
    finally:
        on_net = _docker(
            ["ps", "-aq", "--filter", f"network={_TEST_NETWORK}"]
        ).stdout.split()
        if on_net:
            _docker(["rm", "-f", *(cid.decode() for cid in on_net)])
        _docker(["image", "rm", "-f", image_ref(context.identity)])
        _docker(["network", "rm", _TEST_NETWORK])


def test_full_lifecycle_proves_isolation_and_cleanup(
    runtime: tuple[DockerRuntimeManager, str, GeneratedBuildContext],
) -> None:
    manager, checksum, context = runtime
    version_id = uuid.uuid4()
    policy = ResourcePolicy(cpu_millicores=500, memory_mib=256, pids_limit=128)

    # Build proves a real, tagged image comes out of the generated context.
    image = manager.build(version_id, context, checksum, policy)
    assert image.image_ref == image_ref(context.identity)

    running = manager.start(version_id, image, policy)
    try:
        status = manager.inspect(running.container_id)
        assert status.present and status.running and status.healthy

        obj = json.loads(_docker(["inspect", running.container_id]).stdout)[0]
        host = obj["HostConfig"]
        config = obj["Config"]

        # Isolation (ADR-001): non-root, read-only, no capabilities, no new
        # privileges, isolated network, no host mounts.
        assert config["User"] == "65532:65532"
        assert host["ReadonlyRootfs"] is True
        assert host["CapDrop"] == ["ALL"]
        assert any("no-new-privileges" in opt for opt in host["SecurityOpt"])
        assert host["NetworkMode"] == _TEST_NETWORK
        assert not host["Binds"]  # no host artifact/socket mounts

        # Limits (docs 12): the policy is enforced on the container.
        assert host["Memory"] == 256 * 1024 * 1024
        assert host["PidsLimit"] == 128
        assert host["NanoCpus"] == 500_000_000

        # Labels (ADR-004): the platform can recognise exactly what it owns.
        assert config["Labels"][LABEL_MANAGED] == "true"

        # The runtime actually serves: predict through it from inside the
        # container (no host ports are published, per ADR-005).
        script = (
            "import urllib.request, json;"
            "body = json.dumps({'value': 21}).encode();"
            "req = urllib.request.Request("
            "'http://127.0.0.1:8000/predict', data=body,"
            " headers={'Content-Type': 'application/json'});"
            "print(urllib.request.urlopen(req).read().decode())"
        )
        predicted = _docker(["exec", running.container_id, "python", "-c", script])
        assert predicted.returncode == 0, predicted.stderr
        assert json.loads(predicted.stdout)["result"]["score"] == 21.0

        # Reconciliation enumerates the managed runtime and maps it back.
        managed = manager.reconcile()
        assert any(item.version_id == version_id for item in managed)
    finally:
        manager.stop(running.container_id)

    # Cleanup is deterministic: the container is gone after stop.
    assert manager.inspect(running.container_id).present is False


def test_build_failure_surfaces_no_raw_output(
    runtime: tuple[DockerRuntimeManager, str, GeneratedBuildContext],
) -> None:
    # A context whose entrypoint import fails still builds an image (the failure
    # is at start), so to force a *build* failure we corrupt the generated
    # Dockerfile's base image to one that cannot be pulled.
    manager, checksum, context = runtime
    broken = GeneratedBuildContext(
        generator_version=context.generator_version,
        runtime=context.runtime,
        files={**context.files, "Dockerfile": "FROM forgeml/does-not-exist:0\n"},
        identity="broken" + context.identity,
    )
    from forgeml.domain.deployment.ports import RuntimeExecutionError

    with pytest.raises(RuntimeExecutionError) as caught:
        manager.build(uuid.uuid4(), broken, checksum, ResourcePolicy())
    assert caught.value.failure.code == "runtime_build_failed"
    assert "forgeml/does-not-exist" not in caught.value.failure.message
