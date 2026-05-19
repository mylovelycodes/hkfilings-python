"""Lightweight dataclasses mirroring the v1 public schema.

These avoid pulling pydantic into the SDK so the client stays small and
import-fast. ``from_dict`` accepts the JSON objects served by the API; any
unknown keys are kept on the ``extra`` mapping for forward compatibility —
a backend release adding new fields will never break SDK consumers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _coerce_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


@dataclass
class Task:
    task_id: str
    status: str
    progress_percent: int | None = None
    progress_stage: str | None = None
    review_status: str | None = None
    has_result: bool = False
    has_pdf: bool = False
    error_message: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Task:
        known = {f.name for f in cls.__dataclass_fields__.values()}
        extra = {k: v for k, v in data.items() if k not in known}
        return cls(
            task_id=data["task_id"],
            status=data["status"],
            progress_percent=_coerce_int(data.get("progress_percent")),
            progress_stage=data.get("progress_stage"),
            review_status=data.get("review_status"),
            has_result=bool(data.get("has_result")),
            has_pdf=bool(data.get("has_pdf")),
            error_message=data.get("error_message"),
            extra=extra,
        )


# ---------------------------------------------------------------------------
# Layer 1 — financial facts
# ---------------------------------------------------------------------------


@dataclass
class Fact:
    metric_key: str
    metric_label: str | None = None
    value: float | None = None
    comparable_value: float | None = None
    yoy_change: float | None = None
    source_page: int | None = None
    source_text: str | None = None
    confidence: float = 0.0
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Fact:
        known = {f.name for f in cls.__dataclass_fields__.values()}
        extra = {k: v for k, v in data.items() if k not in known}
        return cls(
            metric_key=data.get("metric_key", ""),
            metric_label=data.get("metric_label"),
            value=_coerce_float(data.get("value")),
            comparable_value=_coerce_float(data.get("comparable_value")),
            yoy_change=_coerce_float(data.get("yoy_change")),
            source_page=_coerce_int(data.get("source_page")),
            source_text=data.get("source_text"),
            confidence=_coerce_float(data.get("confidence")) or 0.0,
            extra=extra,
        )


@dataclass
class ReportEnvelope:
    task_id: str
    schema_version: str
    company: dict[str, Any]
    facts: list[Fact]
    validation: list[dict[str, Any]]
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_legacy(cls, task_id: str, data: dict[str, Any]) -> ReportEnvelope:
        report = data.get("json_report") or {}
        company = report.get("company") or {}
        raw_facts = report.get("facts") or []
        facts = [Fact.from_dict(item) for item in raw_facts if isinstance(item, dict)]
        return cls(
            task_id=task_id,
            schema_version=data.get("schema_version") or "1.0",
            company=company,
            facts=facts,
            validation=report.get("validation") or [],
            extra={k: v for k, v in data.items() if k not in {"json_report", "schema_version"}},
        )


@dataclass
class Matrix:
    schema_version: str
    ticker: str
    periods: list[str]
    metrics: list[dict[str, Any]]
    cells: list[dict[str, Any]]
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Matrix:
        known = {f.name for f in cls.__dataclass_fields__.values()}
        extra = {k: v for k, v in data.items() if k not in known}
        return cls(
            schema_version=data.get("schema_version", "1.0"),
            ticker=data.get("ticker", ""),
            periods=list(data.get("periods") or []),
            metrics=list(data.get("metrics") or []),
            cells=list(data.get("cells") or []),
            extra=extra,
        )


# ---------------------------------------------------------------------------
# Layer 2 — industry signals, supply-chain edges, catalysts
# ---------------------------------------------------------------------------


@dataclass
class Signal:
    """An industry signal extracted from the MD&A / risk / outlook sections.

    Each row is bound to an evidence page + source text with a confidence
    score; ``review_status`` reflects whether a human or the automated
    anti-hallucination pipeline has validated the row.
    """

    signal_id: str
    task_id: str | None = None
    ticker: str | None = None
    market: str | None = None
    signal_type: str = ""
    signal_category: str | None = None
    direction: str | None = None
    strength: str | None = None
    time_horizon: str | None = None
    summary: str | None = None
    rationale: str | None = None
    affected_segments: list[Any] = field(default_factory=list)
    upstream_entities: list[Any] = field(default_factory=list)
    downstream_entities: list[Any] = field(default_factory=list)
    industry_tags: list[Any] = field(default_factory=list)
    financial_metrics_linked: list[Any] = field(default_factory=list)
    linked_fact_ids: list[Any] = field(default_factory=list)
    evidence: list[Any] = field(default_factory=list)
    confidence: float = 0.0
    review_status: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Signal:
        known = {f.name for f in cls.__dataclass_fields__.values()}
        extra = {k: v for k, v in data.items() if k not in known}
        return cls(
            signal_id=str(data.get("signal_id") or ""),
            task_id=data.get("task_id"),
            ticker=data.get("ticker"),
            market=data.get("market"),
            signal_type=data.get("signal_type") or "",
            signal_category=data.get("signal_category"),
            direction=data.get("direction"),
            strength=data.get("strength"),
            time_horizon=data.get("time_horizon"),
            summary=data.get("summary"),
            rationale=data.get("rationale"),
            affected_segments=_coerce_list(data.get("affected_segments")),
            upstream_entities=_coerce_list(data.get("upstream_entities")),
            downstream_entities=_coerce_list(data.get("downstream_entities")),
            industry_tags=_coerce_list(data.get("industry_tags")),
            financial_metrics_linked=_coerce_list(data.get("financial_metrics_linked")),
            linked_fact_ids=_coerce_list(data.get("linked_fact_ids")),
            evidence=_coerce_list(data.get("evidence")),
            confidence=_coerce_float(data.get("confidence")) or 0.0,
            review_status=data.get("review_status"),
            extra=extra,
        )


@dataclass
class SignalEnvelope:
    """Envelope returned by ``/v1/hk-tasks/{id}/signals`` and
    ``/v1/hk-companies/{ticker}/signals``."""

    schema_version: str
    count: int
    signals: list[Signal]
    task_id: str | None = None
    ticker: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SignalEnvelope:
        raw = data.get("signals") or []
        signals = [Signal.from_dict(item) for item in raw if isinstance(item, dict)]
        return cls(
            schema_version=str(data.get("schema_version") or "1.0"),
            count=_coerce_int(data.get("count")) or len(signals),
            signals=signals,
            task_id=data.get("task_id"),
            ticker=data.get("ticker"),
            extra={
                k: v
                for k, v in data.items()
                if k not in {"schema_version", "count", "signals", "task_id", "ticker"}
            },
        )


@dataclass
class SupplyChainNode:
    """One edge of the supply-chain graph — the company's relationship to
    a single external entity (supplier / customer / competitor / regulator
    / substitute / partner)."""

    edge_id: str
    task_id: str | None = None
    ticker: str | None = None
    market: str | None = None
    node_role: str = ""
    node_type: str | None = None
    node_label: str = ""
    linked_segments: list[Any] = field(default_factory=list)
    exposure_share: float | None = None
    direction_to_company: str | None = None
    evidence_page: int | None = None
    evidence_text: str | None = None
    confidence: float = 0.0
    review_status: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SupplyChainNode:
        known = {f.name for f in cls.__dataclass_fields__.values()}
        extra = {k: v for k, v in data.items() if k not in known}
        return cls(
            edge_id=str(data.get("edge_id") or ""),
            task_id=data.get("task_id"),
            ticker=data.get("ticker"),
            market=data.get("market"),
            node_role=data.get("node_role") or "",
            node_type=data.get("node_type"),
            node_label=data.get("node_label") or "",
            linked_segments=_coerce_list(data.get("linked_segments")),
            exposure_share=_coerce_float(data.get("exposure_share")),
            direction_to_company=data.get("direction_to_company"),
            evidence_page=_coerce_int(data.get("evidence_page")),
            evidence_text=data.get("evidence_text"),
            confidence=_coerce_float(data.get("confidence")) or 0.0,
            review_status=data.get("review_status"),
            extra=extra,
        )


@dataclass
class SupplyChainEnvelope:
    """Envelope returned by ``/v1/hk-tasks/{id}/supply-chain`` and
    ``/v1/hk-companies/{ticker}/supply-chain``."""

    schema_version: str
    count: int
    nodes: list[SupplyChainNode]
    task_id: str | None = None
    ticker: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SupplyChainEnvelope:
        raw = data.get("supply_chain") or data.get("nodes") or []
        nodes = [SupplyChainNode.from_dict(item) for item in raw if isinstance(item, dict)]
        return cls(
            schema_version=str(data.get("schema_version") or "1.0"),
            count=_coerce_int(data.get("count")) or len(nodes),
            nodes=nodes,
            task_id=data.get("task_id"),
            ticker=data.get("ticker"),
            extra={
                k: v
                for k, v in data.items()
                if k not in {"schema_version", "count", "supply_chain", "nodes", "task_id", "ticker"}
            },
        )


@dataclass
class Catalyst:
    """A forward-looking catalyst (upcoming event likely to move the stock
    in the next 1–4 quarters), each backed by evidence in the report."""

    catalyst_id: str
    task_id: str | None = None
    ticker: str | None = None
    market: str | None = None
    catalyst_type: str = ""
    direction: str | None = None
    expected_horizon: str | None = None
    summary: str | None = None
    evidence_page: int | None = None
    evidence_text: str | None = None
    confidence: float = 0.0
    review_status: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Catalyst:
        known = {f.name for f in cls.__dataclass_fields__.values()}
        extra = {k: v for k, v in data.items() if k not in known}
        return cls(
            catalyst_id=str(data.get("catalyst_id") or ""),
            task_id=data.get("task_id"),
            ticker=data.get("ticker"),
            market=data.get("market"),
            catalyst_type=data.get("catalyst_type") or "",
            direction=data.get("direction"),
            expected_horizon=data.get("expected_horizon"),
            summary=data.get("summary"),
            evidence_page=_coerce_int(data.get("evidence_page")),
            evidence_text=data.get("evidence_text"),
            confidence=_coerce_float(data.get("confidence")) or 0.0,
            review_status=data.get("review_status"),
            extra=extra,
        )


@dataclass
class CatalystEnvelope:
    """Envelope returned by ``/v1/hk-tasks/{id}/catalysts`` and
    ``/v1/hk-companies/{ticker}/catalysts``."""

    schema_version: str
    count: int
    catalysts: list[Catalyst]
    task_id: str | None = None
    ticker: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CatalystEnvelope:
        raw = data.get("catalysts") or []
        catalysts = [Catalyst.from_dict(item) for item in raw if isinstance(item, dict)]
        return cls(
            schema_version=str(data.get("schema_version") or "1.0"),
            count=_coerce_int(data.get("count")) or len(catalysts),
            catalysts=catalysts,
            task_id=data.get("task_id"),
            ticker=data.get("ticker"),
            extra={
                k: v
                for k, v in data.items()
                if k not in {"schema_version", "count", "catalysts", "task_id", "ticker"}
            },
        )
