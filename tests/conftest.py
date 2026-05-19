"""Shared pytest fixtures for the hkfilings test suite.

We mock at the HTTP boundary with pytest-httpx — never at the client
class internals. This keeps tests close to what the real API contract
looks like and immediately catches accidental URL / method changes.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from hkfilings import HKFilingsClient

TEST_BASE_URL = "https://api.test.invalid"


@pytest.fixture
def api_key() -> str:
    return "ak_test_unit_suite"


@pytest.fixture
def client(api_key: str) -> Iterator[HKFilingsClient]:
    c = HKFilingsClient(base_url=TEST_BASE_URL, api_key=api_key)
    try:
        yield c
    finally:
        c.close()


@pytest.fixture
def task_completed_payload() -> dict:
    return {
        "task_id": "tsk_abc",
        "status": "completed",
        "progress_percent": 100,
        "progress_stage": "done",
        "has_result": True,
        "has_pdf": True,
        "review_status": "approved",
        "future_field": "ok",  # forward-compat
    }


@pytest.fixture
def task_pending_payload() -> dict:
    return {
        "task_id": "tsk_abc",
        "status": "pending",
        "progress_percent": 30,
        "progress_stage": "parsing",
        "has_result": False,
        "has_pdf": True,
    }


@pytest.fixture
def report_envelope_payload() -> dict:
    return {
        "schema_version": "1.0",
        "json_report": {
            "company": {"ticker": "9988", "name": "Alibaba"},
            "facts": [
                {
                    "metric_key": "revenue",
                    "metric_label": "Revenue",
                    "value": 245_864_000_000.0,
                    "comparable_value": 224_500_000_000.0,
                    "yoy_change": 0.0952,
                    "source_page": 87,
                    "source_text": "Revenue for the year increased…",
                    "confidence": 0.98,
                    "new_field": "future-compat",
                },
                {
                    "metric_key": "missing_value_metric",
                    "value": None,  # critical: must distinguish None from 0.0
                    "confidence": 0.5,
                },
            ],
            "validation": [{"rule": "yoy_recalc", "passed": True}],
        },
    }


@pytest.fixture
def signal_envelope_payload() -> dict:
    return {
        "task_id": "tsk_abc",
        "schema_version": "1.0",
        "count": 1,
        "signals": [
            {
                "signal_id": "sig_001",
                "task_id": "tsk_abc",
                "ticker": "9988",
                "signal_type": "margin_driver",
                "direction": "positive",
                "strength": "medium",
                "time_horizon": "next_quarter",
                "summary": "Cloud margin improved as AI workload monetization scaled.",
                "rationale": "Mgmt called out unit economics.",
                "affected_segments": ["cloud"],
                "upstream_entities": [],
                "downstream_entities": [],
                "industry_tags": ["cloud", "ai"],
                "financial_metrics_linked": ["gross_margin"],
                "linked_fact_ids": ["fact_42"],
                "evidence": [{"page": 87, "text": "Cloud gross margin..."}],
                "confidence": 0.91,
                "review_status": "approved",
                "novel_field": "preserved",
            }
        ],
    }


@pytest.fixture
def supply_chain_payload() -> dict:
    return {
        "task_id": "tsk_abc",
        "schema_version": "1.0",
        "count": 1,
        "supply_chain": [
            {
                "edge_id": "edge_001",
                "task_id": "tsk_abc",
                "ticker": "9988",
                "node_role": "supplier",
                "node_type": "company",
                "node_label": "TSMC",
                "linked_segments": ["cloud"],
                "exposure_share": 0.12,
                "direction_to_company": "upstream",
                "evidence_page": 145,
                "evidence_text": "...",
                "confidence": 0.88,
                "review_status": "approved",
            }
        ],
    }


@pytest.fixture
def catalyst_payload() -> dict:
    return {
        "task_id": "tsk_abc",
        "schema_version": "1.0",
        "count": 1,
        "catalysts": [
            {
                "catalyst_id": "cat_001",
                "task_id": "tsk_abc",
                "ticker": "9988",
                "catalyst_type": "earnings",
                "direction": "positive",
                "expected_horizon": "next_quarter",
                "summary": "Q2 cloud guidance likely upgraded.",
                "evidence_page": 12,
                "evidence_text": "Management raised outlook…",
                "confidence": 0.81,
                "review_status": "approved",
            }
        ],
    }


@pytest.fixture
def matrix_payload() -> dict:
    return {
        "schema_version": "1.0",
        "ticker": "9988",
        "periods": ["2024H1", "2025H1", "2026H1"],
        "metrics": [{"key": "revenue", "label": "Revenue"}],
        "cells": [
            {"period": "2024H1", "metric_key": "revenue", "value": 200},
            {"period": "2025H1", "metric_key": "revenue", "value": 224},
            {"period": "2026H1", "metric_key": "revenue", "value": 245},
        ],
        "audit_signature": "deadbeef",  # forward-compat
    }
