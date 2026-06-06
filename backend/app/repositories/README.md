# Repositories

Repositories isolate persistence details.

Use naming like:

- `universe_repository.py`
- `timeline_repository.py`
- `memory_repository.py`
- `graph_repository.py`
- `asset_repository.py`

Repositories should not call OpenAI models or perform orchestration.
