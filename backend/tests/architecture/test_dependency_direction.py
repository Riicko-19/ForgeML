"""AST-enforced Module 0 dependency direction."""

import ast
from pathlib import Path

SOURCE = Path(__file__).parents[2] / "src" / "forgeml"


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_provider_neutral_core_does_not_import_fastapi_or_api() -> None:
    for name in ("config.py", "correlation.py", "errors.py", "logging.py"):
        imports = _imports(SOURCE / "core" / name)
        assert "fastapi" not in imports
        assert not any(item.startswith("forgeml.api") for item in imports)


def test_api_never_imports_bootstrap_or_future_modules() -> None:
    forbidden = (
        "forgeml.bootstrap",
        "forgeml.application",
        "forgeml.domain",
        "forgeml.infrastructure",
    )
    for path in (SOURCE / "api").glob("*.py"):
        imports = _imports(path)
        assert not any(
            item == prefix or item.startswith(f"{prefix}.")
            for item in imports
            for prefix in forbidden
        )


def test_bootstrap_imports_core_not_api() -> None:
    imports = _imports(SOURCE / "bootstrap.py")
    assert not any(item.startswith("forgeml.api") for item in imports)
