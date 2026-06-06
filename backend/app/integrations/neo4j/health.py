from __future__ import annotations

from app.integrations.neo4j.connection import Neo4jConnectionManager


class Neo4jHealthService:
    def __init__(self, manager: Neo4jConnectionManager) -> None:
        self._manager = manager

    def is_healthy(self) -> bool:
        self._manager.verify_connectivity()
        with self._manager.session() as session:
            result = session.run("RETURN 1 AS ok")
            return result.single(strict=True)["ok"] == 1
