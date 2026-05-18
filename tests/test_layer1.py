"""Layer 1 (financial facts) endpoint bindings.

We assert the exact HTTP shape (method, path, JSON body) the client
sends — these contracts are part of the public v1 surface and changing
them is a breaking change.
"""

from __future__ import annotations

import httpx
import pytest

from hkfilings import HKFilingsClient
from tests.conftest import TEST_BASE_URL


def test_create_task_posts_to_v1_hk_tasks(
    httpx_mock,  # type: ignore[no-untyped-def]
    client: HKFilingsClient,
) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{TEST_BASE_URL}/v1/hk-tasks",
        json={"task_id": "tsk_1", "status": "pending"},
    )
    task = client.create_task(pdf_url="https://x/report.pdf", ticker="9988")
    assert task.task_id == "tsk_1"
    assert task.status == "pending"

    req = httpx_mock.get_request()
    assert req.method == "POST"
    body = req.read()
    assert b'"pdf_url":"https://x/report.pdf"' in body
    assert b'"ticker":"9988"' in body
    assert b'"market":"HK"' in body


def test_analyze_posts_ticker_year_force(
    httpx_mock,
    client: HKFilingsClient,
) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{TEST_BASE_URL}/v1/hk-tasks/analyze",
        json={"task_id": "tsk_2", "status": "pending"},
    )
    client.analyze(ticker="9988", year=2026, force=True, language="en")

    req = httpx_mock.get_request()
    body = req.read()
    assert b'"ticker":"9988"' in body
    assert b'"year":2026' in body
    assert b'"force":true' in body
    assert b'"language":"en"' in body


def test_upload_sends_multipart(
    httpx_mock,
    client: HKFilingsClient,
    tmp_path,  # type: ignore[no-untyped-def]
) -> None:
    pdf = tmp_path / "report.pdf"
    pdf.write_bytes(b"%PDF-1.4\nstub\n")

    httpx_mock.add_response(
        method="POST",
        url=f"{TEST_BASE_URL}/v1/hk-tasks/upload",
        json={"task_id": "tsk_3", "status": "pending"},
    )
    task = client.upload(file_path=pdf, ticker="9988", company_name="Alibaba")
    assert task.task_id == "tsk_3"

    req = httpx_mock.get_request()
    ctype = req.headers["content-type"]
    assert ctype.startswith("multipart/form-data")
    raw = req.read()
    assert b"report.pdf" in raw
    assert b"9988" in raw
    assert b"Alibaba" in raw


def test_upload_raises_on_missing_file(
    client: HKFilingsClient,
    tmp_path,
) -> None:
    with pytest.raises(FileNotFoundError):
        client.upload(file_path=tmp_path / "nonexistent.pdf")


def test_task_status_get_path(
    httpx_mock,
    client: HKFilingsClient,
    task_pending_payload: dict,
) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{TEST_BASE_URL}/v1/hk-tasks/tsk_abc",
        json=task_pending_payload,
    )
    t = client.task_status("tsk_abc")
    assert t.status == "pending"
    assert t.progress_percent == 30


def test_result_unwraps_legacy_envelope(
    httpx_mock,
    client: HKFilingsClient,
    report_envelope_payload: dict,
) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{TEST_BASE_URL}/v1/hk-tasks/tsk_abc/result",
        json=report_envelope_payload,
    )
    env = client.result("tsk_abc")
    assert env.task_id == "tsk_abc"
    assert env.schema_version == "1.0"
    assert env.company["ticker"] == "9988"
    assert len(env.facts) == 2
    assert env.facts[0].value == 245_864_000_000.0
    assert env.facts[0].source_page == 87


def test_result_missing_value_stays_none(
    httpx_mock,
    client: HKFilingsClient,
    report_envelope_payload: dict,
) -> None:
    """Why (Rule 9): distinguishing 'missing' from 'zero' is core to the
    SDK's truthfulness — a regression to value=0.0 would silently corrupt
    every downstream calculation."""
    httpx_mock.add_response(
        method="GET",
        url=f"{TEST_BASE_URL}/v1/hk-tasks/tsk_abc/result",
        json=report_envelope_payload,
    )
    env = client.result("tsk_abc")
    missing = env.facts[1]
    assert missing.metric_key == "missing_value_metric"
    assert missing.value is None, "None must NOT be coerced to 0.0"


