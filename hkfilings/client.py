"""HKFilingsClient — sync HTTP client built on httpx.

Designed to be small, dependency-light and stable across schema changes.
All paths use the v1 prefix; legacy 0.x endpoints will fail with 410.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any

import httpx

from ._version import __version__
from .types import (
    Catalyst,
    CatalystEnvelope,
    Fact,
    Matrix,
    ReportEnvelope,
    Signal,
    SignalEnvelope,
    SupplyChainEnvelope,
    SupplyChainNode,
    Task,
)

DEFAULT_BASE_URL = "https://api.hkfilings.app"
"""Public managed endpoint. Override via ``base_url=`` to self-host."""

_VALID_SCHEMA_NAMES: frozenset[str] = frozenset({
    "financial_fact",
    "industry_signal",
    "supply_chain_node",
    "catalyst",
})


class HKFilingsError(Exception):
    """Raised on non-2xx responses from the API.

    ``status_code`` and ``payload`` (the parsed JSON body, if any) are
    surfaced so callers can branch on them without re-parsing.
    """

    def __init__(
        self,
        status_code: int,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(f"{status_code}: {message}")
        self.status_code = status_code
        self.payload = payload or {}


class HKFilingsClient:
    """Synchronous client for the HKFilings API.

    Example:
        >>> from hkfilings import HKFilingsClient
        >>> client = HKFilingsClient(api_key="ak_...")
        >>> task = client.analyze(ticker="9988", year=2026)
        >>> report = client.wait(task.task_id)
        >>> for f in report.facts:
        ...     print(f.metric_key, f.value, f.source_page)

    The default ``base_url`` points at the managed service at
    ``https://api.hkfilings.app``. Get a free API key (20 tasks/month, no
    credit card) at https://hkfilings.app/signup. Set ``base_url`` to
    target a self-hosted backend.
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 60.0,
        user_agent: str | None = None,
    ) -> None:
        resolved_base = base_url or os.environ.get("HKFILINGS_BASE_URL") or DEFAULT_BASE_URL
        resolved_key = api_key or os.environ.get("HKFILINGS_API_KEY")
        headers: dict[str, str] = {
            "user-agent": user_agent or f"hkfilings-python/{__version__}",
        }
        if resolved_key:
            headers["x-api-key"] = resolved_key
        else:
            # Soft warning — not all endpoints require a key (demo / public
            # schema introspection), but most do. We don't raise so users
            # can call schema()/health on a self-hosted instance freely.
            print(
                "[hkfilings] no api_key provided; most endpoints require one. "
                "Get a free key at https://hkfilings.app/signup",
                file=sys.stderr,
            )
        self._client = httpx.Client(
            base_url=resolved_base.rstrip("/"),
            headers=headers,
            timeout=timeout,
        )
        self.base_url = resolved_base.rstrip("/")

    # ------------------------------------------------------------------
    # context-manager helpers
    # ------------------------------------------------------------------

    def __enter__(self) -> HKFilingsClient:
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    # ------------------------------------------------------------------
    # raw http
    # ------------------------------------------------------------------

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        response = self._client.request(method, path, **kwargs)
        if not 200 <= response.status_code < 300:
            try:
                payload = response.json()
                detail = payload.get("detail") or response.text
            except Exception:
                payload = {}
                detail = response.text
            raise HKFilingsError(response.status_code, detail or "request failed", payload)
        return response

    def _json(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        data: dict[str, Any] = self._request(method, path, **kwargs).json()
        return data

    # ------------------------------------------------------------------
    # Layer 1 — tasks
    # ------------------------------------------------------------------

    def create_task(
        self,
        pdf_url: str,
        company_name: str | None = None,
        ticker: str | None = None,
        market: str = "HK",
    ) -> Task:
        """Create a parsing task for a PDF reachable at ``pdf_url``."""
        body = {
            "pdf_url": pdf_url,
            "company_name": company_name,
            "ticker": ticker,
            "market": market,
        }
        return Task.from_dict(self._json("POST", "/v1/hk-tasks", json=body))

    def analyze(
        self,
        ticker: str,
        year: int,
        market: str = "HK",
        language: str = "zh",
        force: bool = False,
        company_name: str | None = None,
    ) -> Task:
        """Analyze the latest report for ``ticker`` in fiscal ``year``.

        The backend auto-discovers the PDF from HKEXnews.
        """
        body = {
            "ticker": ticker,
            "year": year,
            "market": market,
            "language": language,
            "force": force,
            "company_name": company_name,
        }
        return Task.from_dict(self._json("POST", "/v1/hk-tasks/analyze", json=body))

    def upload(
        self,
        file_path: str | Path,
        ticker: str | None = None,
        company_name: str | None = None,
        market: str = "HK",
    ) -> Task:
        """Upload a local PDF for parsing."""
        path = Path(file_path)
        with path.open("rb") as fh:
            files = {"file": (path.name, fh, "application/pdf")}
            data: dict[str, Any] = {"market": market}
            if ticker:
                data["ticker"] = ticker
            if company_name:
                data["company_name"] = company_name
            return Task.from_dict(self._json("POST", "/v1/hk-tasks/upload", files=files, data=data))

    def task_status(self, task_id: str) -> Task:
        """Return the current status of a task."""
        return Task.from_dict(self._json("GET", f"/v1/hk-tasks/{task_id}"))

    def wait(
        self,
        task_id: str,
        timeout: float = 600.0,
        poll_interval: float = 2.0,
    ) -> ReportEnvelope:
        """Block until ``task_id`` reaches a terminal state, then return its result.

        Raises ``HKFilingsError`` with status_code 408 on timeout,
        409 if the task ended in ``failed`` or ``canceled``.
        """
        deadline = time.time() + timeout
        while True:
            task = self.task_status(task_id)
            if task.status == "completed":
                return self.result(task_id)
            if task.status in {"failed", "canceled"}:
                raise HKFilingsError(
                    409,
                    f"task ended in state '{task.status}': {task.error_message or 'no message'}",
                )
            if time.time() > deadline:
                raise HKFilingsError(408, f"timed out waiting for task {task_id}")
            time.sleep(poll_interval)

    def result(self, task_id: str) -> ReportEnvelope:
        """Fetch the Layer 1 financial facts report for a completed task."""
        data = self._json("GET", f"/v1/hk-tasks/{task_id}/result")
        return ReportEnvelope.from_legacy(task_id, data)

    def facts_csv(self, task_id: str) -> bytes:
        """Return the facts of a completed task as CSV bytes."""
        return self._request("GET", f"/v1/hk-tasks/{task_id}/facts.csv").content

    # ------------------------------------------------------------------
    # company / matrix
    # ------------------------------------------------------------------

    def company_matrix(self, ticker: str, metrics: list[str] | None = None) -> Matrix:
        """Cross-period matrix of facts for ``ticker``.

        Returns a period × metric grid suitable for time-series analysis.
        Filter by ``metrics=["revenue", "gross_profit"]`` to narrow scope.
        """
        params: dict[str, Any] = {}
        if metrics:
            params["metrics"] = ",".join(metrics)
        return Matrix.from_dict(
            self._json("GET", f"/v1/hk-companies/{ticker}/matrix", params=params)
        )

    # ------------------------------------------------------------------
    # Layer 2 — industry signals
    # ------------------------------------------------------------------

    def task_signals(
        self,
        task_id: str,
        review_status: str | None = None,
        signal_type: str | None = None,
    ) -> SignalEnvelope:
        """Industry signals extracted from a single task's report.

        ``signal_type`` filters by type (e.g. ``segment_growth``,
        ``margin_driver``, ``upstream_cost``). ``review_status`` filters
        by review state (``approved`` / ``auto_passed`` / ``pending`` / ...).
        """
        params: dict[str, Any] = {}
        if review_status:
            params["review_status"] = review_status
        if signal_type:
            params["signal_type"] = signal_type
        return SignalEnvelope.from_dict(
            self._json("GET", f"/v1/hk-tasks/{task_id}/signals", params=params)
        )

    def company_signals(
        self,
        ticker: str,
        period: str | None = None,
        signal_type: str | None = None,
        review_status: str | None = "approved,auto_passed",
    ) -> SignalEnvelope:
        """Cross-period signal feed for ``ticker``.

        Default ``review_status`` filter excludes pending / changes_requested
        rows. Pass ``None`` to include everything.
        """
        params: dict[str, Any] = {}
        if period:
            params["period"] = period
        if signal_type:
            params["signal_type"] = signal_type
        if review_status:
            params["review_status"] = review_status
        return SignalEnvelope.from_dict(
            self._json("GET", f"/v1/hk-companies/{ticker}/signals", params=params)
        )

    def patch_signal(self, signal_id: str, **fields: Any) -> dict[str, Any]:
        """Update a single signal's review fields (status / summary / direction / ...)."""
        return self._json("PATCH", f"/v1/hk-signals/{signal_id}", json=fields)

    # ------------------------------------------------------------------
    # Layer 2 — supply-chain graph
    # ------------------------------------------------------------------

    def task_supply_chain(self, task_id: str) -> SupplyChainEnvelope:
        """Supply-chain nodes (suppliers / customers / competitors / regulators /
        substitutes / partners) extracted from a single task's report."""
        return SupplyChainEnvelope.from_dict(
            self._json("GET", f"/v1/hk-tasks/{task_id}/supply-chain")
        )

    def company_supply_chain(
        self,
        ticker: str,
        review_status: str | None = "approved,auto_passed",
    ) -> SupplyChainEnvelope:
        """Cross-period supply-chain feed for ``ticker``."""
        params: dict[str, Any] = {}
        if review_status:
            params["review_status"] = review_status
        return SupplyChainEnvelope.from_dict(
            self._json("GET", f"/v1/hk-companies/{ticker}/supply-chain", params=params)
        )

    # ------------------------------------------------------------------
    # Layer 2 — catalysts
    # ------------------------------------------------------------------

    def task_catalysts(self, task_id: str) -> CatalystEnvelope:
        """Forward-looking catalysts (1–4Q horizon) extracted from a task's report."""
        return CatalystEnvelope.from_dict(
            self._json("GET", f"/v1/hk-tasks/{task_id}/catalysts")
        )

    def company_catalysts(
        self,
        ticker: str,
        review_status: str | None = "approved,auto_passed",
    ) -> CatalystEnvelope:
        """Cross-period catalyst feed for ``ticker``."""
        params: dict[str, Any] = {}
        if review_status:
            params["review_status"] = review_status
        return CatalystEnvelope.from_dict(
            self._json("GET", f"/v1/hk-companies/{ticker}/catalysts", params=params)
        )

    # ------------------------------------------------------------------
    # Layer 2 — intelligence brief
    # ------------------------------------------------------------------

    def intelligence_brief(self, task_id: str) -> dict[str, Any]:
        """Executive intelligence brief (rich nested structure) for a task.

        Returned as a raw dict (no dataclass wrapper) because the brief
        layout is plan-tier-aware and may include arbitrarily-nested
        sections.
        """
        return self._json("GET", f"/v1/hk-tasks/{task_id}/intelligence-brief")

    # ------------------------------------------------------------------
    # Review (Layer 1 facts)
    # ------------------------------------------------------------------

    def review_diff(
        self,
        task_id: str,
        from_version: int | None = None,
        to_version: int | None = None,
    ) -> dict[str, Any]:
        """Diff between two review versions of a task."""
        params: dict[str, Any] = {}
        if from_version is not None:
            params["from_version"] = from_version
        if to_version is not None:
            params["to_version"] = to_version
        return self._json("GET", f"/v1/hk-tasks/{task_id}/review/diff", params=params)

    def patch_fact(self, fact_id: str, **fields: Any) -> dict[str, Any]:
        """Update a single fact's review fields."""
        return self._json("PATCH", f"/v1/hk-facts/{fact_id}", json=fields)

    def fact_comment(
        self,
        fact_id: str,
        body: str,
        author: str | None = None,
    ) -> dict[str, Any]:
        """Attach a review comment to a fact."""
        return self._json(
            "POST",
            f"/v1/hk-facts/{fact_id}/comments",
            json={"body": body, "author": author},
        )

    # ------------------------------------------------------------------
    # Schema introspection
    # ------------------------------------------------------------------

    def schema(self, name: str = "financial_fact") -> dict[str, Any]:
        """Fetch a JSON Schema document for one of the public v1 record types.

        Valid names: ``financial_fact`` (default), ``industry_signal``,
        ``supply_chain_node``, ``catalyst``. These schemas are part of
        the frozen v1 contract — see https://docs.hkfilings.app/schema.
        """
        if name not in _VALID_SCHEMA_NAMES:
            raise ValueError(
                f"name must be one of {sorted(_VALID_SCHEMA_NAMES)}, got {name!r}"
            )
        return self._json("GET", f"/v1/schema/{name}")


__all__ = [
    "DEFAULT_BASE_URL",
    "HKFilingsClient",
    "HKFilingsError",
    # Re-export types so users only need one import line:
    "Task",
    "Fact",
    "ReportEnvelope",
    "Matrix",
    "Signal",
    "SignalEnvelope",
    "SupplyChainNode",
    "SupplyChainEnvelope",
    "Catalyst",
    "CatalystEnvelope",
]
