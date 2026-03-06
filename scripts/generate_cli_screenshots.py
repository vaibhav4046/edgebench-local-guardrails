from __future__ import annotations

import json
import subprocess
from collections.abc import Iterable
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SCREEN_DIR = ROOT / "docs" / "screenshots"


def _font() -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/consola.ttf"),
        Path("C:/Windows/Fonts/consolab.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), 18)
    return ImageFont.load_default()


def _run_command(args: list[str]) -> str:
    completed = subprocess.run(
        args,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    out = completed.stdout.strip()
    err = completed.stderr.strip()
    if err:
        return f"{out}\n{err}".strip()
    return out


def _render_terminal(path: Path, lines: Iterable[str], title: str) -> None:
    font = _font()
    lines_list = list(lines)
    if not lines_list:
        lines_list = [""]

    # Compute text block size.
    dummy = Image.new("RGB", (10, 10))
    draw = ImageDraw.Draw(dummy)
    line_height = int(draw.textbbox((0, 0), "Ag", font=font)[3] * 1.45)
    max_width = 0
    for line in lines_list:
        width = int(draw.textbbox((0, 0), line, font=font)[2])
        if width > max_width:
            max_width = width

    pad_x = 24
    pad_y = 22
    top_bar = 44
    width = min(max(900, max_width + pad_x * 2), 1800)
    height = top_bar + pad_y * 2 + line_height * len(lines_list)

    img = Image.new("RGB", (width, height), (20, 23, 28))
    draw = ImageDraw.Draw(img)

    # Top bar.
    draw.rectangle((0, 0, width, top_bar), fill=(33, 38, 45))
    draw.text((14, 10), title, fill=(229, 231, 235), font=font)
    draw.ellipse((width - 70, 14, width - 58, 26), fill=(244, 63, 94))
    draw.ellipse((width - 50, 14, width - 38, 26), fill=(250, 204, 21))
    draw.ellipse((width - 30, 14, width - 18, 26), fill=(74, 222, 128))

    y = top_bar + pad_y
    for line in lines_list:
        draw.text((pad_x, y), line, fill=(167, 243, 208), font=font)
        y += line_height

    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def _doctor_lines() -> list[str]:
    cmd = [
        str(ROOT / ".venv" / "Scripts" / "python.exe"),
        "-m",
        "edgebench.cli",
        "doctor",
        "--dataset",
        "data/smoke_prompts_10.jsonl",
    ]
    output = _run_command(cmd)
    return [
        r"PS C:\Users\lalwa\Downloads\edgebench-local-guardrails> python -m edgebench.cli doctor --dataset data/smoke_prompts_10.jsonl",
        *output.splitlines(),
    ]


def _latest_run_id() -> str:
    latest = ROOT / "results" / "latest" / "summary.json"
    if latest.exists():
        payload = json.loads(latest.read_text(encoding="utf-8"))
        run_id = payload.get("run_id")
        if isinstance(run_id, str) and run_id:
            return run_id

    candidates = sorted((ROOT / "results").glob("*/summary.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError("No results summary.json files found")
    payload = json.loads(candidates[0].read_text(encoding="utf-8"))
    run_id = payload.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        raise ValueError("Latest summary.json is missing run_id")
    return run_id


def _benchmark_lines() -> list[str]:
    run_id = _latest_run_id()
    summary_path = ROOT / "results" / run_id / "summary.json"
    records_path = ROOT / "results" / run_id / "results.jsonl"

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    first_record = json.loads(records_path.read_text(encoding="utf-8").splitlines()[0])
    return [
        rf"PS C:\Users\lalwa\Downloads\edgebench-local-guardrails> python -m edgebench.cli benchmark --run-id {run_id}",
        f"run_id: {summary['run_id']}",
        f"total_records: {summary['total_records']}",
        f"success_count: {summary['success_count']}",
        f"failure_count: {summary['failure_count']}",
        f"error_type_counts: {summary['error_type_counts']}",
        f"first_failure: {first_record['validation_errors'][0]['msg']}",
    ]


def _report_lines() -> list[str]:
    report_path = ROOT / "report" / "report.md"
    raw = report_path.read_text(encoding="utf-8").splitlines()
    clipped = raw[:18]
    return [
        r"PS C:\Users\lalwa\Downloads\edgebench-local-guardrails> python -m edgebench.cli report --results results/latest --out report/report.md",
        *clipped,
    ]


def main() -> None:
    _render_terminal(SCREEN_DIR / "cli_doctor.png", _doctor_lines(), "CLI Doctor Check")
    _render_terminal(SCREEN_DIR / "cli_benchmark.png", _benchmark_lines(), "CLI Benchmark Run")
    _render_terminal(SCREEN_DIR / "cli_report.png", _report_lines(), "CLI Report Generation")
    print(f"Wrote screenshots to {SCREEN_DIR}")


if __name__ == "__main__":
    main()
