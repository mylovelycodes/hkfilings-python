"""Constructor wiring — env vars, header injection, base_url normalization."""

from __future__ import annotations

import pytest

from hkfilings import DEFAULT_BASE_URL, HKFilingsClient


def test_base_url_default_is_managed_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    """Why: SDK users who just `pip install` should hit the managed API,
    not localhost. A regression here means everyone gets a connection error
    on first use."""
    monkeypatch.delenv("HKFILINGS_BASE_URL", raising=False)
    monkeypatch.delenv("HKFILINGS_API_KEY", raising=False)
    c = HKFilingsClient(api_key="ak_x")
    assert c.base_url == DEFAULT_BASE_URL
    assert c.base_url.startswith("https://"), "production endpoint must be HTTPS"
    c.close()


def test_base_url_trailing_slash_stripped() -> None:
    """Why: httpx joins paths with the base; double slashes break routes."""
    c = HKFilingsClient(base_url="https://api.test.invalid/", api_key="ak_x")
    assert c.base_url == "https://api.test.invalid"
    c.close()


def test_env_vars_used_when_args_omitted(monkeypatch: pytest.MonkeyPatch) -> None:
    """Why: 12-factor-style config is the path of least friction for
    notebooks and CI. The env vars are documented in the README."""
    monkeypatch.setenv("HKFILINGS_BASE_URL", "https://env.test.invalid")
    monkeypatch.setenv("HKFILINGS_API_KEY", "ak_from_env")
    c = HKFilingsClient()
    assert c.base_url == "https://env.test.invalid"
    assert c._client.headers["x-api-key"] == "ak_from_env"
    c.close()


def test_explicit_args_win_over_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HKFILINGS_BASE_URL", "https://env.invalid")
    monkeypatch.setenv("HKFILINGS_API_KEY", "ak_env")
    c = HKFilingsClient(base_url="https://explicit.invalid", api_key="ak_explicit")
    assert c.base_url == "https://explicit.invalid"
    assert c._client.headers["x-api-key"] == "ak_explicit"
    c.close()


def test_api_key_sets_x_api_key_header() -> None:
    c = HKFilingsClient(base_url="https://api.test.invalid", api_key="ak_xyz")
    assert c._client.headers["x-api-key"] == "ak_xyz"
    c.close()


def test_user_agent_includes_version() -> None:
    """Why: identifies SDK traffic in backend logs for triage."""
    from hkfilings import __version__

    c = HKFilingsClient(base_url="https://api.test.invalid", api_key="ak_x")
    ua = c._client.headers["user-agent"]
    assert "hkfilings-python" in ua
    assert __version__ in ua
    c.close()


def test_user_agent_override() -> None:
    c = HKFilingsClient(
        base_url="https://api.test.invalid",
        api_key="ak_x",
        user_agent="my-product/1.0",
    )
    assert c._client.headers["user-agent"] == "my-product/1.0"
    c.close()


def test_context_manager_closes_underlying_client() -> None:
    """Why: leaked httpx clients hold sockets; matters in long-running jobs."""
    with HKFilingsClient(base_url="https://api.test.invalid", api_key="ak_x") as c:
        underlying = c._client
        assert not underlying.is_closed
    assert underlying.is_closed
