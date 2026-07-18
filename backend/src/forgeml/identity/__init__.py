"""Out-of-band API key administration (ADR-026).

Deliberately a CLI and not a route. Epic 1 delivers authentication without
authorization, so an authenticated key-creation endpoint would let every valid
key mint more keys -- a leaked key could issue itself a permanent replacement,
and revoking the original would accomplish nothing.

This tool's authorization is possession of the database credential and shell
access on the host, which is the same authority needed to run the control plane
at all. It therefore grants nothing an operator at that level does not already
have, which is the test for whether an out-of-band tool is a hole.

HTTP key management arrives with Epic 2, where a key can carry a scope and
"may this principal mint keys" has somewhere to be asked.
"""
