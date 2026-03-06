from __future__ import annotations

import argparse

from edgebench.report.generator import write_report

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate markdown report from benchmark artifacts")
    parser.add_argument("--results", required=True, help="Path to results/<run_id>")
    parser.add_argument("--out", default="report/report.md")
    parser.add_argument("--template-dir", default="report")
    args = parser.parse_args()

    write_report(results_dir=args.results, out_path=args.out, template_dir=args.template_dir)
    print(f"Wrote report: {args.out}")
