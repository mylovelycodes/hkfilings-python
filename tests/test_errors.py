"""Error propagation — HKFilingsError must expose status + payload."""

from __future__ import annotations

import pytest

from hkfilings import HKFilingsClient, HKFilingsError
from tests.conftest import TEST_BASE_URL


def test_4xx_raises_with_status_and_payload(
    httpx_mock,
    client: HKFilingsClient,
) -> None:
    """Why: callers branch on status_code (e.g. 429 → upgrade prompt,
    402 → demo-tier upsell). Hiding the code in a stringified message
    would force fragile string parsing."""
    httpx_mock.add_response(
        method="POST",
        url=f"{TEST_BASE_URL}/v1/hk-tasks/analyze",
        status_code=429,
        json={"detail": "rate_limited", "upgrade_url": "https://hkfilings.app/pricing"},
    )
    with pytest.raises(HKFilingsError) as info:
        client.analyze(ticker="9988", year=2026)
    assert info.value.status_code == 429
    assert "rate_limited" in str(info.value)
    assert info.value.payload["upgrade_url"] == "https://hkfilings.app/pricing"


def test_5xx_with_non_json_body(
    httpx_mock,
    client: HKFilingsClient,
) -> None:
    """Why: backend can return an HTML error page from a reverse proxy.
    Client must not crash trying to parse it as JSON."""
    httpx_mock.add_response(
        method="GET",
        url=f"{TEST_BASE_URL}/v1/hk-tasks/tsk_abc",
        status_code=502,
        text="<html>Bad gateway</html>",
    )
    with pytest.raises(HKFilingsError) as info:
        client.task_status("tsk_abc")
    assert info.value.status_code == 502
    assert info.value.payload == {}


def test_2xx_does_not_raise(
    httpx_mock,
    client: HKFilingsClient,
) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{TEST_BASE_URL}/v1/hk-tasks/tsk_abc",
        json={"task_id": "tsk_abc", "status": "pending"},
    )
    # Should NOT raise.
    client.task_status("tsk_abc")


def test_404_detail_propagates_in_message(
    httpx_mock,
    client: HKFilingsClient,
) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{TEST_BASE_URL}/v1/hk-tasks/missing",
        status_code=404,
        json={"detail": "task not found"},
    )
    with pytest.raises(HKFilingsError) as info:
        client.task_status("missing")
    assert info.value.status_code == 404
    assert "task not found" in str(info.value)
