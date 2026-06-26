# Security Policy

## Supported Versions

TokenHelm is pre-1.0. Security fixes are applied to the latest released minor version.

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅        |
| < 0.1   | ❌        |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Report privately via one of:

- GitHub's [private security advisory](https://github.com/quadkeys/tokenhelm/security/advisories/new) (preferred), or
- email **github@quadkeys.in** with subject `TokenHelm security`.

Please include:

- a description of the issue and its impact,
- steps to reproduce or a proof of concept,
- affected version(s) and environment.

### What to expect

- **Acknowledgement** within 3 business days.
- An initial assessment and severity within 7 business days.
- Coordinated disclosure: we'll agree on a timeline, prepare a fix and a patched release, and
  credit you (if desired) in the release notes.

## Scope notes

TokenHelm **observes** response objects your own client returns; it never handles your provider
credentials and makes no network calls of its own. The runtime dependency surface is a single
package (PyYAML). Relevant areas for reports include: parsing untrusted response/chunk objects,
the bundled `pricing.yaml` loader, and file output in `FileLogger`.
