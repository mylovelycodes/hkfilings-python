"""03 — Layer 2: industry signals + supply-chain graph.

Demonstrates the post-Layer-1 enrichments that are unique to this API:
- Industry signals (margin drivers, segment growth, upstream cost, etc.)
  each bound to evidence in the report
- Supply-chain nodes (suppliers / customers / competitors / regulators)
  with exposure share

Requires Pro or higher (Layer-2 is gated on Free).

Run:
    export HKFILINGS_API_KEY=ak_pro_...
    python examples/03_signals_and_supply_chain.py
"""

from __future__ import annotations

import os
import sys

from hkfilings import HKFilingsClient


def main() -> int:
    if not os.environ.get("HKFILINGS_API_KEY"):
        print("Set HKFILINGS_API_KEY first — get a key at https://hkfilings.app/signup")
        return 2

    client = HKFilingsClient()
    ticker = "9988"  # Alibaba

    print(f"\n=== Industry signals for {ticker} (approved + auto-passed) ===\n")
    sigs = client.company_signals(ticker)
    if sigs.count == 0:
        print("  (no signals — try a Pro key with Layer-2 access)")
    for s in sigs.signals[:10]:
        arrow = {"positive": "↑", "negative": "↓", "neutral": "→"}.get(s.direction or "", "•")
        print(f"  {arrow} [{s.signal_type:<18}] {s.summary or '—'}")
        if s.evidence:
            ev = s.evidence[0]
            page = ev.get("page", "?")
            text = (ev.get("text") or "")[:80]
            print(f"      └─ p.{page} — {text}…")

    print(f"\n=== Supply-chain nodes for {ticker} ===\n")
    sc = client.company_supply_chain(ticker)
    if sc.count == 0:
        print("  (no supply-chain data)")
    for n in sc.nodes[:20]:
        share = "" if n.exposure_share is None else f"  ({n.exposure_share:.1%})"
        print(f"  [{n.node_role:<10}] {n.node_label}{share}")

    print(f"\n=== Forward-looking catalysts for {ticker} ===\n")
    cats = client.company_catalysts(ticker)
    if cats.count == 0:
        print("  (no catalysts)")
    for c in cats.catalysts[:10]:
        arrow = {"positive": "↑", "negative": "↓"}.get(c.direction or "", "•")
        print(f"  {arrow} [{c.catalyst_type}, {c.expected_horizon}] {c.summary or '—'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
