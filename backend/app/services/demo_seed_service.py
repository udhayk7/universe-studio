from __future__ import annotations

# ruff: noqa: E501
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from neo4j.exceptions import Neo4jError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.agent_run import AgentRun
from app.db.models.character import Character
from app.db.models.character_state_history import CharacterStateHistory
from app.db.models.consistency_check import ConsistencyCheck
from app.db.models.episode import Episode
from app.db.models.event import Event
from app.db.models.event_participant import EventParticipant
from app.db.models.job import Job
from app.db.models.location import Location
from app.db.models.memory_entry import MemoryEntry
from app.db.models.relationship import Relationship
from app.db.models.scene import Scene
from app.db.models.scene_participant import SceneParticipant
from app.db.models.timeline import Timeline
from app.db.models.timeline_commit import TimelineCommit
from app.db.models.timeline_commit_event import TimelineCommitEvent
from app.db.models.universe import Universe
from app.db.models.world_object import WorldObject
from app.integrations.neo4j.connection import get_neo4j_manager
from app.integrations.neo4j.relationships import (
    ALLIED_WITH,
    BETRAYED,
    KNOWS,
    LOVES,
    OCCURRED_AT,
    OWNS,
    PARTICIPATED_IN,
    RELATIONSHIP_TYPES,
)
from app.repositories.graph_repository import GraphRepository
from app.schemas.demo import DemoSeedResult, DemoSeedSummary

DEMO_UNIVERSE_TITLE = "Memory Market 2094"
TIMELINE_A_NAME = "Timeline A - Maya Survives"
TIMELINE_B_NAME = "Timeline B - Maya Dies"


@dataclass(slots=True)
class EpisodeSeed:
    title: str
    logline: str
    summary: str
    scenes: list[dict[str, Any]]