def test_unknown_fields_land_in_extra(
    httpx_mock,
    client: HKFilingsClient,
    report_envelope_payload: dict,
) -> None:
    """Why (Rule 9): v1 schema is frozen forward-compatible — when the
    backend ships new fields, the SDK must not crash and must preserve
    them under .extra so callers can opt in."""
    httpx_mock.add_response(
        method="GET",
        url=f"{TEST_BASE_URL}/v1/hk-tasks/tsk_abc/result",
        json=report_envelope_payload,
    )
    env = client.result("tsk_abc")
    assert env.facts[0].extra.get("new_field") == "future-compat"


def test_facts_csv_returns_bytes(
    httpx_mock,
    client: HKFilingsClient,
) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{TEST_BASE_URL}/v1/hk-tasks/tsk_abc/facts.csv",
        content=b"metric,value\nrevenue,245864000000\n",
    )
    out = client.facts_csv("tsk_abc")
    assert isinstance(out, bytes)
    assert b"revenue,245864000000" in out


def test_company_matrix_serializes_metrics_param(
    httpx_mock,
    client: HKFilingsClient,
    matrix_payload: dict,
) -> None:
    httpx_mock.add_response(
        method="GET",
        url=httpx.URL(
            f"{TEST_BASE_URL}/v1/hk-companies/9988/matrix",
            params={"metrics": "revenue,gross_profit"},
        ),
        json=matrix_payload,
    )
    m = client.company_matrix("9988", metrics=["revenue", "gross_profit"])
    assert m.ticker == "9988"
    assert len(m.cells) == 3
    assert m.periods == ["2024H1", "2025H1", "2026H1"]
    assert m.extra.get("audit_signature") == "deadbeef"


def test_wait_polls_then_returns_result(
    httpx_mock,
    monkeypatch: pytest.MonkeyPatch,
    client: HKFilingsClient,
    task_pending_payload: dict,
    task_completed_payload: dict,
    report_envelope_payload: dict,
) -> None:
    """Why (Rule 9): wait() must actually sleep between polls — a busy
    loop would burn the user's rate-limit quota in seconds. We monkeypatch
    time.sleep to prove the call happens (rather than waiting in real time)."""
    sleep_calls: list[float] = []
    monkeypatch.setattr("hkfilings.client.time.sleep", sleep_calls.append)

    httpx_mock.add_response(
        method="GET",
        url=f"{TEST_BASE_URL}/v1/hk-tasks/tsk_abc",
        json=task_pending_payload,
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{TEST_BASE_URL}/v1/hk-tasks/tsk_abc",
        json=task_completed_payload,
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{TEST_BASE_URL}/v1/hk-tasks/tsk_abc/result",
        json=report_envelope_payload,
    )

    env = client.wait("tsk_abc", timeout=60, poll_interval=0.5)
    assert env.task_id == "tsk_abc"
    assert sleep_calls == [0.5], "must sleep poll_interval between polls"


def test_wait_raises_on_failed_task(
    httpx_mock,
    monkeypatch: pytest.MonkeyPatch,
    client: HKFilingsClient,
) -> None:
    from hkfilings import HKFilingsError

    monkeypatch.setattr("hkfilings.client.time.sleep", lambda _: None)
    httpx_mock.add_response(
        method="GET",
        url=f"{TEST_BASE_URL}/v1/hk-tasks/tsk_abc",
        json={
            "task_id": "tsk_abc",
            "status": "failed",
            "error_message": "ocr_failed",
            "has_result": False,
            "has_pdf": True,
        },
    )
    with pytest.raises(HKFilingsError) as info:
        client.wait("tsk_abc", timeout=10, poll_interval=0.1)
    assert info.value.status_code == 409
    assert "ocr_failed" in str(info.value)


def test_wait_raises_on_timeout(
    httpx_mock,
    monkeypatch: pytest.MonkeyPatch,
    client: HKFilingsClient,
    task_pending_payload: dict,
) -> None:
    from hkfilings import HKFilingsError

    # Simulate time advancing past deadline on the second check.
    now = [1000.0]
    monkeypatch.setattr("hkfilings.client.time.time", lambda: now[0])
    monkeypatch.setattr(
        "hkfilings.client.time.sleep",
        lambda s: now.__setitem__(0, now[0] + 100),
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{TEST_BASE_URL}/v1/hk-tasks/tsk_abc",
        json=task_pending_payload,
        is_reusable=True,
    )
    with pytest.raises(HKFilingsError) as info:
        client.wait("tsk_abc", timeout=10, poll_interval=1.0)
    assert info.value.status_code == 408
