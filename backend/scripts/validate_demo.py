from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from sqlalchemy import func, select

from app.db.models.agent_run import AgentRun
from app.db.models.character import Character
from app.db.models.consistency_check import ConsistencyCheck
from app.db.models.episode import Episode
from app.db.models.event import Event
from app.db.models.relationship import Relationship
from app.db.models.scene import Scene
from app.db.models.timeline import Timeline
from app.db.models.universe import Universe
from app.db.session import SessionLocal
from app.services.character_memory_service import CharacterMemoryService
from app.services.demo_seed_service import DEMO_UNIVERSE_TITLE, TIMELINE_B_NAME
from app.services.timeline_diff_service import TimelineDiffService
from app.services.universe_memory_explorer_service import UniverseMemoryExplorerService


@dataclass(slots=True)
class Check:
    name: str
    passed: bool
    detail: str


def main() -> None:
    db = SessionLocal()
    try:
        universe = db.scalar(
            select(Universe).where(Universe.title == DEMO_UNIVERSE_TITLE).limit(1)
        )
        checks: list[Check] = []
        if universe is None:
            checks.append(Check("universe creation", False, "Demo universe is missing."))
            print_report(checks)
            raise SystemExit(1)

        timelines = list(
            db.scalars(select(Timeline).where(Timeline.universe_id == universe.id))
        )
        timeline_b = next(
            (timeline for timeline in timelines if timeline.name == TIMELINE_B_NAME),
            None,
        )
        characters = list(
            db.scalars(select(Character).where(Character.universe_id == universe.id))
        )
        episodes = list(
            db.scalars(select(Episode).where(Episode.universe_id == universe.id))
        )

        graph = UniverseMemoryExplorerService(db).graph(universe.id)
        completed_episodes = [episode for episode in episodes if episode.status == "completed"]
        branch_events = list(
            db.scalars(
                select(Event).where(
                    Event.universe_id == universe.id,
                    Event.event_type == "timeline_branch_modification",
                )
            )
        )
        relationships = _count(db, Relationship, universe.id)
        scenes = _scene_count(db, universe.id)
        consistency_checks = _count(db, ConsistencyCheck, universe.id)
        agent_runs = _count(db, AgentRun, universe.id)

        checks.extend(
            [
                Check(
                    "universe creation",
                    universe.title == DEMO_UNIVERSE_TITLE,
                    f"Found {universe.title} ({universe.id}).",
                ),
                Check(
                    "graph generation",
                    len(graph.nodes) >= 29 and len(graph.edges) >= 40,
                    (
                        f"{len(graph.nodes)} graph nodes, {len(graph.edges)} graph "
                        f"edges via {graph.source}."
                    ),
                ),
                Check(
                    "character dossiers",
                    len(characters) == 8
                    and all(_has_context_pack(db, character) for character in characters),
                    f"{len(characters)} characters with retrievable context packs.",
                ),
                Check(
                    "episode generation",
                    len(completed_episodes) >= 2 and scenes >= 8,
                    f"{len(completed_episodes)} completed episodes and {scenes} scenes.",
                ),
                Check(
                    "branching",
                    (
                        len(timelines) == 2
                        and timeline_b is not None
                        and timeline_b.parent_timeline_id is not None
                    ),
                    (
                        f"{len(timelines)} timelines; Timeline B parent set: "
                        f"{bool(timeline_b and timeline_b.parent_timeline_id)}."
                    ),
                ),
                Check(
                    "alternate future generation",
                    bool(
                        timeline_b
                        and any(
                            episode.timeline_id == timeline_b.id
                            for episode in completed_episodes
                        )
                    ),
                    "Timeline B has a completed alternate-future episode.",
                ),
                Check(
                    "timeline differences",
                    _has_timeline_diff(db, timelines),
                    (
                        f"{len(branch_events)} branch modification event(s), "
                        f"{relationships} relationships."
                    ),
                ),
                Check(
                    "consistency checks",
                    consistency_checks >= 2,
                    f"{consistency_checks} stored consistency checks.",
                ),
                Check(
                    "agent traces",
                    agent_runs >= 10,
                    f"{agent_runs} stored agent trace rows.",
                ),
            ]
        )
        print_report(checks)
        if not all(check.passed for check in checks):
            raise SystemExit(1)
    finally:
        db.close()


def _has_context_pack(db, character: Character) -> bool:
    pack = CharacterMemoryService(db).get_context_pack(character.id)
    return bool(pack.relationships and pack.important_memories and pack.arc)


def _has_timeline_diff(db, timelines: list[Timeline]) -> bool:
    if len(timelines) < 2:
        return False
    base = next((timeline for timeline in timelines if timeline.is_canon), timelines[0])
    compare = next((timeline for timeline in timelines if not timeline.is_canon), timelines[-1])
    diff = TimelineDiffService(db).diff(
        base_timeline_id=base.id,
        compare_timeline_id=compare.id,
    )
    return bool(diff.changed_events or diff.relationship_differences or diff.state_differences)


def _count(db, model, universe_id) -> int:
    return int(
        db.scalar(
            select(func.count()).select_from(model).where(model.universe_id == universe_id)
        )
        or 0
    )


def _scene_count(db, universe_id) -> int:
    episode_ids = select(Episode.id).where(Episode.universe_id == universe_id)
    return int(
        db.scalar(
            select(func.count()).select_from(Scene).where(Scene.episode_id.in_(episode_ids))
        )
        or 0
    )


def print_report(checks: list[Check]) -> None:
    print(
        json.dumps(
            {
                "passed": all(check.passed for check in checks),
                "checks": [asdict(check) for check in checks],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
