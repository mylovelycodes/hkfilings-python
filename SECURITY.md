# Security Policy

## Supported versions

Only the latest minor release of `hkfilings` receives security
fixes. Patch versions are cut as needed.

| Version | Status |
| ------- | ------ |
| 0.1.x   | Supported |

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security reports.

Email **security@hkfilings.app** with:

- A description of the issue and its impact.
- Steps to reproduce (a minimal proof-of-concept is ideal).
- The SDK version (`pip show hkfilings`) and Python version.
- Optional: your suggested fix.

We aim to:

- Acknowledge receipt within **72 hours**.
- Provide a triage update within **7 days**.
- Ship a fix within **30 days** for high-severity issues.

If the issue is in the managed API (not the SDK itself), we'll route
it to the backend team. Either way, you'll hear back from us.

## Scope

In scope:

- Bugs in this Python package that lead to credential leakage, code
  execution, or sending requests to unintended hosts.
- Vulnerabilities in our pinned dependencies that this SDK is exposed
  to in its default configuration.

Out of scope:

- Backend / parsing service vulnerabilities — report those separately.
- Social-engineering or physical attacks.
- Theoretical issues without a practical exploit path.

## API key hygiene

API keys are sensitive. Treat them like passwords:

- Never commit them to git. Use environment variables (`HKFILINGS_API_KEY`)
  or a secrets manager.
- Rotate immediately if leaked. The dashboard at
  https://hkfilings.app/dashboard has a "Revoke" button.
- Keys prefixed `ak_live_` are production. Keys prefixed `ak_test_`
  are sandbox.

We participate in GitHub's secret-scanning partner program; keys
accidentally pushed to public repos are auto-revoked.
