from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from neo4j import Session


class GraphRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute_read(
        self, query: str, parameters: Mapping[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        result = self._session.run(query, dict(parameters or {}))
        return [record.data() for record in result]

    def execute_write(
        self, query: str, parameters: Mapping[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        result = self._session.run(query, dict(parameters or {}))
        return [record.data() for record in result]

    def health_check(self) -> bool:
        result = self._session.run("RETURN 1 AS ok")
        return result.single(strict=True)["ok"] == 1
