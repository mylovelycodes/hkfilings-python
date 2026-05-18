# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
- Default `base_url` points at the managed service `https://api.hkfilings.app`.

### Schema contract

This release ships against v1 of the public schema. New fields added by
future backend releases land in each dataclass's `extra` dict — your code
will keep working without an SDK upgrade.

[Unreleased]: https://github.com/mylovelycodes/hkfilings-python/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/mylovelycodes/hkfilings-python/releases/tag/v0.1.0
