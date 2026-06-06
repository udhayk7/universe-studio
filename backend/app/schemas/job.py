from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import Field

from app.schemas.common import TimestampedResponse


class JobRead(TimestampedResponse):
    universe_id: uuid.UUID | None = None
    job_type: str
    status: str
    progress: int
    message: str | None = None
    result_data: dict[str, Any] = Field(default_factory=dict)
    completed_at: datetime | None = None
