# Report Generation

Generate a technical report from measured artifacts only:

```powershell
python report/generate_report.py --results results/<run_id> --out report/report.md
```

Or via CLI:

```powershell
python -m edgebench.cli report --results results/<run_id> --out report/report.md
```

The report reads `summary.json` + `results.jsonl`. No benchmark numbers are hardcoded.
