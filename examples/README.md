# Examples

Runnable Python scripts that demonstrate the SDK. Pick your scenario:

| File | What it shows | Plan tier needed |
| ---- | ------------- | ---------------- |
| [`01_quickstart.py`](01_quickstart.py) | The 5-line "analyze a report and print facts" path | Free |
| [`02_compare_gross_margin_baba_vs_tencent.py`](02_compare_gross_margin_baba_vs_tencent.py) | Cross-company / cross-period comparison with pandas | Free (2 tasks total) |
| [`03_signals_and_supply_chain.py`](03_signals_and_supply_chain.py) | Layer-2: industry signals + supply-chain graph | Pro (Layer-2 access) |

Each script is self-contained and can be run directly:

```bash
export HKFILINGS_API_KEY=ak_test_your_key_here
python examples/01_quickstart.py
```

Get a free key (20 tasks/month, no credit card) at
https://hkfilings.app/signup.

## Notebooks

Jupyter notebooks live in [docs.hkfilings.app](https://docs.hkfilings.app/python/notebooks)
where they render with output. For local Jupyter use, install `jupytext`
and convert any of these scripts:

```bash
pip install jupytext jupyter
jupytext --to ipynb examples/01_quickstart.py
jupyter notebook examples/01_quickstart.ipynb
```
