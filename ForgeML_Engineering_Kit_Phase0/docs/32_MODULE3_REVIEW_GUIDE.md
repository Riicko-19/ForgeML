# Module 3 — Review Guide

**Total review time: ~45 minutes.** Module 3 is small because Modules 0–2 already
did the hard parts: the error envelope, the correlation ID, the idempotency
index, and the transaction boundary all came for free. Almost all of the risk is
in one file.

---

## §1 — The file that matters (20 min)

### `application/package/services.py` — read in full

This is the whole module. Everything else is transport.

| Function | Why it matters |
| --- | --- |
| `PackageService.upload` | Order is load-bearing: **store the bytes → begin the operation → create the package → validate → record**. The checksum does not exist until the bytes are stored, and the operation's target *is* the checksum. Swap two lines here and idempotency breaks. |
| `PackageService._execute` | Claims **its own** operation by id (`claim`, not `claim_next`). Then validates **outside** any transaction — docs 04 forbids holding one across artifact work — and records the verdict and the audit event in a single transaction. |
| `_fingerprint` | Why reusing a key with a different filename is a 409. |
| `_validate` | The one place a *platform* failure is distinguished from a *package* verdict. `ArchiveUnreadable` → the package is rejected with a finding. `AppError` (the artifact is gone) → the **operation fails**. Getting this backwards blames the operator for a disk fault. |

---

## §2 — The contract tests (15 min)

Read the names; read these bodies:

| Test | What it pins |
| --- | --- |
| `test_reusing_a_key_for_a_different_request_conflicts` | 409, and *why* it is reachable |
| `test_the_same_key_against_different_bytes_is_a_separate_operation` | Why that is **not** a conflict (docs 04 scopes the key per target) |
| `test_the_same_bytes_under_a_new_key_resolve_to_one_package` | ADR-003 |
| `test_a_rejected_package_still_completes_its_operation` | D-2, the decision most likely to be questioned |
| `test_an_unreadable_artifact_fails_the_operation` | The other side of D-2 |
| `test_every_error_response_uses_the_frozen_envelope` | Caught a real bug: FastAPI was documenting its own 422 shape while the API returned ours |
| `test_startup_returns_an_abandoned_operation_to_the_queue` | ADR-016 actually runs |

---

## §3 — Skim (10 min)

`api/v1/packages.py`, `api/v1/operations.py`, `api/v1/schemas.py`,
`core/composition.py`, `infrastructure/database/provider.py`. Glance at
`_safe_filename` (untrusted text that reaches a database row and an audit event)
and at `encode_cursor` (without it, page two of any list is broken).

---

## §4 — Questions you should answer

1. **A rejected package returns `202` and a *succeeded* operation** (D-2). The
   client polls, sees success, then reads the package to find it was rejected.
   **Is that the shape you want, or should an invalid package fail the
   operation?** This is the most arguable decision in the module.
2. **Validation runs inside the request** (D-1). Upload latency now includes
   validation, bounded by `PackageLimits`. **Confirm that is acceptable until the
   worker lands.**
3. **`/readyz` now returns 503 without a database, and startup fails closed.** A
   deployment that forgets `FORGEML_DATABASE_URL` will not boot. **That is
   intended — confirm.**
4. **The OpenAPI schema is public; the interactive docs are not** (D-7). Fine on
   an admin network. **Revisit the moment authentication exists.**
5. **Still no authentication.** Unchanged, and still the largest risk in ForgeML.

---

## §5 — Risks

| Risk | Severity | Mitigation |
| --- | --- | --- |
| No authentication on a code-executing API | **High** | None. Documented; needs an ADR (stabilization S0-11) |
| Inline validation blocks the request thread | Medium | Bounded by `PackageLimits`; handler runs in a threadpool |
| Two concurrent uploads of the same bytes | Low | Unique index + `claim(id)`; covered by Module 2's forced race tests |
| Published schema drifts from behaviour | Low | Contract test asserts every 4xx/5xx uses the envelope |

## If you have 10 minutes

`PackageService.upload` and `_execute`. If those are right, Module 3 is right.
