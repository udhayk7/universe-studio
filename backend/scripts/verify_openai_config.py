from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import get_settings  # noqa: E402
from app.integrations.openai.status import get_openai_auth_status  # noqa: E402


def main() -> int:
    get_settings.cache_clear()
    status = get_openai_auth_status()
    print(json.dumps(status.to_response(), indent=2, sort_keys=True))
    return 0 if status.api_key_found and status.client_initialized else 1


if __name__ == "__main__":
    raise SystemExit(main())