class DemoSeedService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def seed(self, *, reset: bool = True, sync_neo4j: bool = True) -> DemoSeedResult:
        if reset:
            self._reset_demo_universe()

        existing = self._db.scalar(
            select(Universe).where(Universe.title == DEMO_UNIVERSE_TITLE).limit(1)
        )
        if existing is not None:
            return self._result_for_existing(existing, sync_neo4j=sync_neo4j)

        universe = Universe(
            title=DEMO_UNIVERSE_TITLE,
            tagline="Every memory has a price.",
            premise="Memories are bought and sold as currency.",
            genre="neo-noir science fiction",
            tone="cinematic, tense, emotional",
            status="demo_ready",
        )
        self._db.add(universe)
        self._db.flush()

        timeline_a = Timeline(universe_id=universe.id, name=TIMELINE_A_NAME, is_canon=True)
        self._db.add(timeline_a)
        self._db.flush()

        initial_commit = self._commit(
            timeline=timeline_a,
            parent=None,
            message="World seed: Memory Market 2094",
            commit_type="demo_seed",
            created_by="demo_seeder",
        )

        locations = self._create_locations(universe.id)
        characters = self._create_characters(universe.id)
        self._create_objects(universe.id, characters, locations)
        self._create_world_rules(universe.id, timeline_a.id, initial_commit.id)
        self._create_initial_character_memory(universe.id, timeline_a.id, initial_commit.id, characters)
        self._create_initial_states(universe.id, timeline_a.id, initial_commit.id, characters)

        a_commits, a_events = self._create_timeline_a_events(
            universe=universe,
            timeline=timeline_a,
            parent_commit=initial_commit,
            characters=characters,
            locations=locations,
        )
        branch_point_commit = a_commits["maya_survives"]
        branch_source_event = a_events["maya_survives"]

        self._create_relationships(
            universe_id=universe.id,
            timeline=timeline_a,
            characters=characters,
            variant="a",
            valid_from_event_id=branch_source_event.id,
        )
        self._create_timeline_a_post_branch_states(
            universe.id,
            timeline_a.id,
            branch_point_commit.id,
            characters,
        )

        timeline_b = Timeline(
            universe_id=universe.id,
            parent_timeline_id=timeline_a.id,
            branch_from_commit_id=branch_point_commit.id,
            name=TIMELINE_B_NAME,
            is_canon=False,
        )
        self._db.add(timeline_b)
        self._db.flush()

        b_branch_commit, b_branch_event, b_future_commit = self._create_timeline_b_branch(
            universe=universe,
            timeline=timeline_b,
            parent_commit=branch_point_commit,
            characters=characters,
            locations=locations,
        )
        self._copy_branch_memory(
            source_timeline=timeline_a,
            target_timeline=timeline_b,
            branch_commit=b_branch_commit,
            inherited_until_commit=branch_point_commit,
        )
        self._create_relationships(
            universe_id=universe.id,
            timeline=timeline_b,
            characters=characters,
            variant="b",
            valid_from_event_id=b_branch_event.id,
        )
        self._create_timeline_b_states(
            universe.id,
            timeline_b.id,
            b_branch_commit.id,
            b_future_commit.id,
            characters,
        )

        episode_a = self._create_episode(
            universe=universe,
            timeline=timeline_a,
            parent_commit=a_commits["accord"],
            seed=self._episode_a_seed(),
            characters=characters,
            locations=locations,
            order_start=16,
            job_prompt="Generate Episode 1 after Maya survives the Vault Collapse.",
        )
        episode_b = self._create_episode(
            universe=universe,
            timeline=timeline_b,
            parent_commit=b_future_commit,
            seed=self._episode_b_seed(),
            characters=characters,
            locations=locations,
            order_start=20,
            job_prompt="Generate the alternate future after Maya dies.",
        )

        self._create_consistency_checks(
            universe=universe,
            timeline_a=timeline_a,
            timeline_b=timeline_b,
            episode_a=episode_a,
            episode_b=episode_b,
        )

        timeline_a.head_commit_id = episode_a.commit_id
        timeline_b.head_commit_id = episode_b.commit_id
        universe.active_timeline_id = timeline_a.id
        self._db.add_all([timeline_a, timeline_b, universe])
        self._db.commit()

        neo4j_synced = False
        neo4j_message = "Neo4j sync skipped."
        if sync_neo4j:
            neo4j_synced, neo4j_message = self.sync_neo4j(universe.id)

        return self._build_result(
            universe_id=universe.id,
            timeline_a_id=timeline_a.id,
            timeline_b_id=timeline_b.id,
            branch_event_id=b_branch_event.id,
            episode_ids=[episode_a.id, episode_b.id],
            alternate_future_episode_id=episode_b.id,
            neo4j_synced=neo4j_synced,
            neo4j_message=neo4j_message,
        )

    def sync_neo4j(self, universe_id: uuid.UUID) -> tuple[bool, str]:
        universe = self._db.get(Universe, universe_id)
        if universe is None:
            return False, f"Universe {universe_id} not found."

        try:
            manager = get_neo4j_manager()
            with manager.session() as session:
                repository = GraphRepository(session)
                self._reset_neo4j_demo_graph(repository)
                self._write_neo4j_graph(repository, universe)
        except (Neo4jError, OSError, RuntimeError) as error:
            return False, f"Neo4j unavailable: {error}"
        return True, "Neo4j demo graph synced."

    def _reset_demo_universe(self) -> None:
        existing_universes = list(
            self._db.scalars(select(Universe).where(Universe.title == DEMO_UNIVERSE_TITLE))
        )
        for universe in existing_universes:
            universe.active_timeline_id = None
            self._db.add(universe)
        self._db.flush()

        for universe in existing_universes:
            self._db.delete(universe)
        self._db.commit()

    def _create_locations(self, universe_id: uuid.UUID) -> dict[str, Location]:
        data = [
            ("South Exchange", "The loudest memory trading floor in the lower city.", "market"),
            ("Vault of First Light", "A sealed archive of childhood memories.", "archive"),
            ("Null Choir Station", "A pirate broadcast tower above the transit spine.", "station"),
            ("Civic Recall Court", "The court where purchased memories become legal evidence.", "court"),
            ("Orin House", "A private tower owned by the dynasty that prices grief.", "estate"),
            ("The Forgetting Rain", "A rooftop district where corrupted memories fall as static.", "district"),
        ]
        locations: dict[str, Location] = {}
        for name, description, location_type in data:
            location = Location(
                universe_id=universe_id,
                name=name,
                description=description,
                location_type=location_type,
                rules={},
            )
            self._db.add(location)
            locations[name] = location
        self._db.flush()
        return locations

    def _create_characters(self, universe_id: uuid.UUID) -> dict[str, Character]:
        data = [
            (
                "Maya Orin",
                ["Maya", "The Unpriced Heir"],
                "A runaway heir who can remember emotions other people sold away.",
                ["defiant", "empathetic", "strategic"],
                ["free memory debtors", "break her family's pricing engine"],
                ["becoming a commodity", "losing her own childhood"],
                "alive",
            ),
            (
                "Jax Vey",
                ["Jax", "Receipt Runner"],
                "A courier who smuggles forbidden memories through market ledgers.",
                ["loyal", "reckless", "funny under pressure"],
                ["protect Maya", "repay the city he exploited"],
                ["being remembered only as a thief"],
                "alive",
            ),
            (
                "Dr. Nia Sol",
                ["Nia"],
                "The neuroscientist who built the Recall Lattice and regrets it.",
                ["brilliant", "guilty", "precise"],
                ["repair the lattice", "keep memory copies impossible"],
                ["her invention erasing consent forever"],
                "alive",
            ),
            (
                "Rook Sable",
                ["Rook"],
                "A market fixer who sells secrets but still keeps one moral line.",
                ["cynical", "observant", "transactional"],
                ["control the black receipt market", "stay alive"],
                ["owing anyone an honest debt"],
                "alive",
            ),
            (
                "Tessa Vale",
                ["Tess", "The Broadcast Saint"],
                "A pirate journalist turning stolen memories into public uprisings.",
                ["fearless", "provocative", "compassionate"],
                ["broadcast the truth", "protect forgotten families"],
                ["silence", "state ownership of grief"],
                "alive",
            ),
            (
                "Cassian Harlow",
                ["Cassian", "The Ledger Minister"],
                "The civic minister who profits from legal memory auctions.",
                ["polished", "ruthless", "patient"],
                ["control the market", "own the Recall Lattice"],
                ["public accountability", "Maya surviving with evidence"],
                "alive",
            ),
            (
                "Elian Kade",
                ["The Archivist", "Elian"],
                "A retired archive keeper who knows where the first stolen memories sleep.",
                ["gentle", "haunted", "protective"],
                ["restore the childhood cache", "save Maya from Orin House"],
                ["the archive burning again"],
                "alive",
            ),
            (
                "Vera Orin",
                ["Vera", "The Price Matriarch"],
                "Maya's mother and the architect of grief-backed currency.",
                ["commanding", "calculating", "wounded"],
                ["preserve Orin House", "recover Maya"],
                ["a city where grief cannot be priced"],
                "alive",
            ),
        ]
        characters: dict[str, Character] = {}
        for name, aliases, description, traits, goals, fears, status in data:
            character = Character(
                universe_id=universe_id,
                canonical_name=name,
                aliases=aliases,
                description=description,
                traits={
                    "personality": traits,
                    "strengths": traits[:2],
                    "weaknesses": [fears[0]],
                },
                goals={"items": goals},
                fears={"items": fears},
                voice_style="cinematic, grounded, emotionally specific",
                status=status,
            )
            self._db.add(character)
            characters[name] = character
        self._db.flush()
        return characters

    def _create_objects(
        self,
        universe_id: uuid.UUID,
        characters: dict[str, Character],
        locations: dict[str, Location],
    ) -> dict[str, WorldObject]:
        data = [
            ("Black Receipt", "A ledger token proving memories were illegally copied.", "evidence", "Rook Sable", None),
            ("Recall Lattice", "The machine that prices memory weight across the city.", "machine", None, "Vault of First Light"),
            ("Childhood Cache", "A sealed archive of unpriced childhood memories.", "archive", "Elian Kade", "Vault of First Light"),
            ("Orin Price Key", "Vera's biometric key to the grief-backed currency engine.", "key", "Vera Orin", "Orin House"),
            ("Null Choir Transmitter", "A pirate relay that can broadcast memory fragments citywide.", "device", "Tessa Vale", "Null Choir Station"),
            ("Maya's Echo Shard", "A volatile imprint created at the timeline branch point.", "memory_artifact", "Jax Vey", None),
        ]
        objects: dict[str, WorldObject] = {}
        for name, description, object_type, owner_name, location_name in data:
            world_object = WorldObject(
                universe_id=universe_id,
                name=name,
                description=description,
                object_type=object_type,
                status="active",
                current_owner_character_id=characters[owner_name].id if owner_name else None,
                current_location_id=locations[location_name].id if location_name else None,
            )
            self._db.add(world_object)
            objects[name] = world_object
        self._db.flush()
        return objects

    def _create_world_rules(
        self,
        universe_id: uuid.UUID,
        timeline_id: uuid.UUID,
        commit_id: uuid.UUID,
    ) -> None:
        rules = [
            "Memories can be transferred, but a person feels the emotional absence afterward.",
            "Memories cannot be copied without creating an unstable echo shard.",
            "A memory used as legal currency must be verified in the Civic Recall Court.",
            "A sold childhood memory cannot be naturally recovered without the original receipt.",
        ]
        for rule in rules:
            self._memory(
                universe_id=universe_id,
                timeline_id=timeline_id,
                commit_id=commit_id,
                entity_type="universe",
                entity_id=None,
                memory_type="world_rule",
                content=rule,
                structured_value={"rule": rule},
            )

    def _create_initial_character_memory(
        self,
        universe_id: uuid.UUID,
        timeline_id: uuid.UUID,
        commit_id: uuid.UUID,
        characters: dict[str, Character],
    ) -> None:
        for character in characters.values():
            self._memory(
                universe_id=universe_id,
                timeline_id=timeline_id,
                commit_id=commit_id,
                entity_type="character",
                entity_id=character.id,
                memory_type="character_memory",
                content=f"{character.canonical_name} is established in the market conflict.",
                structured_value={"character": character.canonical_name},
            )
            self._memory(
                universe_id=universe_id,
                timeline_id=timeline_id,
                commit_id=commit_id,
                entity_type="character",
                entity_id=character.id,
                memory_type="goal",
                content=str(character.goals["items"][0]),
                structured_value={"goal": character.goals["items"][0]},
            )
            self._memory(
                universe_id=universe_id,
                timeline_id=timeline_id,
                commit_id=commit_id,
                entity_type="character",
                entity_id=character.id,
                memory_type="fear",
                content=str(character.fears["items"][0]),
                structured_value={"fear": character.fears["items"][0]},
            )

    def _create_initial_states(
        self,
        universe_id: uuid.UUID,
        timeline_id: uuid.UUID,
        commit_id: uuid.UUID,
        characters: dict[str, Character],
    ) -> None:
        for character in characters.values():
            self._db.add(
                CharacterStateHistory(
                    universe_id=universe_id,
                    character_id=character.id,
                    timeline_id=timeline_id,
                    commit_id=commit_id,
                    current_status=character.status,
                    emotional_state="pressurized",
                    physical_state="stable",
                    summary=f"{character.canonical_name} enters the demo under market pressure.",
                    source="demo_seed",
                    confidence=1.0,
                )
            )

    def _create_timeline_a_events(
        self,
        *,
        universe: Universe,
        timeline: Timeline,
        parent_commit: TimelineCommit,
        characters: dict[str, Character],
        locations: dict[str, Location],
    ) -> tuple[dict[str, TimelineCommit], dict[str, Event]]:
        specs = [
            ("act", "The Mnemonic Act Passes", "Memory transfers become legal currency.", "Civic Recall Court", ["Cassian Harlow", "Vera Orin"], 1, 8),
            ("rescue", "Maya Saves Jax at the South Exchange", "Maya buys back Jax's fear before brokers erase his route memory.", "South Exchange", ["Maya Orin", "Jax Vey"], 2, 7),
            ("ledger", "Cassian Opens the Civic Ledger", "Cassian weaponizes court records to identify memory debtors.", "Civic Recall Court", ["Cassian Harlow", "Tessa Vale"], 3, 6),
            ("lattice", "Nia Builds the Recall Lattice", "Nia proves the lattice can price grief with terrifying accuracy.", "Vault of First Light", ["Dr. Nia Sol", "Vera Orin"], 4, 8),
            ("receipt", "Rook Steals the Black Receipt", "Rook steals proof that Orin House copied forbidden memories.", "South Exchange", ["Rook Sable", "Jax Vey"], 5, 7),
            ("riot", "Tessa Broadcasts the First Memory Riot", "Tessa airs stolen testimony and starts a citywide protest.", "Null Choir Station", ["Tessa Vale", "Maya Orin"], 6, 8),
            ("audit", "Orin House Marks Maya for Audit", "Vera declares Maya an asset of Orin House.", "Orin House", ["Vera Orin", "Maya Orin"], 7, 9),
            ("cache", "Elian Hides the Childhood Cache", "Elian moves unpriced childhood memories below the old vault.", "Vault of First Light", ["Elian Kade", "Maya Orin"], 8, 8),
            ("hack", "The Null Choir Hacks the Vault", "The pirate relay opens the vault for thirteen seconds.", "Null Choir Station", ["Tessa Vale", "Dr. Nia Sol", "Rook Sable"], 9, 7),
            ("collapse", "The Vault Collapse Begins", "The Recall Lattice overloads and starts erasing owned grief.", "Vault of First Light", ["Maya Orin", "Jax Vey", "Dr. Nia Sol"], 10, 9),
            ("maya_survives", "Maya Survives the Collapse", "Maya absorbs the echo surge and walks out with the Black Receipt.", "Vault of First Light", ["Maya Orin", "Jax Vey", "Dr. Nia Sol"], 11, 10),
            ("expose", "Maya Exposes Cassian's Ledger", "Maya proves the minister sold civic memories to Orin House.", "Civic Recall Court", ["Maya Orin", "Cassian Harlow", "Tessa Vale"], 12, 9),
            ("freeze", "The Market Freezes Memory Prices", "The South Exchange halts trading while the city audits grief debt.", "South Exchange", ["Rook Sable", "Vera Orin"], 13, 8),
            ("return", "Jax Returns the Stolen Childhoods", "Jax uses the receipt routes to return hundreds of childhood memories.", "The Forgetting Rain", ["Jax Vey", "Elian Kade"], 14, 8),
            ("accord", "The City Ratifies the Recall Accord", "The city bans coercive memory debt and protects first memories.", "Civic Recall Court", ["Maya Orin", "Tessa Vale", "Dr. Nia Sol"], 15, 9),
        ]
        commits: dict[str, TimelineCommit] = {}
        events: dict[str, Event] = {}
        current_parent = parent_commit
        for key, title, summary, location_name, participant_names, order, importance in specs:
            commit = self._commit(
                timeline=timeline,
                parent=current_parent,
                message=title,
                commit_type="historical_event",
                created_by="demo_seeder",
            )
            event = self._event(
                universe_id=universe.id,
                commit_id=commit.id,
                title=title,
                summary=summary,
                location_id=locations[location_name].id,
                participant_ids=[characters[name].id for name in participant_names],
                event_type="historical_event",
                order_index=order,
                importance=importance,
            )
            for name in participant_names:
                self._character_arc_memory(universe.id, timeline.id, commit.id, characters[name], event)
            commits[key] = commit
            events[key] = event
            current_parent = commit
        timeline.head_commit_id = current_parent.id
        return commits, events

    def _create_timeline_b_branch(
        self,
        *,
        universe: Universe,
        timeline: Timeline,
        parent_commit: TimelineCommit,
        characters: dict[str, Character],
        locations: dict[str, Location],
    ) -> tuple[TimelineCommit, Event, TimelineCommit]:
        branch_commit = self._commit(
            timeline=timeline,
            parent=parent_commit,
            message="Branch divergence: Maya dies in the Vault Collapse",
            commit_type="timeline_branch",
            created_by="demo_seeder",
        )
        branch_event = self._event(
            universe_id=universe.id,
            commit_id=branch_commit.id,
            title="Maya Dies in the Vault Collapse",
            summary="Maya shields Jax from the echo surge and dies before exposing Cassian.",
            location_id=locations["Vault of First Light"].id,
            participant_ids=[
                characters["Maya Orin"].id,
                characters["Jax Vey"].id,
                characters["Dr. Nia Sol"].id,
            ],
            event_type="timeline_branch_modification",
            order_index=11,
            importance=10,
        )
        self._memory(
            universe_id=universe.id,
            timeline_id=timeline.id,
            commit_id=branch_commit.id,
            entity_type="timeline",
            entity_id=timeline.id,
            memory_type="branch_divergence",
            content="Timeline B diverges when Maya dies instead of surviving the Vault Collapse.",
            structured_value={
                "timeline": TIMELINE_B_NAME,
                "changed_event": "Maya Survives the Collapse",
                "new_outcome": "Maya dies",
            },
            valid_from_event_id=branch_event.id,
        )

        specs = [
            ("Jax Becomes Guardian of Maya's Echo", "Jax preserves a volatile shard of Maya's final memory.", "The Forgetting Rain", ["Jax Vey", "Elian Kade"], 12, 9),
            ("Cassian Seizes the Recall Lattice", "With Maya gone, Cassian claims emergency control of the lattice.", "Civic Recall Court", ["Cassian Harlow", "Vera Orin", "Dr. Nia Sol"], 13, 9),
            ("Rook Betrays the Black Receipt", "Rook sells the receipt route to protect Tessa from arrest.", "South Exchange", ["Rook Sable", "Tessa Vale"], 14, 8),
            ("Tessa Sparks the Empty Name Uprising", "Tessa broadcasts Maya's last memory and starts a leaderless revolt.", "Null Choir Station", ["Tessa Vale", "Jax Vey"], 15, 9),
            ("The City Trades Grief Futures", "Cassian turns predicted grief into the next market instrument.", "Civic Recall Court", ["Cassian Harlow", "Vera Orin", "Jax Vey"], 16, 9),
            ("Nia Locks the Echo Shard", "Nia seals Maya's shard before it duplicates across the city.", "Vault of First Light", ["Dr. Nia Sol", "Jax Vey", "Elian Kade"], 17, 8),
        ]
        current_parent = branch_commit
        for title, summary, location_name, participant_names, order, importance in specs:
            commit = self._commit(
                timeline=timeline,
                parent=current_parent,
                message=title,
                commit_type="alternate_future_event",
                created_by="demo_seeder",
            )
            event = self._event(
                universe_id=universe.id,
                commit_id=commit.id,
                title=title,
                summary=summary,
                location_id=locations[location_name].id,
                participant_ids=[characters[name].id for name in participant_names],
                event_type="alternate_future_event",
                order_index=order,
                importance=importance,
            )
            for name in participant_names:
                self._character_arc_memory(universe.id, timeline.id, commit.id, characters[name], event)
            current_parent = commit
        timeline.head_commit_id = current_parent.id
        return branch_commit, branch_event, current_parent

    def _copy_branch_memory(
        self,
        *,
        source_timeline: Timeline,
        target_timeline: Timeline,
        branch_commit: TimelineCommit,
        inherited_until_commit: TimelineCommit,
    ) -> None:
        inherited_commit_ids = self._commit_ids_until(source_timeline.id, inherited_until_commit.id)
        entries = self._db.scalars(
            select(MemoryEntry).where(
                MemoryEntry.timeline_id == source_timeline.id,
                MemoryEntry.commit_id.in_(inherited_commit_ids),
            )
        ).all()
        for entry in entries:
            self._memory(
                universe_id=entry.universe_id,
                timeline_id=target_timeline.id,
                commit_id=branch_commit.id,
                entity_type=entry.entity_type,
                entity_id=entry.entity_id,
                memory_type=entry.memory_type,
                content=entry.content,
                structured_value={
                    **entry.structured_value,
                    "inherited_from_timeline_id": str(source_timeline.id),
                },
                valid_from_event_id=entry.valid_from_event_id,
            )

    def _create_relationships(
        self,
        *,
        universe_id: uuid.UUID,
        timeline: Timeline,
        characters: dict[str, Character],
        variant: str,
        valid_from_event_id: uuid.UUID,
    ) -> None:
        base_relationships = [
            ("Maya Orin", "Jax Vey", LOVES, 82, "Maya and Jax repeatedly choose each other over profit."),
            ("Jax Vey", "Maya Orin", LOVES, 78, "Jax risks his routes to protect Maya."),
            ("Maya Orin", "Dr. Nia Sol", ALLIED_WITH, 74, "They both want the lattice made accountable."),
            ("Dr. Nia Sol", "Maya Orin", ALLIED_WITH, 68, "Nia trusts Maya with the lattice truth."),
            ("Maya Orin", "Vera Orin", BETRAYED, -72, "Vera marks Maya as an asset of Orin House."),
            ("Vera Orin", "Maya Orin", KNOWS, -55, "Vera knows Maya's compassion is a threat."),
            ("Tessa Vale", "Maya Orin", ALLIED_WITH, 81, "Tessa makes Maya's evidence public."),
            ("Maya Orin", "Tessa Vale", ALLIED_WITH, 70, "Maya trusts Tessa to broadcast the truth."),
            ("Rook Sable", "Jax Vey", KNOWS, 48, "They trade routes and favors in the South Exchange."),
            ("Jax Vey", "Rook Sable", KNOWS, 42, "Jax knows Rook always prices loyalty."),
            ("Rook Sable", "Tessa Vale", ALLIED_WITH, 36, "Rook protects Tessa when it still benefits him."),
            ("Tessa Vale", "Rook Sable", KNOWS, 28, "Tessa knows Rook's betrayal math."),
            ("Cassian Harlow", "Vera Orin", ALLIED_WITH, 76, "Cassian and Vera profit from legal memory auctions."),
            ("Vera Orin", "Cassian Harlow", ALLIED_WITH, 73, "Vera uses Cassian's court to launder memory debt."),
            ("Cassian Harlow", "Maya Orin", BETRAYED, -84, "Cassian needs Maya erased or discredited."),
            ("Maya Orin", "Cassian Harlow", BETRAYED, -80, "Maya exposes Cassian's ledger."),
            ("Elian Kade", "Maya Orin", ALLIED_WITH, 85, "Elian protects Maya's childhood cache."),
            ("Maya Orin", "Elian Kade", ALLIED_WITH, 78, "Maya treats Elian as chosen family."),
            ("Elian Kade", "Vera Orin", KNOWS, -44, "Elian remembers what Vera did to the first archive."),
            ("Dr. Nia Sol", "Cassian Harlow", BETRAYED, -66, "Cassian weaponizes Nia's invention."),
            ("Cassian Harlow", "Dr. Nia Sol", KNOWS, -38, "Cassian understands Nia's guilt can be coerced."),
            ("Tessa Vale", "Cassian Harlow", BETRAYED, -74, "Tessa broadcasts Cassian's corruption."),
            ("Jax Vey", "Elian Kade", ALLIED_WITH, 61, "Jax and Elian return stolen childhoods together."),
            ("Vera Orin", "Rook Sable", KNOWS, 35, "Vera buys Rook's market intelligence."),
        ]
        variant_overrides = {
            ("Maya Orin", "Jax Vey"): (LOVES, 95, "Maya's death turns Jax's love into a vow."),
            ("Jax Vey", "Maya Orin"): (LOVES, 96, "Jax guards Maya's echo shard."),
            ("Rook Sable", "Tessa Vale"): (BETRAYED, -62, "Rook sells the receipt route to save Tessa."),
            ("Tessa Vale", "Rook Sable"): (BETRAYED, -68, "Tessa cannot forgive Rook's transaction."),
            ("Cassian Harlow", "Vera Orin"): (ALLIED_WITH, 90, "Maya's death lets Cassian and Vera consolidate control."),
            ("Dr. Nia Sol", "Jax Vey"): (ALLIED_WITH, 64, "Nia helps Jax stabilize Maya's echo shard."),
            ("Jax Vey", "Cassian Harlow"): (BETRAYED, -90, "Jax blames Cassian for Maya's death."),
        }
        for source_name, target_name, rel_type, strength, evidence in base_relationships:
            if variant == "b" and (source_name, target_name) in variant_overrides:
                rel_type, strength, evidence = variant_overrides[(source_name, target_name)]
            self._db.add(
                Relationship(
                    universe_id=universe_id,
                    timeline_id=timeline.id,
                    source_character_id=characters[source_name].id,
                    target_character_id=characters[target_name].id,
                    relationship_type=rel_type,
                    strength=strength,
                    status="active",
                    valid_from_event_id=valid_from_event_id,
                    evidence=evidence,
                    confidence=0.95,
                )
            )
            self._memory(
                universe_id=universe_id,
                timeline_id=timeline.id,
                commit_id=timeline.head_commit_id or valid_from_event_id,
                entity_type="relationship",
                entity_id=None,
                memory_type="relationship_memory",
                content=f"{source_name} -> {target_name}: {rel_type} ({strength}). {evidence}",
                structured_value={
                    "source": source_name,
                    "target": target_name,
                    "relationship_type": rel_type,
                    "strength": strength,
                },
            )
        self._db.flush()

    def _create_timeline_a_post_branch_states(
        self,
        universe_id: uuid.UUID,
        timeline_id: uuid.UUID,
        commit_id: uuid.UUID,
        characters: dict[str, Character],
    ) -> None:
        states = {
            "Maya Orin": ("alive", "resolved", "exhausted", "Maya survives and carries the echo surge."),
            "Jax Vey": ("alive", "hopeful", "bruised", "Jax believes the market can still be repaired."),
            "Cassian Harlow": ("alive", "cornered", "stable", "Cassian faces public exposure."),
        }
        self._create_states(universe_id, timeline_id, commit_id, characters, states)

    def _create_timeline_b_states(
        self,
        universe_id: uuid.UUID,
        timeline_id: uuid.UUID,
        branch_commit_id: uuid.UUID,
        future_commit_id: uuid.UUID,
        characters: dict[str, Character],
    ) -> None:
        branch_states = {
            "Maya Orin": ("dead", "absent", "deceased", "Maya dies shielding Jax from the echo surge."),
            "Jax Vey": ("alive", "broken", "injured", "Jax survives with Maya's echo shard."),
            "Dr. Nia Sol": ("alive", "guilty", "stable", "Nia blames herself for the unstable shard."),
        }
        future_states = {
            "Cassian Harlow": ("alive", "emboldened", "stable", "Cassian controls grief futures."),
            "Tessa Vale": ("alive", "furious", "hunted", "Tessa leads the Empty Name uprising."),
            "Rook Sable": ("alive", "ashamed", "stable", "Rook's betrayal costs him the only trust he valued."),
        }
        self._create_states(universe_id, timeline_id, branch_commit_id, characters, branch_states)
        self._create_states(universe_id, timeline_id, future_commit_id, characters, future_states)

    def _create_states(
        self,
        universe_id: uuid.UUID,
        timeline_id: uuid.UUID,
        commit_id: uuid.UUID,
        characters: dict[str, Character],
        states: dict[str, tuple[str, str, str, str]],
    ) -> None:
        for name, (status, emotional, physical, summary) in states.items():
            self._db.add(
                CharacterStateHistory(
                    universe_id=universe_id,
                    character_id=characters[name].id,
                    timeline_id=timeline_id,
                    commit_id=commit_id,
                    current_status=status,
                    emotional_state=emotional,
                    physical_state=physical,
                    summary=summary,
                    source="demo_seed",
                    confidence=1.0,
                )
            )
            self._memory(
                universe_id=universe_id,
                timeline_id=timeline_id,
                commit_id=commit_id,
                entity_type="character",
                entity_id=characters[name].id,
                memory_type="state_change",
                content=summary,
                structured_value={
                    "current_status": status,
                    "emotional_state": emotional,
                    "physical_state": physical,
                },
            )

    def _create_episode(
        self,
        *,
        universe: Universe,
        timeline: Timeline,
        parent_commit: TimelineCommit,
        seed: EpisodeSeed,
        characters: dict[str, Character],
        locations: dict[str, Location],
        order_start: int,
        job_prompt: str,
    ) -> Episode:
        commit = self._commit(
            timeline=timeline,
            parent=parent_commit,
            message=f"Generated episode: {seed.title}",
            commit_type="episode_generation",
            created_by="director_agent",
        )
        episode = Episode(
            universe_id=universe.id,
            timeline_id=timeline.id,
            commit_id=commit.id,
            title=seed.title,
            logline=seed.logline,
            summary=seed.summary,
            status="completed",
        )
        self._db.add(episode)
        self._db.flush()

        for index, scene_seed in enumerate(seed.scenes, start=1):
            location = locations[str(scene_seed["location"])]
            scene = Scene(
                episode_id=episode.id,
                location_id=location.id,
                scene_number=index,
                title=str(scene_seed["title"]),
                summary=str(scene_seed["outcome"]),
                dialogue=str(scene_seed["dialogue"]),
                visual_direction=str(scene_seed["description"]),
            )
            self._db.add(scene)
            self._db.flush()
            participant_ids = [characters[name].id for name in scene_seed["characters"]]
            for character_id in participant_ids:
                self._db.add(
                    SceneParticipant(scene_id=scene.id, character_id=character_id, role="primary")
                )
            event = self._event(
                universe_id=universe.id,
                commit_id=commit.id,
                title=str(scene_seed["title"]),
                summary=str(scene_seed["outcome"]),
                location_id=location.id,
                participant_ids=participant_ids,
                event_type="generated_episode_scene",
                order_index=order_start + index - 1,
                importance=8,
            )
            self._memory(
                universe_id=universe.id,
                timeline_id=timeline.id,
                commit_id=commit.id,
                entity_type="episode",
                entity_id=episode.id,
                memory_type="scene_outcome",
                content=f"Scene {index}: {scene.summary}",
                structured_value={"scene_id": str(scene.id), "event_id": str(event.id)},
                valid_from_event_id=event.id,
            )

        self._memory(
            universe_id=universe.id,
            timeline_id=timeline.id,
            commit_id=commit.id,
            entity_type="universe",
            entity_id=universe.id,
            memory_type="episode_summary",
            content=f"{seed.title}: {seed.summary}",
            structured_value={"episode_id": str(episode.id), "episode_title": seed.title},
        )
        job = self._create_episode_job(universe.id, episode, job_prompt)
        self._create_agent_trace(universe.id, timeline.id, episode, job)
        timeline.head_commit_id = commit.id
        return episode

    def _create_episode_job(
        self,
        universe_id: uuid.UUID,
        episode: Episode,
        prompt: str,
    ) -> Job:
        job = Job(
            universe_id=universe_id,
            job_type="episode_generation",
            status="completed",
            progress=100,
            message="Demo episode generated",
            result_data={
                "episode_id": str(episode.id),
                "universe_id": str(universe_id),
                "scene_count": 4,
                "memory_entries_created": 6,
                "consistency_issues": 0,
                "consistency_verdict": "pass",
                "prompt": prompt,
            },
            completed_at=datetime.now(UTC),
        )
        self._db.add(job)
        self._db.flush()
        return job

    def _create_agent_trace(
        self,
        universe_id: uuid.UUID,
        timeline_id: uuid.UUID,
        episode: Episode,
        job: Job,
    ) -> None:
        steps = [
            ("Historian Agent", "Retrieved branch-aware memory.", "Retrieved 8 characters, 24 relationships, 18 memories, 6 locations."),
            ("Story Agent", "Built story outline from memory.", "Generated a 4-beat outline with character pressure."),
            ("Director Agent", "Converted outline into scenes.", "Generated 4 cinematic scenes with dialogue and outcomes."),
            ("Consistency Agent", "Checked character, timeline, branch, and world-rule continuity.", "Verdict pass; found 0 blocking issues."),
            ("Memory Update", "Committed durable consequences.", "Created scene outcomes, events, and episode summary memories."),
        ]
        for index, (agent_name, input_summary, output_summary) in enumerate(steps):
            started_at = datetime.now(UTC)
            self._db.add(
                AgentRun(
                    universe_id=universe_id,
                    job_id=job.id,
                    episode_id=episode.id,
                    agent_name=agent_name,
                    input_summary=f"{input_summary} Timeline: {timeline_id}.",
                    output_summary=output_summary,
                    status="completed",
                    started_at=started_at,
                    completed_at=started_at,
                    duration_ms=420 + (index * 180),
                )
            )

    def _create_consistency_checks(
        self,
        *,
        universe: Universe,
        timeline_a: Timeline,
        timeline_b: Timeline,
        episode_a: Episode,
        episode_b: Episode,
    ) -> None:
        self._db.add_all(
            [
                ConsistencyCheck(
                    universe_id=universe.id,
                    timeline_id=timeline_a.id,
                    episode_id=episode_a.id,
                    severity="low",
                    issue_type="world_rule",
                    description=(
                        "New location introduced during generation.\n\n"
                        "The episode references The Forgetting Rain as an active district; "
                        "the seeder confirms it as a stored location."
                    ),
                    suggested_fix="Resolved by adding The Forgetting Rain to location memory.",
                    affected_entities=[{"entity_type": "location", "name": "The Forgetting Rain"}],
                    status="resolved",
                ),
                ConsistencyCheck(
                    universe_id=universe.id,
                    timeline_id=timeline_b.id,
                    episode_id=episode_b.id,
                    severity="medium",
                    issue_type="branch",
                    description=(
                        "Potential branch leakage prevented.\n\n"
                        "The alternate future avoids Timeline A's fact that Maya exposed "
                        "Cassian after surviving the collapse."
                    ),
                    suggested_fix="Keep Maya's post-collapse evidence out of Timeline B scenes.",
                    affected_entities=[
                        {"entity_type": "timeline", "name": TIMELINE_A_NAME},
                        {"entity_type": "timeline", "name": TIMELINE_B_NAME},
                    ],
                    status="open",
                ),
            ]
        )

    def _episode_a_seed(self) -> EpisodeSeed:
        return EpisodeSeed(
            title="The Price of Recall",
            logline="Maya survives the vault and forces the city to price truth above grief.",
            summary=(
                "After the Vault Collapse, Maya, Jax, Nia, and Tessa turn the Black "
                "Receipt into a public reckoning against Cassian and Orin House."
            ),
            scenes=[
                {
                    "title": "Echoes Under First Light",
                    "location": "Vault of First Light",
                    "characters": ["Maya Orin", "Jax Vey", "Dr. Nia Sol"],
                    "description": "Blue-white memory static rains through the cracked archive.",
                    "dialogue": "MAYA: I remember what they sold.\nJAX: Then make them pay in truth.",
                    "outcome": "Maya stabilizes the echo surge and keeps the Black Receipt intact.",
                },
                {
                    "title": "Broadcast Without Permission",
                    "location": "Null Choir Station",
                    "characters": ["Tessa Vale", "Maya Orin", "Rook Sable"],
                    "description": "The pirate tower turns the city skyline into a witness stand.",
                    "dialogue": "TESSA: The city hears everything now.\nROOK: Even what it bought to forget.",
                    "outcome": "Tessa broadcasts proof of copied memories across every exchange.",
                },
                {
                    "title": "The Minister's Auction",
                    "location": "Civic Recall Court",
                    "characters": ["Maya Orin", "Cassian Harlow", "Vera Orin"],
                    "description": "Court ledgers glow as citizens reclaim their own testimony.",
                    "dialogue": "CASSIAN: Evidence has a price.\nMAYA: Not when it remembers you.",
                    "outcome": "Maya exposes Cassian's illegal ledger and fractures Vera's control.",
                },
                {
                    "title": "Rain of Returned Names",
                    "location": "The Forgetting Rain",
                    "characters": ["Jax Vey", "Elian Kade", "Maya Orin"],
                    "description": "Forgotten childhoods fall as luminous rain over the rooftops.",
                    "dialogue": "ELIAN: First memories know their way home.\nJAX: Then let them run.",
                    "outcome": "The city begins returning stolen childhood memories to their owners.",
                },
            ],
        )

    def _episode_b_seed(self) -> EpisodeSeed:
        return EpisodeSeed(
            title="The City Without Maya",
            logline="In the branch where Maya dies, Jax turns grief into rebellion.",
            summary=(
                "Maya's death lets Cassian control the market, but Jax, Tessa, Nia, "
                "and Elian use her echo shard to ignite an alternate future."
            ),
            scenes=[
                {
                    "title": "The Shard That Answers",
                    "location": "The Forgetting Rain",
                    "characters": ["Jax Vey", "Elian Kade", "Dr. Nia Sol"],
                    "description": "Jax holds Maya's echo shard as rain turns to broken voices.",
                    "dialogue": "JAX: This is not a copy.\nNIA: No. It is what loss left behind.",
                    "outcome": "Nia stabilizes Maya's echo without violating the no-copy rule.",
                },
                {
                    "title": "Emergency Price",
                    "location": "Civic Recall Court",
                    "characters": ["Cassian Harlow", "Vera Orin", "Tessa Vale"],
                    "description": "Cassian sells grief futures beneath emergency banners.",
                    "dialogue": "CASSIAN: The city needs order.\nTESSA: It needs witnesses.",
                    "outcome": "Tessa captures evidence that Cassian is monetizing predicted grief.",
                },
                {
                    "title": "Receipt for a Betrayal",
                    "location": "South Exchange",
                    "characters": ["Rook Sable", "Tessa Vale", "Jax Vey"],
                    "description": "The exchange lights flicker as Rook confesses the sold route.",
                    "dialogue": "ROOK: I bought you time.\nTESSA: You sold our future.",
                    "outcome": "Rook loses Tessa's trust but gives Jax one route into the court.",
                },
                {
                    "title": "Empty Names Rise",
                    "location": "Null Choir Station",
                    "characters": ["Jax Vey", "Tessa Vale", "Dr. Nia Sol"],
                    "description": "The transmitter turns Maya's final memory into a citywide vow.",
                    "dialogue": "JAX: Say her name.\nTESSA: Say every name they priced.",
                    "outcome": "The Empty Name uprising begins without Timeline A's surviving Maya.",
                },
            ],
        )

    def _commit(
        self,
        *,
        timeline: Timeline,
        parent: TimelineCommit | None,
        message: str,
        commit_type: str,
        created_by: str,
    ) -> TimelineCommit:
        commit = TimelineCommit(
            timeline_id=timeline.id,
            parent_commit_id=parent.id if parent else None,
            message=message,
            commit_type=commit_type,
            created_by=created_by,
        )
        self._db.add(commit)
        self._db.flush()
        timeline.head_commit_id = commit.id
        return commit

    def _event(
        self,
        *,
        universe_id: uuid.UUID,
        commit_id: uuid.UUID,
        title: str,
        summary: str,
        location_id: uuid.UUID,
        participant_ids: list[uuid.UUID],
        event_type: str,
        order_index: int,
        importance: int,
    ) -> Event:
        event = Event(
            universe_id=universe_id,
            location_id=location_id,
            title=title,
            summary=summary,
            event_type=event_type,
            order_index=order_index,
            importance=importance,
        )
        self._db.add(event)
        self._db.flush()
        self._db.add(TimelineCommitEvent(commit_id=commit_id, event_id=event.id, change_type="created"))
        for character_id in participant_ids:
            self._db.add(EventParticipant(event_id=event.id, character_id=character_id, role="participant"))
        return event

    def _memory(
        self,
        *,
        universe_id: uuid.UUID,
        timeline_id: uuid.UUID,
        commit_id: uuid.UUID,
        entity_type: str,
        entity_id: uuid.UUID | None,
        memory_type: str,
        content: str,
        structured_value: dict[str, Any],
        valid_from_event_id: uuid.UUID | None = None,
    ) -> MemoryEntry:
        entry = MemoryEntry(
            universe_id=universe_id,
            timeline_id=timeline_id,
            commit_id=commit_id,
            entity_type=entity_type,
            entity_id=entity_id,
            memory_type=memory_type,
            content=content,
            structured_value=structured_value,
            confidence=1.0,
            source="demo_seed",
            valid_from_event_id=valid_from_event_id,
        )
        self._db.add(entry)
        return entry

    def _character_arc_memory(
        self,
        universe_id: uuid.UUID,
        timeline_id: uuid.UUID,
        commit_id: uuid.UUID,
        character: Character,
        event: Event,
    ) -> None:
        self._memory(
            universe_id=universe_id,
            timeline_id=timeline_id,
            commit_id=commit_id,
            entity_type="character",
            entity_id=character.id,
            memory_type="character_arc_event",
            content=f"{character.canonical_name} is changed by {event.title}: {event.summary}",
            structured_value={
                "event_title": event.title,
                "importance": event.importance,
                "order_index": event.order_index,
            },
            valid_from_event_id=event.id,
        )

    def _commit_ids_until(
        self,
        timeline_id: uuid.UUID,
        target_commit_id: uuid.UUID,
    ) -> list[uuid.UUID]:
        commits: list[uuid.UUID] = []
        current_id: uuid.UUID | None = target_commit_id
        seen: set[uuid.UUID] = set()
        while current_id is not None and current_id not in seen:
            seen.add(current_id)
            commit = self._db.get(TimelineCommit, current_id)
            if commit is None or commit.timeline_id != timeline_id:
                break
            commits.append(commit.id)
            current_id = commit.parent_commit_id
        return list(reversed(commits))

    def _result_for_existing(self, universe: Universe, *, sync_neo4j: bool) -> DemoSeedResult:
        timelines = list(
            self._db.scalars(select(Timeline).where(Timeline.universe_id == universe.id))
        )
        timeline_a = next(timeline for timeline in timelines if timeline.name == TIMELINE_A_NAME)
        timeline_b = next(timeline for timeline in timelines if timeline.name == TIMELINE_B_NAME)
        episodes = list(
            self._db.scalars(select(Episode).where(Episode.universe_id == universe.id))
        )
        branch_event = self._db.scalar(
            select(Event)
            .where(
                Event.universe_id == universe.id,
                Event.title == "Maya Dies in the Vault Collapse",
            )
            .limit(1)
        )
        neo4j_synced = False
        neo4j_message = "Neo4j sync skipped."
        if sync_neo4j:
            neo4j_synced, neo4j_message = self.sync_neo4j(universe.id)
        return self._build_result(
            universe_id=universe.id,
            timeline_a_id=timeline_a.id,
            timeline_b_id=timeline_b.id,
            branch_event_id=branch_event.id if branch_event else uuid.uuid4(),
            episode_ids=[episode.id for episode in episodes],
            alternate_future_episode_id=episodes[-1].id,
            neo4j_synced=neo4j_synced,
            neo4j_message=neo4j_message,
        )

    def _build_result(
        self,
        *,
        universe_id: uuid.UUID,
        timeline_a_id: uuid.UUID,
        timeline_b_id: uuid.UUID,
        branch_event_id: uuid.UUID,
        episode_ids: list[uuid.UUID],
        alternate_future_episode_id: uuid.UUID,
        neo4j_synced: bool,
        neo4j_message: str | None,
    ) -> DemoSeedResult:
        return DemoSeedResult(
            universe_id=universe_id,
            timeline_a_id=timeline_a_id,
            timeline_b_id=timeline_b_id,
            branch_event_id=branch_event_id,
            episode_ids=episode_ids,
            alternate_future_episode_id=alternate_future_episode_id,
            summary=DemoSeedSummary(
                characters=self._count(Character, universe_id),
                locations=self._count(Location, universe_id),
                objects=self._count(WorldObject, universe_id),
                relationships=self._count(Relationship, universe_id),
                events=self._count(Event, universe_id),
                memory_entries=self._count(MemoryEntry, universe_id),
                timelines=self._count(Timeline, universe_id),
                episodes=self._count(Episode, universe_id),
                scenes=self._episode_child_count(Scene, universe_id),
                agent_runs=self._count(AgentRun, universe_id),
                consistency_checks=self._count(ConsistencyCheck, universe_id),
            ),
            neo4j_synced=neo4j_synced,
            neo4j_message=neo4j_message,
        )

    def _count(self, model: type[Any], universe_id: uuid.UUID) -> int:
        return int(
            self._db.scalar(
                select(func.count()).select_from(model).where(model.universe_id == universe_id)
            )
            or 0
        )

    def _episode_child_count(self, model: type[Any], universe_id: uuid.UUID) -> int:
        episode_ids = select(Episode.id).where(Episode.universe_id == universe_id)
        return len(list(self._db.scalars(select(model).where(model.episode_id.in_(episode_ids)))))

    def _reset_neo4j_demo_graph(self, repository: GraphRepository) -> None:
        repository.execute_write(
            """
            MATCH (u:Universe {title: $title})
            OPTIONAL MATCH (n)
            WHERE n.universe_id = u.id
            WITH collect(DISTINCT n) + collect(DISTINCT u) AS nodes
            UNWIND nodes AS node
            WITH node WHERE node IS NOT NULL
            DETACH DELETE node
            """,
            {"title": DEMO_UNIVERSE_TITLE},
        )

    def _write_neo4j_graph(self, repository: GraphRepository, universe: Universe) -> None:
        self._merge_node(
            repository,
            "Universe",
            universe.id,
            {
                "title": universe.title,
                "genre": universe.genre,
                "tone": universe.tone,
            },
        )
        for timeline in self._db.scalars(select(Timeline).where(Timeline.universe_id == universe.id)):
            self._merge_node(
                repository,
                "Timeline",
                timeline.id,
                {
                    "name": timeline.name,
                    "is_canon": timeline.is_canon,
                    "universe_id": str(universe.id),
                },
            )
        for character in self._db.scalars(select(Character).where(Character.universe_id == universe.id)):
            self._merge_node(
                repository,
                "Character",
                character.id,
                {
                    "name": character.canonical_name,
                    "status": character.status,
                    "universe_id": str(universe.id),
                },
            )
        for location in self._db.scalars(select(Location).where(Location.universe_id == universe.id)):
            self._merge_node(
                repository,
                "Location",
                location.id,
                {
                    "name": location.name,
                    "location_type": location.location_type,
                    "universe_id": str(universe.id),
                },
            )
        for world_object in self._db.scalars(select(WorldObject).where(WorldObject.universe_id == universe.id)):
            self._merge_node(
                repository,
                "Object",
                world_object.id,
                {
                    "name": world_object.name,
                    "object_type": world_object.object_type,
                    "status": world_object.status,
                    "universe_id": str(universe.id),
                },
            )
            if world_object.current_owner_character_id:
                self._merge_relationship(
                    repository,
                    "Character",
                    world_object.current_owner_character_id,
                    "Object",
                    world_object.id,
                    OWNS,
                    {"universe_id": str(universe.id)},
                )
        for event in self._db.scalars(select(Event).where(Event.universe_id == universe.id)):
            self._merge_node(
                repository,
                "Event",
                event.id,
                {
                    "title": event.title,
                    "event_type": event.event_type,
                    "importance": event.importance,
                    "order_index": event.order_index,
                    "universe_id": str(universe.id),
                },
            )
            for participant in event.participants:
                self._merge_relationship(
                    repository,
                    "Character",
                    participant.character_id,
                    "Event",
                    event.id,
                    PARTICIPATED_IN,
                    {"universe_id": str(universe.id), "role": participant.role},
                )
            if event.location_id:
                self._merge_relationship(
                    repository,
                    "Event",
                    event.id,
                    "Location",
                    event.location_id,
                    OCCURRED_AT,
                    {"universe_id": str(universe.id)},
                )
        for relationship in self._db.scalars(
            select(Relationship).where(Relationship.universe_id == universe.id)
        ):
            self._merge_relationship(
                repository,
                "Character",
                relationship.source_character_id,
                "Character",
                relationship.target_character_id,
                self._graph_relationship_type(relationship.relationship_type),
                {
                    "universe_id": str(universe.id),
                    "timeline_id": str(relationship.timeline_id),
                    "strength": relationship.strength,
                    "source_type": relationship.relationship_type,
                },
            )

    def _merge_node(
        self,
        repository: GraphRepository,
        label: str,
        entity_id: uuid.UUID,
        properties: dict[str, Any],
    ) -> None:
        repository.execute_write(
            f"MERGE (node:{label} {{id: $id}}) SET node += $properties",
            {"id": str(entity_id), "properties": self._serialize(properties)},
        )

    def _merge_relationship(
        self,
        repository: GraphRepository,
        from_label: str,
        from_id: uuid.UUID,
        to_label: str,
        to_id: uuid.UUID,
        relationship_type: str,
        properties: dict[str, Any],
    ) -> None:
        repository.execute_write(
            f"""
            MATCH (from_node:{from_label} {{id: $from_id}})
            MATCH (to_node:{to_label} {{id: $to_id}})
            MERGE (from_node)-[rel:{relationship_type}]->(to_node)
            SET rel += $properties
            """,
            {
                "from_id": str(from_id),
                "to_id": str(to_id),
                "properties": self._serialize(properties),
            },
        )

    def _graph_relationship_type(self, relationship_type: str) -> str:
        normalized = relationship_type.strip().upper().replace(" ", "_")
        return normalized if normalized in RELATIONSHIP_TYPES else KNOWS

    def _serialize(self, properties: dict[str, Any]) -> dict[str, Any]:
        return {
            key: str(value) if isinstance(value, uuid.UUID) else value
            for key, value in properties.items()
            if value is not None
        }
