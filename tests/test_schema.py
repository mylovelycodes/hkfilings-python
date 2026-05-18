"""Schema introspection — fetches the four frozen v1 JSON Schema docs."""

from __future__ import annotations

import pytest

from hkfilings import HKFilingsClient
from tests.conftest import TEST_BASE_URL


@pytest.mark.parametrize(
    "name",
    ["financial_fact", "industry_signal", "supply_chain_node", "catalyst"],
)
def test_schema_fetches_each_valid_name(
    httpx_mock,
    client: HKFilingsClient,
    name: str,
) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{TEST_BASE_URL}/v1/schema/{name}",
        json={"$schema": "https://json-schema.org/draft/2020-12/schema", "title": name},
    )
    out = client.schema(name=name)
    assert out["title"] == name


def test_schema_default_is_financial_fact(
    httpx_mock,
    client: HKFilingsClient,
) -> None:
    """Why: backward-compat — the v0 SDK shipped `schema()` with no args
    returning the financial_fact schema. Existing callers must keep working."""
    httpx_mock.add_response(
        method="GET",
        url=f"{TEST_BASE_URL}/v1/schema/financial_fact",
        json={"title": "financial_fact"},
    )
    out = client.schema()
    assert out["title"] == "financial_fact"


def test_schema_rejects_unknown_name(client: HKFilingsClient) -> None:
    """Why: catches typos client-side before a wasted HTTP roundtrip."""
    with pytest.raises(ValueError, match="must be one of"):
        client.schema(name="not_a_schema")
