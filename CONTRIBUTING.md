# Contributing to hkfilings

Thanks for your interest! This SDK is a thin HTTP client for the HK
Annual Report Parser API; the parsing engine itself is a separate
service. Below is what to do for each kind of contribution.

## Quick decision tree

- **Bug in this SDK** (wrong URL, broken type, missing field) → open
  a GitHub issue with the bug-report template and we'll fix it.
- **Parsing bug in a specific report** (wrong number, missed segment,
  hallucinated signal) → please include the `task_id` in your issue
  so the backend team can triage on the SaaS side.
- **Want a new endpoint exposed in the SDK** → open a feature request;
  we'll usually ship it within a release.
- **Want a new endpoint added to the backend** → that's a product
  request, not an SDK issue. Email product@hkfilings.app.

## Development setup

```bash
git clone https://github.com/mylovelycodes/hkfilings-python.git
cd hkfilings
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Run the test + lint suite:

```bash
pytest              # unit tests with coverage
ruff check .        # lint
ruff format .       # autoformat (run before committing)
mypy hkfilings
```

All three must pass before a PR can be merged. CI runs the same matrix
across Python 3.10 / 3.11 / 3.12 / 3.13.

## Project layout

```
hkfilings/
├── __init__.py     # public surface; touch carefully
├── _version.py     # single version source — bump here
├── client.py       # HTTP client; one method per endpoint
├── types.py        # dataclasses; mirror the v1 schema
└── py.typed        # PEP 561 marker (empty)
tests/              # pytest + pytest-httpx, mocked at the HTTP layer
examples/           # runnable notebooks + scripts
```

## Schema compatibility rules — please read

This SDK ships against a **frozen v1 public schema**. To keep
downstream code from breaking on every release, the following rules
are enforced in code review:

1. **Never add a required field** to an existing dataclass. New backend
   fields land in the `extra` dict automatically — no SDK change needed.
2. **Method signatures may only grow keyword-only optional parameters.**
   Positional argument order is part of the public contract.
3. **Never remove a method or rename it without a deprecation path.**
   Removals require: deprecation warning for one minor version, then
   removal in the next.
4. **Default behavior may not change between minor releases.** If you
   want different defaults, add a new method or an opt-in parameter.

## Tests

We test at the HTTP boundary using `pytest-httpx` — we mock the
responses, not the httpx client internals. Every method on
`HKFilingsClient` should have:

- A success-path test verifying the request shape (method, path, body).
- An error-path test verifying `HKFilingsError` propagates with
  `status_code` and `payload`.
- Optional: a forward-compat test verifying unknown response fields
  land in `extra`.

Tests must encode **why** the behavior matters, not just **what** it
does. A test like `assert client.analyze("9988", 2026).status == "pending"`
is worthless if it doesn't also assert that the request body had
`ticker="9988"` and `year=2026`. See `tests/test_analyze.py` for the
pattern.

## Pull request flow

1. Fork → branch (`fix/issue-123` or `feat/short-name`).
2. Write code + tests. Coverage must stay ≥ 85%.
3. Update `CHANGELOG.md` (the `[Unreleased]` section).
4. Run `pytest`, `ruff check .`, `mypy hkfilings` locally.
5. Open a PR using the template. Link the issue you're closing.
6. After approval, we squash-merge.

## Release process (maintainers only)

1. Bump `hkfilings/_version.py`.
2. Move the `[Unreleased]` block in `CHANGELOG.md` under a new
   `[X.Y.Z] — YYYY-MM-DD` heading.
3. `git tag vX.Y.Z && git push --tags`.
4. The `publish.yml` workflow uploads to PyPI via OIDC trusted
   publishing. Verify the new version on
   https://pypi.org/project/hkfilings/.

## Code of conduct

By participating, you agree to abide by our
[Code of Conduct](CODE_OF_CONDUCT.md).
