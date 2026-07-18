# Security Policy

## Supported versions

ForgeML is pre-1.0 and under active development. Only the latest release on
`main` receives security fixes (ADR-021).

| Version | Supported |
| --- | --- |
| `main` / latest release | Yes |
| Anything earlier | No |

---

## Reporting a vulnerability

**Do not open a public issue.**

Report privately through
[GitHub Security Advisories](https://github.com/Riicko-19/ForgeML/security/advisories/new).

Please include: what the issue is, how to reproduce it, and what an attacker
gains. A working proof of concept is welcome but not required.

We will acknowledge within **5 business days**, confirm or dispute within **10
business days**, and credit you in the advisory unless you prefer otherwise.

---

## The security model you are testing against

Read this before reporting — several properties below are **intentional**, and
knowing which is which will save us both time.

### ForgeML runs code you give it. That is the product.

A `.forge` package contains Python that ForgeML builds into an image and
executes. Under [ADR-001](ForgeML_Engineering_Kit_Phase0/docs/10_ARCHITECTURE_DECISIONS.md),
packages come from a **trusted operator**. ForgeML is not a sandbox for hostile
code, and "my package ran the code I put in it" is not a vulnerability.

Container isolation is defense-in-depth against a *compromised* model, not a
boundary against a *malicious* operator.

### Current posture (Epic 1 complete, Epic 2 pending)

| Property | State |
| --- | --- |
| Authentication | **Required on every `/v1` route.** API keys, always on, no bypass (ADR-025) |
| Authorization | **None.** Epic 2. Every valid key can do everything |
| Rate limiting | **None.** Epic 2 |
| Credential storage | SHA-256 digest of a 256-bit CSPRNG secret; plaintext never stored |
| Transport security | **Not provided.** Terminate TLS at a reverse proxy |
| Default bind address | `127.0.0.1`; wildcard binds are rejected by config |
| Intended deployment | Single host, administrative network only |

Authentication is not authorization. Because the control plane is root-equivalent
through the Docker daemon and no key is scoped, **every API key is a root
credential for the host.** The control plane **must not** be exposed to an
untrusted network.

Reports of the form "any valid key can do anything" or "there is no rate
limiting" are known, tracked as Epic 2, and analysed in
[`docs/SECURITY_REVIEW_EPIC_1.md`](docs/SECURITY_REVIEW_EPIC_1.md); they do not
need a private report.

### What the control plane can do

It drives the Docker daemon, and the daemon is root. **Anyone who reaches the
control plane effectively has root on the host.** This is why the deployment
model is a single administrative host, and why Epic 1 treated the authentication
boundary as protecting host root rather than model metadata.

### Runtime isolation (ADR-001)

Every model container runs:

- as a non-root user
- with a read-only root filesystem (`/tmp` is a size-capped `noexec,nosuid` tmpfs)
- with `--cap-drop ALL` and `--security-opt no-new-privileges`
- on an internal, egress-free Docker network
- under CPU, memory, and PID limits
- with **no** Docker socket mounted

A way to escape any of these **is** a vulnerability — please report it.

### Package handling

Archive extraction refuses path traversal, symlinks, and encrypted members;
enforces uncompressed-size limits during the write; and bans YAML aliases.
Validation never imports, executes, or deserializes package content, and this is
enforced by an architecture test rather than by convention.

A way to make validation execute package content, escape the extraction root, or
allocate beyond the configured limits **is** a vulnerability.

**Known gap:** `docker build` installs the package's declared dependencies, and
Python packaging executes code at install time. Build-time execution is *not*
covered by the runtime hardening above. This is tracked for Module 10.

---

## In scope

- Container escape or privilege escalation from a model runtime
- Path traversal, zip-slip, or resource exhaustion in archive handling
- Code execution in the control plane from package *validation*
- Escaping the artifact store's content-addressed layout
- Secrets or internal detail leaking through API responses, errors, or logs
- Any way to reach a `/v1` route without a valid credential
- Any way to distinguish an unknown key from a wrong, revoked, or expired one
- Recovering an API key secret from the database, logs, or an error response
- Forging an audit `actor_id`, or attributing an action to the wrong principal
- SQL injection, or any way to bypass the metadata layer's immutability triggers
- Request-ID spoofing or audit-trail forgery

## Out of scope

- Missing authorization or rate limiting (Epic 2, known and analysed)
- A valid API key being able to perform any operation (the same, by design today)
- Bearer tokens being readable over plaintext HTTP (terminate TLS in front)
- Arbitrary code execution from a package the operator deliberately uploaded
- Build-time code execution via package dependencies (known, Module 10)
- Denial of service through legitimate resource-intensive models
- Anything requiring host access you already have
- Findings against a deployment that ignores the administrative-network model

---

## Disclosure

Coordinated disclosure. We ask for **90 days** or until a fix ships, whichever is
sooner. We will not pursue legal action against good-faith research that follows
this policy.
