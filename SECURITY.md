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

### Current posture (pre-Module 9)

| Property | State |
| --- | --- |
| Authentication | **None.** Module 9. Every endpoint is open |
| Authorization | **None.** Module 9 |
| Rate limiting | **None.** Module 9 |
| Default bind address | `127.0.0.1`; wildcard binds are rejected by config |
| Intended deployment | Single host, administrative network only |

The control plane **must not** be exposed to an untrusted network today. Reports
of the form "the API has no authentication" are known and tracked as Module 9;
they do not need a private report.

### What the control plane can do

It drives the Docker daemon, and the daemon is root. **Anyone who reaches the
control plane effectively has root on the host.** This is why the deployment
model is a single administrative host and why authentication is the next module.

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
- SQL injection, or any way to bypass the metadata layer's immutability triggers
- Request-ID spoofing or audit-trail forgery

## Out of scope

- Missing authentication, authorization, or rate limiting (Module 9, known)
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
