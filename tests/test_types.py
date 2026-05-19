"""Dataclass `from_dict` semantics — the forward-compat contract lives here."""

from __future__ import annotations

from hkfilings.types import (
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
    _coerce_float,
    _coerce_int,
    _coerce_list,
)

# ---------------------------------------------------------------------------
# coercion helpers
# ---------------------------------------------------------------------------


def test_coerce_float_preserves_none() -> None:
    """Why (Rule 9): the difference between 'this metric is missing'
    (None) and 'this metric is zero' (0.0) is semantically critical.
    Coercing None → 0.0 corrupts every downstream computation."""
    assert _coerce_float(None) is None


def test_coerce_float_handles_strings() -> None:
    assert _coerce_float("3.14") == 3.14
    assert _coerce_float("not a number") is None


def test_coerce_int_handles_strings() -> None:
    assert _coerce_int("42") == 42
    assert _coerce_int(None) is None
    assert _coerce_int("nope") is None


def test_coerce_list_wraps_scalars() -> None:
    assert _coerce_list(None) == []
    assert _coerce_list([1, 2]) == [1, 2]
    assert _coerce_list("alone") == ["alone"]


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------


def test_task_from_dict_captures_extra() -> None:
    task = Task.from_dict({
        "task_id": "tsk_1",
        "status": "pending",
        "progress_percent": "50",  # str-coerced to int
        "novel_field": "kept",
    })
    assert task.progress_percent == 50
    assert task.extra == {"novel_field": "kept"}


# ---------------------------------------------------------------------------
# Fact
# ---------------------------------------------------------------------------


def test_fact_from_dict_minimal() -> None:
    fact = Fact.from_dict({"metric_key": "revenue", "value": 100})
    assert fact.metric_key == "revenue"
    assert fact.value == 100.0
    assert fact.confidence == 0.0


def test_fact_from_dict_missing_value_is_none() -> None:
    """Why (Rule 9): see _coerce_float test — this asserts the policy
    is plumbed through the Fact dataclass."""
    fact = Fact.from_dict({"metric_key": "x", "value": None})
    assert fact.value is None


def test_fact_extras_preserved() -> None:
    fact = Fact.from_dict({
        "metric_key": "revenue",
        "value": 1.0,
        "unit": "RMB",  # not declared on the dataclass
        "bbox": [1, 2, 3, 4],
    })
    assert fact.extra == {"unit": "RMB", "bbox": [1, 2, 3, 4]}


# ---------------------------------------------------------------------------
# ReportEnvelope
# ---------------------------------------------------------------------------


def test_report_envelope_unwraps_json_report() -> None:
    env = ReportEnvelope.from_legacy(
        "tsk_1",
        {
            "schema_version": "1.0",
            "json_report": {
                "company": {"ticker": "9988"},
                "facts": [{"metric_key": "revenue", "value": 1.0}],
                "validation": [],
            },
        },
    )
    assert env.task_id == "tsk_1"
    assert env.company == {"ticker": "9988"}
    assert len(env.facts) == 1


def test_report_envelope_handles_missing_keys() -> None:
    env = ReportEnvelope.from_legacy("tsk_1", {})
    assert env.facts == []
    assert env.company == {}
    assert env.schema_version == "1.0"


# ---------------------------------------------------------------------------
# Matrix
# ---------------------------------------------------------------------------


def test_matrix_from_dict() -> None:
    m = Matrix.from_dict({
        "schema_version": "1.0",
        "ticker": "9988",
        "periods": ["2024", "2025"],
        "metrics": [{"key": "revenue"}],
        "cells": [{"period": "2024", "metric_key": "revenue", "value": 100}],
        "audit_signature": "abc",
    })
    assert m.ticker == "9988"
    assert m.extra == {"audit_signature": "abc"}


# ---------------------------------------------------------------------------
# Layer 2 dataclasses
# ---------------------------------------------------------------------------


def test_signal_from_dict() -> None:
    s = Signal.from_dict({
        "signal_id": "sig_1",
        "signal_type": "margin_driver",
        "direction": "positive",
        "confidence": "0.9",
        "evidence": [{"page": 1}],
        "future_attr": True,
    })
    assert s.signal_id == "sig_1"
    assert s.confidence == 0.9
    assert s.evidence == [{"page": 1}]
    assert s.extra == {"future_attr": True}


def test_signal_envelope_count_fallback() -> None:
    """When the backend omits count, we compute it from signals."""
    env = SignalEnvelope.from_dict({"signals": [{"signal_id": "s1"}, {"signal_id": "s2"}]})
    assert env.count == 2


def test_supply_chain_node_from_dict() -> None:
    n = SupplyChainNode.from_dict({
        "edge_id": "e1",
        "node_role": "supplier",
        "node_label": "TSMC",
        "exposure_share": "0.12",
    })
    assert n.exposure_share == 0.12


def test_supply_chain_envelope_handles_alt_key() -> None:
    """Defensive: backend may send `nodes` or `supply_chain` as the array key."""
    env = SupplyChainEnvelope.from_dict({"nodes": [{"edge_id": "e1", "node_role": "supplier"}]})
    assert env.count == 1


def test_catalyst_from_dict() -> None:
    c = Catalyst.from_dict({
        "catalyst_id": "c1",
        "catalyst_type": "earnings",
        "direction": "positive",
        "expected_horizon": "next_quarter",
        "confidence": 0.8,
    })
    assert c.catalyst_id == "c1"
    assert c.expected_horizon == "next_quarter"


def test_catalyst_envelope_from_dict() -> None:
    env = CatalystEnvelope.from_dict({
        "task_id": "tsk_abc",
        "schema_version": "1.0",
        "count": 1,
        "catalysts": [{"catalyst_id": "c1", "catalyst_type": "earnings"}],
    })
    assert env.task_id == "tsk_abc"
    assert env.catalysts[0].catalyst_id == "c1"
