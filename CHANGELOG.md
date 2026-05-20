# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.2] — 2026-05-20

### Fixed

- **Default `base_url` now points at the API host.** Earlier 0.1.x
  defaulted to `https://hkfilings.app`, which is the static marketing
  site on Cloudflare Pages, not the API. Any call made with the
  default base would hit the SPA HTML fallback and the client would
  raise on `response.json()` parse failure. 0.1.2 defaults to
  `https://api.hkfilings.app`. The marketing apex still routes the
  public API paths to the Worker, so explicitly setting
  `base_url="https://hkfilings.app"` keeps working — but the new
  default avoids a confusing first-call failure.
- **`upload()` now sends the PDF as the raw request body**, with
  metadata (`ticker` / `market` / `company_name` / `language` /
  `fiscal_year`) on the query string. Earlier 0.1.x used
  `multipart/form-data` (httpx `files=` + `data=`), which the
  Cloudflare Worker stored verbatim into R2 — leaving a multipart-
  wrapped blob there instead of a real PDF, and silently dropping
  every form field. The downstream parser then failed with an opaque
  error. The new contract matches the Worker's
  `POST /v1/hk-tasks/upload` raw-body shape.

### Added

- `upload(..., language=, fiscal_year=)` parameters, matching the
  query-string contract the Worker exposes.

## [0.1.1] — 2026-05-19

### Fixed

- README image and intra-doc links now use absolute GitHub URLs so they
  render correctly on PyPI (cover image, bilingual cross-link,
  `examples/`, `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`). The 0.1.0
  release page on PyPI shows a broken cover image because PyPI does not
  resolve relative paths against the source repository.

## [0.1.0] — 2026-05-12

Initial public release.

### Added

- Synchronous `HKFilingsClient` with bindings to the v1 managed API.
- Layer 1 (financial facts) endpoints:
  - `create_task`, `analyze`, `upload`, `task_status`, `wait`
  - `result`, `facts_csv`
  - `company_matrix`
- Layer 2 (industry signals, supply-chain, catalysts) endpoints:
  - `task_signals`, `company_signals`, `patch_signal`
  - `task_supply_chain`, `company_supply_chain`
  - `task_catalysts`, `company_catalysts`
  - `intelligence_brief`
- Review endpoints:
  - `review_diff`, `patch_fact`, `fact_comment`
- Schema introspection: `schema(name=...)` for `financial_fact`,
  `industry_signal`, `supply_chain_node`, `catalyst`.
- Dataclasses with forward-compatible `extra` dict:
  - `Task`, `Fact`, `ReportEnvelope`, `Matrix`
  - `Signal`, `SignalEnvelope`
  - `SupplyChainNode`, `SupplyChainEnvelope`
  - `Catalyst`, `CatalystEnvelope`
- Custom `HKFilingsError` exposing `status_code` and parsed `payload`.
- Context-manager support (`with HKFilingsClient(...) as client:`).
- `HKFILINGS_BASE_URL` / `HKFILINGS_API_KEY` environment variables.
- Full type hints + `py.typed` marker for downstream mypy users.
- Default `base_url` points at the managed service `https://hkfilings.app`.

### Schema contract

This release ships against v1 of the public schema. New fields added by
future backend releases land in each dataclass's `extra` dict — your code
will keep working without an SDK upgrade.

[Unreleased]: https://github.com/mylovelycodes/hkfilings-python/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/mylovelycodes/hkfilings-python/releases/tag/v0.1.1
[0.1.0]: https://github.com/mylovelycodes/hkfilings-python/releases/tag/v0.1.0
