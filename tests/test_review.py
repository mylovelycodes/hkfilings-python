"""Review endpoints: diff, patch_fact, fact_comment."""

from __future__ import annotations

import httpx

from hkfilings import HKFilingsClient
from tests.conftest import TEST_BASE_URL


def test_review_diff_with_version_params(
    httpx_mock,
    client: HKFilingsClient,
) -> None:
    httpx_mock.add_response(
        method="GET",
        url=httpx.URL(
            f"{TEST_BASE_URL}/v1/hk-tasks/tsk_abc/review/diff",
            params={"from_version": 1, "to_version": 3},
        ),
        json={"changes": []},
    )
    out = client.review_diff("tsk_abc", from_version=1, to_version=3)
    assert out == {"changes": []}


def test_review_diff_omits_none_versions(
    httpx_mock,
    client: HKFilingsClient,
) -> None:
    """Why: if the client forwards `None` it pollutes query strings as
    `from_version=None`, which the backend would reject as a bad int."""
    httpx_mock.add_response(
        method="GET",
        url=f"{TEST_BASE_URL}/v1/hk-tasks/tsk_abc/review/diff",
        json={"changes": []},
    )
    client.review_diff("tsk_abc")  # no version args
    req = httpx_mock.get_request()
    assert "from_version" not in str(req.url)
    assert "to_version" not in str(req.url)


def test_patch_fact_forwards_kwargs_as_json(
    httpx_mock,
    client: HKFilingsClient,
) -> None:
    httpx_mock.add_response(
        method="PATCH",
        url=f"{TEST_BASE_URL}/v1/hk-facts/fact_42",
        json={"fact_id": "fact_42", "review_status": "approved"},
    )
    result = client.patch_fact("fact_42", review_status="approved", value=200.0)
    assert result["fact_id"] == "fact_42"

    req = httpx_mock.get_request()
    body = req.read()
    assert b'"review_status":"approved"' in body
    assert b'"value":200.0' in body


def test_fact_comment_posts_body_and_author(
    httpx_mock,
    client: HKFilingsClient,
) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{TEST_BASE_URL}/v1/hk-facts/fact_42/comments",
        json={"id": "c_1"},
    )
    client.fact_comment("fact_42", body="check page 87", author="alice@example.com")
    req = httpx_mock.get_request()
    body = req.read()
    assert b'"body":"check page 87"' in body
    assert b'"author":"alice@example.com"' in body
