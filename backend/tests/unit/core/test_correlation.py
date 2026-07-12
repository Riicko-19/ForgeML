"""Correlation context tests."""

import asyncio
from uuid import UUID

from forgeml.core.correlation import (
    current_request_id,
    new_request_id,
    reset_request_id,
    set_request_id,
)


def test_new_request_id_is_uuid4() -> None:
    value = UUID(new_request_id())

    assert value.version == 4


def test_context_is_restored_by_token() -> None:
    outer = set_request_id("outer")
    inner = set_request_id("inner")
    assert current_request_id() == "inner"

    reset_request_id(inner)
    assert current_request_id() == "outer"
    reset_request_id(outer)

    assert current_request_id() is None


def test_concurrent_contexts_are_isolated() -> None:
    async def worker(value: str) -> str | None:
        token = set_request_id(value)
        await asyncio.sleep(0)
        observed = current_request_id()
        reset_request_id(token)
        return observed

    async def run() -> list[str | None]:
        return list(await asyncio.gather(worker("one"), worker("two")))

    assert asyncio.run(run()) == ["one", "two"]
    assert current_request_id() is None
