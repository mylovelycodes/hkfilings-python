"""01 — Quickstart: analyze one report, print every fact.

Reads the API key from the HKFILINGS_API_KEY environment variable. Get a free
key (20 tasks/month, no credit card) at https://hkfilings.app/signup.

Run:
    export HKFILINGS_API_KEY=ak_test_...
    python examples/01_quickstart.py
"""

from __future__ import annotations

import os
import sys

from hkfilings import HKFilingsClient, HKFilingsError


def main() -> int:
    if not os.environ.get("HKFILINGS_API_KEY"):
        print("Set HKFILINGS_API_KEY first — get a key at https://hkfilings.app/signup")
        return 2

    client = HKFilingsClient()  # reads HKFILINGS_API_KEY automatically

    print("Submitting task for 9988 (Alibaba) FY2026 interim report...")
    try:
        task = client.analyze(ticker="9988", year=2026)
    except HKFilingsError as e:
        print(f"API error {e.status_code}: {e}")
        return 1

    print(f"  task_id = {task.task_id}")
    print("  waiting for completion (this can take a couple of minutes)...")

    report = client.wait(task.task_id, timeout=600)
    print(f"  ok — got {len(report.facts)} facts under schema {report.schema_version}\n")

    width = max((len(f.metric_key) for f in report.facts), default=20)
    for f in sorted(report.facts, key=lambda x: x.metric_key):
        value = "—" if f.value is None else f"{f.value:,.0f}"
        page = "—" if f.source_page is None else f"p.{f.source_page}"
        print(f"  {f.metric_key:<{width}}  {value:>20}  {page:>6}  conf={f.confidence:.2f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
