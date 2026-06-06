# Universe Memory Engine

The memory engine converts validated agent proposals into branch-aware memory patches.

Expected future modules:

- `patches.py`: Memory patch request types.
- `commit_builder.py`: Creates timeline commit payloads.
- `character_memory.py`: Character memory helpers.
- `event_memory.py`: Event memory helpers.
- `relationship_memory.py`: Relationship memory helpers.
- `timeline_memory.py`: Branch-aware memory retrieval.
- `conflicts.py`: Conflict types and resolution helpers.

This folder should not contain HTTP endpoint code.
