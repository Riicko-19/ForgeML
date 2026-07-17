"""Fixtures for the smoke tier.

The golden path needs its schema at head, which is exactly what the integration
suite already builds. Re-exporting that fixture here registers it for this
directory -- pytest's own way of sharing one -- so the smoke test can ask for a
migrated database without importing it and shadowing the name.
"""

from tests.integration.api.conftest import migrated

__all__ = ["migrated"]
