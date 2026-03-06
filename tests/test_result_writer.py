from pathlib import Path

from edgebench.runner.result_writer import ResultWriter


def test_result_writer_writes_files(tmp_path: Path):
    writer = ResultWriter(run_dir=tmp_path / "run")
    writer.write_record(
        {
            "prompt_id": "p1",
            "model_key": "m",
            "model_tag": "m:tag",
            "temperature": 0.2,
            "repeat_index": 0,
            "success": True,
            "failure_type": None,
            "metrics": {"ttft_seconds": 0.1},
        }
    )
    writer.write_summary({"ok": True})

    assert (tmp_path / "run" / "results.jsonl").exists()
    assert (tmp_path / "run" / "summary.json").exists()
    assert (tmp_path / "run" / "metrics.csv").exists()
