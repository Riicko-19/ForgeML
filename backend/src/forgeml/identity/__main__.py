"""`python -m forgeml.identity` -- create, list, and revoke API keys (ADR-026)."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from forgeml.application.identity.services import ApiKeyAdministration
from forgeml.core.config import ConfigurationFailure, load_settings
from forgeml.core.errors import AppError
from forgeml.infrastructure.database.provider import DatabaseProvider

_CREATED = """\
API key created.

  key id  {key_id}
  name    {name}

  {token}

This is the only time the token is shown. Only its SHA-256 digest is stored,
so it cannot be recovered -- if you lose it, revoke this key and create another.
"""


def _provider() -> DatabaseProvider:
    return DatabaseProvider(load_settings())


def _create(admin: ApiKeyAdministration, args: argparse.Namespace) -> int:
    token = admin.create(name=args.name, expires_in_days=args.expires_days)
    key_id = token.split("_")[1]
    print(_CREATED.format(key_id=key_id, name=args.name, token=token))
    return 0


def _list(admin: ApiKeyAdministration, _: argparse.Namespace) -> int:
    keys = admin.list()
    if not keys:
        print(
            "No API keys. Create one with: python -m forgeml.identity create --name X"
        )
        return 0
    print(f"{'KEY ID':<18}{'NAME':<24}{'STATE':<10}{'LAST USED':<22}")
    for key in keys:
        if key.revoked_at is not None:
            state = "revoked"
        elif key.expires_at is not None and key.expires_at <= key.created_at:
            state = "expired"
        else:
            state = "active"
        last_used = key.last_used_at.isoformat() if key.last_used_at else "never"
        print(f"{key.key_id:<18}{key.name:<24}{state:<10}{last_used:<22}")
    return 0


def _revoke(admin: ApiKeyAdministration, args: argparse.Namespace) -> int:
    admin.revoke(args.key_id)
    print(f"Revoked {args.key_id}. It stops working on the next request.")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m forgeml.identity",
        description="Administer ForgeML API keys. Requires database access.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    create = commands.add_parser("create", help="Mint a key and print it once")
    create.add_argument("--name", required=True, help="What this key is for")
    create.add_argument(
        "--expires-days",
        type=int,
        default=None,
        help="Expire the key after N days (default: no expiry)",
    )
    create.set_defaults(run=_create)

    listing = commands.add_parser("list", help="List keys; secrets are not shown")
    listing.set_defaults(run=_list)

    revoke = commands.add_parser("revoke", help="Revoke a key by its key id")
    revoke.add_argument("key_id", help="The public key id, not the full token")
    revoke.set_defaults(run=_revoke)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run one key-administration command.

    Failures print a short message and exit non-zero. No traceback: this runs on
    an operator's terminal, and a stack trace there is noise that can carry a
    connection string.
    """

    args = _parser().parse_args(argv)
    try:
        provider = _provider()
    except ConfigurationFailure as failure:
        print(f"configuration error: {failure.code}", file=sys.stderr)
        return 2

    # Explicit try/finally rather than a @contextmanager: AppError is a frozen
    # slots dataclass, and contextlib unwinds by assigning to `__traceback__`,
    # which such a class refuses -- turning a clean "no such key" into an
    # unrelated TypeError. A plain finally has no such opinion.
    try:
        result: int = args.run(
            ApiKeyAdministration(unit_of_work=provider.unit_of_work), args
        )
    except AppError as error:
        print(f"error: {error.message}", file=sys.stderr)
        return 1
    finally:
        provider.dispose()
    return result


if __name__ == "__main__":
    raise SystemExit(main())
