"""Layer 2 (signals / supply-chain / catalysts / intelligence-brief) endpoints."""

from __future__ import annotations

import httpx

from hkfilings import HKFilingsClient
from tests.conftest import TEST_BASE_URL


def test_task_signals_path_and_filters(
    httpx_mock,
    client: HKFilingsClient,
    signal_envelope_payload: dict,
) -> None:
    httpx_mock.add_response(
        method="GET",
        url=httpx.URL(
            f"{TEST_BASE_URL}/v1/hk-tasks/tsk_abc/signals",
            params={"signal_type": "margin_driver"},
        ),
        json=signal_envelope_payload,
    )
    env = client.task_signals("tsk_abc", signal_type="margin_driver")
    assert env.count == 1
    assert env.signals[0].signal_id == "sig_001"
    assert env.signals[0].signal_type == "margin_driver"
    assert env.signals[0].evidence[0]["page"] == 87
    assert env.signals[0].extra.get("novel_field") == "preserved"


def test_company_signals_default_review_filter(
    httpx_mock,
    client: HKFilingsClient,
    signal_envelope_payload: dict,
) -> None:
    """Why: the SDK default mirrors the backend default (approved+auto_passed)
    so that customers calling the public method never accidentally surface
    pending or rejected rows to end-users."""
    httpx_mock.add_response(
        method="GET",
        url=httpx.URL(
            f"{TEST_BASE_URL}/v1/hk-companies/9988/signals",
            params={"review_status": "approved,auto_passed"},
        ),
        json=signal_envelope_payload,
    )
    env = client.company_signals("9988")
    assert env.signals[0].review_status == "approved"


def test_task_supply_chain(
    httpx_mock,
    client: HKFilingsClient,
    supply_chain_payload: dict,
) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{TEST_BASE_URL}/v1/hk-tasks/tsk_abc/supply-chain",
        json=supply_chain_payload,
    )
    env = client.task_supply_chain("tsk_abc")
    assert env.count == 1
    node = env.nodes[0]
    assert node.edge_id == "edge_001"
    assert node.node_role == "supplier"
    assert node.node_label == "TSMC"
    assert node.exposure_share == 0.12


def test_company_supply_chain(
    httpx_mock,
    client: HKFilingsClient,
    supply_chain_payload: dict,
) -> None:
    httpx_mock.add_response(
        method="GET",
        url=httpx.URL(
            f"{TEST_BASE_URL}/v1/hk-companies/9988/supply-chain",
            params={"review_status": "approved,auto_passed"},
        ),
        json=supply_chain_payload,
    )
    env = client.company_supply_chain("9988")
    assert len(env.nodes) == 1


def test_task_catalysts(
    httpx_mock,
    client: HKFilingsClient,
    catalyst_payload: dict,
) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{TEST_BASE_URL}/v1/hk-tasks/tsk_abc/catalysts",
        json=catalyst_payload,
    )
    env = client.task_catalysts("tsk_abc")
    assert env.count == 1
    cat = env.catalysts[0]
    assert cat.catalyst_id == "cat_001"
    assert cat.direction == "positive"
    assert cat.expected_horizon == "next_quarter"


def test_company_catalysts(
    httpx_mock,
    client: HKFilingsClient,
    catalyst_payload: dict,
) -> None:
    httpx_mock.add_response(
        method="GET",
        url=httpx.URL(
            f"{TEST_BASE_URL}/v1/hk-companies/9988/catalysts",
            params={"review_status": "approved,auto_passed"},
        ),
        json=catalyst_payload,
    )
    env = client.company_catalysts("9988")
    assert env.catalysts[0].catalyst_type == "earnings"


def test_intelligence_brief_returns_raw_dict(
    httpx_mock,
    client: HKFilingsClient,
) -> None:
    payload = {
        "task_id": "tsk_abc",
        "intelligence_brief": {
            "summary": "Margins expanded across cloud.",
            "key_insights": ["AI workloads", "Capex discipline"],
        },
    }
    httpx_mock.add_response(
        method="GET",
        url=f"{TEST_BASE_URL}/v1/hk-tasks/tsk_abc/intelligence-brief",
        json=payload,
    )
    out = client.intelligence_brief("tsk_abc")
    assert out == payload
    assert out["intelligence_brief"]["summary"] == "Margins expanded across cloud."


def test_patch_signal(
    httpx_mock,
    client: HKFilingsClient,
) -> None:
    httpx_mock.add_response(
        method="PATCH",
        url=f"{TEST_BASE_URL}/v1/hk-signals/sig_001",
        json={"signal_id": "sig_001", "review_status": "approved"},
    )
    result = client.patch_signal("sig_001", review_status="approved", summary="ok")
    assert result["review_status"] == "approved"

    req = httpx_mock.get_request()
    body = req.read()
    assert b'"review_status":"approved"' in body
    assert b'"summary":"ok"' in body
