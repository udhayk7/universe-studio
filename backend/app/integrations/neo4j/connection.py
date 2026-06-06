from __future__ import annotations

from collections.abc import Generator

from app.core.config import get_settings
from neo4j import Driver, GraphDatabase, Session


class Neo4jConnectionManager:
    def __init__(self, uri: str, user: str, password: str) -> None:
        self._driver: Driver = GraphDatabase.driver(uri, auth=(user, password))

    @property
    def driver(self) -> Driver:
        return self._driver

    def verify_connectivity(self) -> None:
        self._driver.verify_connectivity()

    def session(self) -> Session:
        return self._driver.session()

    def close(self) -> None:
        self._driver.close()


_neo4j_manager: Neo4jConnectionManager | None = None


def get_neo4j_manager() -> Neo4jConnectionManager:
    global _neo4j_manager
    if _neo4j_manager is None:
        settings = get_settings()
        _neo4j_manager = Neo4jConnectionManager(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password,
        )
    return _neo4j_manager


def get_neo4j_session() -> Generator[Session, None, None]:
    manager = get_neo4j_manager()
    with manager.session() as session:
        yield session
