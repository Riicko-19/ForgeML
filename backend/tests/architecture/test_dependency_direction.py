"""AST-enforced dependency direction."""

import ast
from pathlib import Path

import pytest

SOURCE = Path(__file__).parents[2] / "src" / "forgeml"

# Docs 05: the domain expresses policy over values. It may not reach for a
# provider, a transport, or the filesystem, and it may not know that a .forge
# archive happens to be a ZIP.
DOMAIN_FORBIDDEN = (
    "fastapi",
    "starlette",
    "sqlalchemy",
    "docker",
    "yaml",
    "zipfile",
    "pathlib",
    "os",
    "shutil",
    "tempfile",
    "forgeml.api",
    "forgeml.application",
    "forgeml.infrastructure",
)

# The package owner's acceptance gate: no validation path may import, execute,
# or deserialize package content.
EXECUTION_FORBIDDEN = (
    "importlib",
    "imp",
    "runpy",
    "pickle",
    "marshal",
    "shelve",
    "subprocess",
    "joblib",
    "torch",
)

PACKAGE_PATHS = (
    SOURCE / "domain" / "package",
    SOURCE / "application" / "package",
    SOURCE / "infrastructure" / "package",
    SOURCE / "infrastructure" / "storage",
)


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


@pytest.mark.parametrize(
    "path", sorted((SOURCE / "api").rglob("*.py")), ids=lambda path: path.name
)
def test_api_adapts_application_and_never_reaches_a_provider(path: Path) -> None:
    """Docs 02: the API adapter may depend on application use cases, and must
    not reach a provider. It maps transport DTOs to commands; it holds no
    lifecycle rules and never touches an ORM, an artifact path, or Docker.

    Module 0's original rule forbade `forgeml.application` outright, because no
    application layer existed yet. Enforcing that today would contradict the
    dependency direction the FEK actually specifies.
    """

    assert (
        _violations(
            path,
            ("forgeml.bootstrap", "forgeml.infrastructure", "sqlalchemy", "docker"),
        )
        == set()
    )


def test_bootstrap_imports_core_not_api() -> None:
    imports = _imports(SOURCE / "bootstrap.py")
    assert not any(item.startswith("forgeml.api") for item in imports)


def _violations(path: Path, forbidden: tuple[str, ...]) -> set[str]:
    return {
        item
        for item in _imports(path)
        for prefix in forbidden
        if item == prefix or item.startswith(f"{prefix}.")
    }


@pytest.mark.parametrize(
    "path", sorted((SOURCE / "domain").rglob("*.py")), ids=lambda path: path.name
)
def test_domain_depends_on_no_provider_transport_or_filesystem(path: Path) -> None:
    assert _violations(path, DOMAIN_FORBIDDEN) == set()


@pytest.mark.parametrize(
    "path", sorted((SOURCE / "application").rglob("*.py")), ids=lambda path: path.name
)
def test_application_depends_on_domain_not_providers(path: Path) -> None:
    assert (
        _violations(path, ("fastapi", "forgeml.api", "forgeml.infrastructure")) == set()
    )


ORM_HOME = SOURCE / "infrastructure" / "database"


@pytest.mark.parametrize(
    "path",
    sorted(item for item in SOURCE.rglob("*.py") if ORM_HOME not in item.parents),
    ids=lambda path: str(path.relative_to(SOURCE)),
)
def test_sqlalchemy_never_escapes_the_database_adapter(path: Path) -> None:
    """The ORM is confined to one package.

    If SQLAlchemy can be imported anywhere else, a mapped object eventually
    reaches domain policy, and a lazy load fires outside a session in
    production. The membrane is the mapper layer, and this is what holds it.
    """

    assert _violations(path, ("sqlalchemy", "alembic", "psycopg")) == set()


@pytest.mark.parametrize(
    "path",
    sorted(item for root in PACKAGE_PATHS for item in root.rglob("*.py")),
    ids=lambda path: str(path.relative_to(SOURCE)),
)
def test_no_package_path_can_import_or_deserialize_package_content(path: Path) -> None:
    assert _violations(path, EXECUTION_FORBIDDEN) == set()

    tree = ast.parse(path.read_text(encoding="utf-8"))
    called = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert not called & {"eval", "exec", "compile", "__import__"}


# --------------------------------------------------------------------------
# Epic 1: the authentication and identity boundaries (ADR-019, ADR-023).
#
# ADR-019: "A boundary defended only by review is a boundary already lost."
# --------------------------------------------------------------------------

IDENTITY_HOME = SOURCE / "domain" / "identity"

#: The credential lives in the API layer and the identity use cases. Nothing
#: below may import the machinery of proving who someone is -- an application
#: service that can hash a secret is one refactor away from verifying one.
CREDENTIAL_MODULES = ("forgeml.domain.identity.credentials",)


@pytest.mark.parametrize(
    "path",
    sorted((SOURCE / "domain").rglob("*.py")),
    ids=lambda path: path.name,
)
def test_the_identity_domain_is_the_only_domain_that_knows_about_credentials(
    path: Path,
) -> None:
    """Identity policy is confined to one package.

    Deployment or package policy that could reach a credential type would be
    policy that can branch on who is asking, and ADR-019 keeps the domain
    decidable without knowing that.
    """

    if IDENTITY_HOME in path.parents:
        return

    assert _violations(path, CREDENTIAL_MODULES) == set()


@pytest.mark.parametrize(
    "path",
    sorted((SOURCE / "application").rglob("*.py"))
    + sorted((SOURCE / "domain").rglob("*.py")),
    ids=lambda path: str(path.relative_to(SOURCE)),
)
def test_no_transport_credential_type_crosses_below_the_api(path: Path) -> None:
    """ADR-019: no credential, header, token, or request object may cross into
    the application or domain layers.

    The application layer receives a Principal -- a domain value -- exactly as
    it already receives a correlation id. If a Request or a header type can be
    imported here, authentication has started leaking downward.
    """

    forbidden = (
        "starlette",
        "fastapi",
        "forgeml.api",
        "forgeml.core.principal",
    )

    assert _violations(path, forbidden) == set()


def test_the_principal_context_is_read_only_inside_the_api_layer() -> None:
    """`core.principal` is a transport detail with exactly one consumer.

    Services take a Principal as an argument. If anything outside the API layer
    reads the contextvar instead, the dependency becomes invisible: the service
    would look pure and behave differently depending on an ambient value.
    """

    readers = {
        path.relative_to(SOURCE).as_posix()
        for path in SOURCE.rglob("*.py")
        if "forgeml.core.principal" in _imports(path)
    }

    assert readers == {"api/authentication.py"}


def test_no_authorization_check_has_appeared_yet() -> None:
    """Epic 1 is authentication only; authorization is Epic 2 (ADR-019).

    Scanned as declared names rather than as text, so prose about file
    permissions or an ADR reference in a docstring does not trip it. A real
    permission check would arrive as a function or a class, and it would arrive
    without the model ADR-019 says it needs -- becoming the thing Epic 2 has to
    stay compatible with instead of designing freely.
    """

    marker_words = ("permission", "authorize", "authorization", "allowed", "role")
    declared: set[str] = set()
    for path in SOURCE.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                name = node.name.lower()
                if any(word in name for word in marker_words):
                    declared.add(f"{path.relative_to(SOURCE).as_posix()}:{node.name}")

    assert declared == set()
