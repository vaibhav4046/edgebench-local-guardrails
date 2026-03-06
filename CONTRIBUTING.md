# Contributing

## Development workflow
1. Create a virtual environment and install `requirements-dev.txt`.
2. Run tests with `pytest` before opening a PR.
3. Keep changes offline-safe and avoid introducing paid/remote dependencies.

## Code standards
- Python 3.11+
- Type hints for public interfaces
- Pydantic v2 strict schemas for structured output contracts
- Do not hardcode Ollama model tags that may not exist

## Pull request checklist
- [ ] Tests pass locally
- [ ] README instructions updated when behavior changes
- [ ] No fabricated benchmark numbers in docs or reports
- [ ] Results are generated from local measurements only
