"""02 — Compare gross margin: Alibaba (9988) vs Tencent (0700) across periods.

Uses ``company_matrix`` to pull the cross-period grid for two tickers in
two HTTP calls (not one call per report) — fast and free-tier friendly.

Run:
    pip install pandas
    export HKFILINGS_API_KEY=ak_test_...
    python examples/02_compare_gross_margin_baba_vs_tencent.py
"""

from __future__ import annotations

import os
import sys

try:
    import pandas as pd
except ImportError:
    print("This example needs pandas:  pip install pandas")
    sys.exit(2)

from hkfilings import HKFilingsClient


def main() -> int:
    if not os.environ.get("HKFILINGS_API_KEY"):
        print("Set HKFILINGS_API_KEY first — get a key at https://hkfilings.app/signup")
        return 2

    client = HKFilingsClient()
    tickers = ["9988", "0700"]  # Alibaba, Tencent
    metrics = ["revenue", "gross_profit"]

    rows = []
    for tk in tickers:
        matrix = client.company_matrix(tk, metrics=metrics)
        rows.extend({"ticker": tk, **cell} for cell in matrix.cells)

    if not rows:
        print("No data — make sure you have at least one completed task per ticker.")
        return 1

    df = pd.DataFrame(rows)

    wide = df.pivot_table(
        index="period",
        columns=["ticker", "metric_key"],
        values="value",
        aggfunc="first",
    ).sort_index()

    for tk in tickers:
        wide[(tk, "gross_margin")] = (
            wide[(tk, "gross_profit")] / wide[(tk, "revenue")]
        )

    margin_cols = [(tk, "gross_margin") for tk in tickers]
    print("\nGross margin by period:")
    print(wide[margin_cols].dropna(how="all").to_string(float_format=lambda v: f"{v:.2%}"))

    return 0


if __name__ == "__main__":
    sys.exit(main())
