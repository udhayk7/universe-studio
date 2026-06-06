from __future__ import annotations

import argparse

from app.db.session import SessionLocal
from app.services.demo_seed_service import DemoSeedService


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the deterministic Universe Studio demo.")
    parser.add_argument("--no-reset", action="store_true", help="Do not replace an existing demo.")
    parser.add_argument("--skip-neo4j", action="store_true", help="Seed Postgres only.")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        result = DemoSeedService(db).seed(
            reset=not args.no_reset,
            sync_neo4j=not args.skip_neo4j,
        )
        print(result.model_dump_json(indent=2))
    finally:
        db.close()


if __name__ == "__main__":
    main()
