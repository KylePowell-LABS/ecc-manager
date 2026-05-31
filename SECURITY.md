# Security Policy

## Supported Versions

Security fixes are currently handled on the latest released `0.x` version.

## Reporting a Vulnerability

Please report security issues privately through GitHub Security Advisories when the repository is public. If advisories are not enabled yet, open a minimal issue asking for a private reporting channel without including exploit details.

Include:

- The affected ECC Manager version or commit.
- The operating system and Python version.
- A short description of the impact.
- Reproduction steps, if safe to share privately.

## Local Web UI Model

ECC Manager is designed as a local-first tool:

- The Web UI binds to `127.0.0.1` by default.
- Mutating API calls require a local session token.
- The server regenerates plans before applying them so browser-side data cannot change managed symlink targets.
- ECC Manager only updates managed files, managed blocks, or symlinks it can verify.

Do not expose the server with `--host 0.0.0.0` unless you understand and accept the local network risk.

## Secrets and Project Files

Do not commit project lock files, generated instruction files, local ECC source trees, API keys, tokens, or personal paths when contributing examples or tests.
