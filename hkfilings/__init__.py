"""HKFilings — Python client.

Turn Hong Kong listed-company annual / interim PDFs into source-traced
financial facts, industry signals and supply-chain graphs.

Public surface (everything you'll typically need):

    from hkfilings import HKFilingsClient

    client = HKFilingsClient(api_key="ak_...")
    task   = client.analyze(ticker="9988", year=2026)
    report = client.wait(task.task_id)

Get a free API key (20 tasks/month, no credit card) at
https://hkfilings.app/signup.
"""

from ._version import __version__
from .client import DEFAULT_BASE_URL, HKFilingsClient, HKFilingsError
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

__all__ = [
    "__version__",
    "DEFAULT_BASE_URL",
    "HKFilingsClient",
    "HKFilingsError",
    # Layer 1 types
    "Task",
    "Fact",
    "ReportEnvelope",
    "Matrix",
    # Layer 2 types
    "Signal",
    "SignalEnvelope",
    "SupplyChainNode",
    "SupplyChainEnvelope",
    "Catalyst",
    "CatalystEnvelope",
]
