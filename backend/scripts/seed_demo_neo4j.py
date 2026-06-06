from __future__ import annotations

import json

from sqlalchemy import select

from app.db.models.universe import Universe
from app.db.session import SessionLocal
from app.services.demo_seed_service import DEMO_UNIVERSE_TITLE, DemoSeedService


def main() -> None:
    db = SessionLocal()
    try:
        universe = db.scalar(
            select(Universe).where(Universe.title == DEMO_UNIVERSE_TITLE).limit(1)
        )
        if universe is None:
            raise SystemExit("Demo universe not found. Run backend/scripts/seed_demo.py first.")

        synced, message = DemoSeedService(db).sync_neo4j(universe.id)
        print(
            json.dumps(
                {
                    "universe_id": str(universe.id),
                    "neo4j_synced": synced,
                    "neo4j_message": message,
                },
                indent=2,
            )
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
