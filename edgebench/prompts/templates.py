from __future__ import annotations

import json
from typing import Any

STRICT_SYSTEM_PROMPT = """
You are a JSON-only engine.
Return ONLY valid JSON that conforms exactly to the provided JSON Schema.
Do not include Markdown, code fences, explanation text, or extra keys.
If you are unsure, output the best possible schema-valid JSON.
""".strip()


def build_structured_prompt(user_prompt: str, schema: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": STRICT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "JSON Schema:\n"
                f"{json.dumps(schema, indent=2, ensure_ascii=False)}\n\n"
                "Task:\n"
                f"{user_prompt}\n\n"
                "Output requirements:\n"
                "1) Return ONLY JSON.\n"
                "2) Must conform exactly to the schema.\n"
                "3) No additional keys."
            ),
        },
    ]


def build_repair_prompt(
    original_prompt: str,
    invalid_output: str,
    validation_errors: list[dict[str, Any]],
    schema: dict[str, Any],
) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": STRICT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "The previous response was invalid. Repair it.\n\n"
                "Original user prompt:\n"
                f"{original_prompt}\n\n"
                "Invalid model output:\n"
                f"{invalid_output}\n\n"
                "Validation errors:\n"
                f"{json.dumps(validation_errors, indent=2, ensure_ascii=False)}\n\n"
                "JSON Schema:\n"
                f"{json.dumps(schema, indent=2, ensure_ascii=False)}\n\n"
                "Return ONLY corrected JSON that strictly conforms to the schema."
            ),
        },
    ]
