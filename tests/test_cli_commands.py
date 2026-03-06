from edgebench.cli import build_parser


def test_cli_parser_supports_benchmark_command():
    parser = build_parser()
    args = parser.parse_args(
        [
            "benchmark",
            "--models",
            "config/models.yaml",
            "--dataset",
            "data/s.jsonl",
            "--job-timeout-seconds",
            "60",
            "--scorer",
            "field_level",
        ]
    )
    assert args.command == "benchmark"
    assert args.job_timeout_seconds == 60
    assert args.scorer == "field_level"


def test_cli_parser_supports_report_command():
    parser = build_parser()
    args = parser.parse_args(["report", "--results", "results/x", "--out", "report/report.md"])
    assert args.command == "report"


def test_cli_parser_supports_doctor_command():
    parser = build_parser()
    args = parser.parse_args(["doctor", "--dataset", "data/smoke_prompts_10.jsonl"])
    assert args.command == "doctor"
