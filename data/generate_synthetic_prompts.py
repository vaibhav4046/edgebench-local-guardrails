from __future__ import annotations

import argparse
import json
from pathlib import Path


def generate(out_path: str, count: int) -> None:
    categories = ["summarization", "classification", "extraction", "reasoning", "qa"]
    target = Path(out_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    with target.open("w", encoding="utf-8") as handle:
        for i in range(count):
            category = categories[i % len(categories)]
            prompt = {
                "id": f"synthetic-{i+1:05d}",
                "prompt": (
                    f"[{category}] Placeholder benchmark prompt {i+1}. "
                    "Produce a concise response using strict JSON output requirements."
                ),
                "category": category,
            }
            handle.write(json.dumps(prompt, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate placeholder synthetic JSONL prompts")
    parser.add_argument("--out", default="data/synthetic_prompts_3250.jsonl")
    parser.add_argument("--count", type=int, default=3250)
    args = parser.parse_args()
    generate(args.out, args.count)
    print(f"Wrote {args.count} prompts to {args.out}")
