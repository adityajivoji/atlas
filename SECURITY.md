# Security Policy

## Supported versions

Security fixes are handled on the default branch until the project publishes versioned releases.

## Reporting a vulnerability

Please do not report security vulnerabilities in public GitHub issues.

Email the maintainers at `security@example.com` with:

- A description of the vulnerability.
- Steps to reproduce or a proof of concept.
- The affected version or commit.
- Any known mitigation.

You should receive an acknowledgement within 72 hours. Replace `security@example.com` with the project's real security contact before publishing the repository.

## Secret handling

- Never commit `.env` files, private keys, certificates, database dumps, or generated signing key registries.
- Use `.env.example` for non-secret configuration templates.
- Rotate any credential immediately if it may have been committed, logged, or shared publicly.

## Local development defaults

Docker Compose uses development-only credentials and generates local signing keys into a Docker volume. Do not reuse these values or keys in production.
