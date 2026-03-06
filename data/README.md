# Data Directory

- `generate_synthetic_prompts.py` creates a placeholder 3250-prompt dataset.
- `smoke_prompts_10.jsonl` is a tiny local smoke-test dataset.
- Do not commit private production datasets.

Expected JSONL format:

```json
{"id":"p1","prompt":"...","category":"...","expected":{"answer":"..."}}
```

`expected` is optional and enables offline grading.
