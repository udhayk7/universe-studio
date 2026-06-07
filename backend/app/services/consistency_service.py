from __future__ import annotations

import logging
import re
import uuid
from collections import Counter

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.agents.consistency_agents import ConsistencyAgentRunner
from app.core.config import get_settings
from app.core.exceptions import NotFoundError
from app.db.models.character import Character
from app.db.models.consistency_check import ConsistencyCheck
from app.db.models.episode import Episode
from app.db.models.memory_entry import MemoryEntry
from app.db.models.timeline import Timeline
from app.db.models.universe import Universe
from app.schemas.consistency import (
    AffectedEntity,
    ConsistencyCheckRead,
    ConsistencyCheckRequest,
    ConsistencyCheckResult,
    ConsistencyDashboardSummary,
    ConsistencyIssue,
    ConsistencyReport,
)
from app.schemas.episode_generation import EpisodeContextPack, GeneratedEpisode

logger = logging.getLogger(__name__)
BLOCKING_SEVERITIES = frozenset({"high", "blocker"})


class ConsistencyService:
    def __init__(
        self,
        db: Session,
        *,
        agent_runner: ConsistencyAgentRunner | None = None,
    ) -> None:
        self._db = db
        self._agent_runner = agent_runner

    def check(self, payload: ConsistencyCheckRequest) -> ConsistencyCheckResult:
        universe, timeline = self._resolve_universe_timeline(
            universe_id=payload.universe_id,
            timeline_id=payload.timeline_id,
        )
        if payload.episode_id is not None:
            episode = self._db.get(Episode, payload.episode_id)
            if episode is None or episode.universe_id != universe.id:
                raise NotFoundError("Episode", payload.episode_id)

        report = self._combine_reports(
            self._deterministic_content_report(
                universe=universe,
                timeline=timeline,
                content=payload.content,
            ),
            self._agent_report(
                self._manual_agent_input(
                    universe=universe,
                    timeline=timeline,
                    content=payload.content,
                )
            ),
        )
        checks = self.persist_report(
            universe_id=universe.id,
            timeline_id=timeline.id,
            report=report,
            episode_id=payload.episode_id,
        )
        return ConsistencyCheckResult(report=report, checks=checks)

    def get_check(self, check_id: uuid.UUID) -> ConsistencyCheckRead:
        check = self._db.get(ConsistencyCheck, check_id)
        if check is None:
            raise NotFoundError("ConsistencyCheck", check_id)
        return ConsistencyCheckRead.model_validate(check)

    def dashboard(self, universe_id: uuid.UUID) -> ConsistencyDashboardSummary:
        universe = self._db.get(Universe, universe_id)
        if universe is None:
            raise NotFoundError("Universe", universe_id)

        checks = list(
            self._db.scalars(
                select(ConsistencyCheck)
                .where(ConsistencyCheck.universe_id == universe_id)
                .order_by(ConsistencyCheck.created_at.desc())
                .limit(100)
            )
        )
        status_counts = Counter(check.status for check in checks)
        severity_counts = Counter(check.severity for check in checks)
        type_counts = Counter(check.issue_type for check in checks)

        return ConsistencyDashboardSummary(
            universe_id=universe_id,
            open_issues=status_counts["open"],
            resolved_issues=status_counts["resolved"],
            severity_breakdown={
                "low": severity_counts["low"],
                "medium": severity_counts["medium"],
                "high": severity_counts["high"],
                "blocker": severity_counts["blocker"],
                "critical": severity_counts["critical"],
            },
            timeline_conflicts=type_counts["timeline"],
            character_conflicts=type_counts["character"],
            relationship_conflicts=type_counts["relationship"],
            world_rule_violations=type_counts["world_rule"],
            branch_conflicts=type_counts["branch"],
            issues=[ConsistencyCheckRead.model_validate(check) for check in checks],
        )

    def validate_generated_episode(
        self,
        *,
        context: EpisodeContextPack,
        generated: GeneratedEpisode,
    ) -> ConsistencyReport:
        local_report = self._deterministic_episode_report(context=context, generated=generated)
        agent_report = self._agent_report(self._generated_episode_agent_input(context, generated))
        return self._combine_reports(local_report, agent_report)

    def persist_report(
        self,
        *,
        universe_id: uuid.UUID,
        timeline_id: uuid.UUID,
        report: ConsistencyReport,
        episode_id: uuid.UUID | None = None,
    ) -> list[ConsistencyCheckRead]:
        checks: list[ConsistencyCheck] = []
        logger.info(
            "Persisting consistency report",
            extra={
                "universe_id": str(universe_id),
                "timeline_id": str(timeline_id),
                "episode_id": str(episode_id) if episode_id else None,
                "verdict": report.verdict,
                "issue_count": len(report.issues),
                "severity_counts": dict(Counter(issue.severity for issue in report.issues)),
                "blocker_count": len(self.blocking_issues(report)),
            },
        )
        for issue in report.issues:
            check = ConsistencyCheck(
                universe_id=universe_id,
                timeline_id=timeline_id,
                episode_id=episode_id,
                severity=issue.severity,
                issue_type=issue.issue_type,
                description=f"{issue.issue}\n\n{issue.explanation}",
                suggested_fix=issue.suggested_fix,
                affected_entities=[
                    entity.model_dump(mode="json", exclude_none=True)
                    for entity in issue.affected_entities
                ],
                status="open",
            )
            self._db.add(check)
            checks.append(check)

        self._db.commit()
        for check in checks:
            self._db.refresh(check)
        return [ConsistencyCheckRead.model_validate(check) for check in checks]

    def has_blocking_issues(self, report: ConsistencyReport) -> bool:
        return bool(self.blocking_issues(report))

    def blocking_issues(self, report: ConsistencyReport) -> list[ConsistencyIssue]:
        return [issue for issue in report.issues if issue.severity in BLOCKING_SEVERITIES]

    def _resolve_universe_timeline(
        self,
        *,
        universe_id: uuid.UUID,
        timeline_id: uuid.UUID,
    ) -> tuple[Universe, Timeline]:
        universe = self._db.get(Universe, universe_id)
        if universe is None:
            raise NotFoundError("Universe", universe_id)

        timeline = self._db.get(Timeline, timeline_id)
        if timeline is None or timeline.universe_id != universe.id:
            raise NotFoundError("Timeline", timeline_id)
        return universe, timeline

    def _deterministic_content_report(
        self,
        *,
        universe: Universe,
        timeline: Timeline,
        content: str,
    ) -> ConsistencyReport:
        lowered = content.casefold()
        issues: list[ConsistencyIssue] = []

        for character in self._characters(universe.id):
            if self._is_dead(character.status) and character.canonical_name.casefold() in lowered:
                issues.append(
                    ConsistencyIssue(
                        severity="high",
                        issue_type="character",
                        issue="Dead or inactive character appears in new content.",
                        explanation=(
                            f"{character.canonical_name} is currently marked "
                            f"'{character.status}', but appears in the submitted content."
                        ),
                        suggested_fix=(
                            "Clarify that the character appears through memory, recording, "
                            "or flashback, or update the character state with a causal event."
                        ),
                        affected_entities=[
                            AffectedEntity(
                                entity_type="character",
                                entity_id=str(character.id),
                                name=character.canonical_name,
                            )
                        ],
                    )
                )

        issues.extend(self._world_rule_issues(universe.id, timeline.id, lowered))
        issues.extend(self._branch_leakage_issues(universe.id, timeline.id, content))
        return self._report_from_issues(issues, source="deterministic checks")

    def _deterministic_episode_report(
        self,
        *,
        context: EpisodeContextPack,
        generated: GeneratedEpisode,
    ) -> ConsistencyReport:
        issues: list[ConsistencyIssue] = []
        known_characters = {
            self._normalize(character.name): character for character in context.characters
        }
        known_locations = {self._normalize(location.name) for location in context.locations}
        scene_numbers = [scene.scene_number for scene in generated.scenes]

        if sorted(scene_numbers) != list(range(1, len(scene_numbers) + 1)):
            issues.append(
                ConsistencyIssue(
                    severity="medium",
                    issue_type="timeline",
                    issue="Scene numbering is not sequential.",
                    explanation=(
                        "The generated episode has missing or duplicated scene numbers, "
                        "which makes future event ordering ambiguous."
                    ),
                    suggested_fix="Renumber scenes from 1 without gaps or duplicates.",
                    affected_entities=[AffectedEntity(entity_type="episode", name=generated.title)],
                )
            )

        for scene in generated.scenes:
            normalized_scene_characters = [self._normalize(name) for name in scene.characters]
            if len(normalized_scene_characters) != len(set(normalized_scene_characters)):
                issues.append(
                    ConsistencyIssue(
                        severity="low",
                        issue_type="character",
                        issue="Scene contains duplicate character participants.",
                        explanation=f"Scene {scene.scene_number} lists a character more than once.",
                        suggested_fix="Deduplicate scene participants before persistence.",
                        affected_entities=[
                            AffectedEntity(entity_type="scene", name=scene.title),
                        ],
                    )
                )

            for character_name in scene.characters:
                character = known_characters.get(self._normalize(character_name))
                if character is None:
                    issues.append(
                        ConsistencyIssue(
                            severity="high",
                            issue_type="character",
                            issue="Unknown character appears in generated scene.",
                            explanation=(
                                f"{character_name} is not present in this universe's "
                                "character memory."
                            ),
                            suggested_fix=(
                                "Use an existing character or create the character during "
                                "universe extraction before episode generation."
                            ),
                            affected_entities=[
                                AffectedEntity(entity_type="character", name=character_name),
                                AffectedEntity(entity_type="scene", name=scene.title),
                            ],
                        )
                    )
                    continue

                if self._is_dead(character.status):
                    issues.append(
                        ConsistencyIssue(
                            severity="blocker",
                            issue_type="character",
                            issue="Dead character is acting in a generated scene.",
                            explanation=(
                                f"{character.name} is currently '{character.status}' in "
                                f"timeline {context.timeline_name}, but appears as an "
                                f"active participant in scene {scene.scene_number}."
                            ),
                            suggested_fix=(
                                "Rewrite the scene as a memory/recording/flashback, or add "
                                "a prior resurrection or survival event to this timeline."
                            ),
                            affected_entities=[
                                AffectedEntity(
                                    entity_type="character",
                                    entity_id=character.id,
                                    name=character.name,
                                ),
                                AffectedEntity(entity_type="scene", name=scene.title),
                            ],
                        )
                    )

            if known_locations and self._normalize(scene.location) not in known_locations:
                issues.append(
                    ConsistencyIssue(
                        severity="low",
                        issue_type="timeline",
                        issue="Generated scene introduces an unstored location.",
                        explanation=(
                            f"{scene.location} is not currently in location memory. "
                            "This can be valid, but it should be intentional."
                        ),
                        suggested_fix="Confirm the new location or reuse an established location.",
                        affected_entities=[
                            AffectedEntity(entity_type="location", name=scene.location)
                        ],
                    )
                )

        existing_scene_numbers = set(scene_numbers)
        for change in generated.knowledge_changes:
            if (
                change.source_scene_number is not None
                and change.source_scene_number not in existing_scene_numbers
            ):
                issues.append(
                    ConsistencyIssue(
                        severity="high",
                        issue_type="character",
                        issue="Character knowledge references a scene that does not exist.",
                        explanation=(
                            f"{change.character} learns something from scene "
                            f"{change.source_scene_number}, but that scene is not in the episode."
                        ),
                        suggested_fix="Point the knowledge update at an existing scene.",
                        affected_entities=[
                            AffectedEntity(entity_type="character", name=change.character),
                        ],
                    )
                )

        for change in generated.relationship_changes:
            existing = self._find_context_relationship(
                context,
                change.source_character,
                change.target_character,
            )
            if (
                existing is not None
                and (existing.strength or 0) >= 70
                and change.strength_delta <= -70
            ):
                issues.append(
                    ConsistencyIssue(
                        severity="medium",
                        issue_type="relationship",
                        issue="Strong relationship reverses abruptly.",
                        explanation=(
                            f"{change.source_character} and {change.target_character} move "
                            "from a high-trust relationship to a severe negative shift."
                        ),
                        suggested_fix=(
                            "Add a visible betrayal, revelation, or causal scene outcome."
                        ),
                        affected_entities=[
                            AffectedEntity(entity_type="character", name=change.source_character),
                            AffectedEntity(entity_type="character", name=change.target_character),
                        ],
                    )
                )

        content = generated.model_dump_json()
        lowered = content.casefold()
        issues.extend(
            self._world_rule_issues(
                uuid.UUID(context.universe.id),
                uuid.UUID(context.timeline_id),
                lowered,
            )
        )
        issues.extend(
            self._branch_leakage_issues(
                uuid.UUID(context.universe.id),
                uuid.UUID(context.timeline_id),
                content,
            )
        )
        return self._report_from_issues(issues, source="deterministic episode checks")

    def _agent_report(self, input_text: str) -> ConsistencyReport | None:
        settings = get_settings()
        if not settings.openai_api_key:
            return None
        runner = self._agent_runner or ConsistencyAgentRunner()
        return runner.check(input_text)

    def _combine_reports(
        self,
        first: ConsistencyReport,
        second: ConsistencyReport | None,
    ) -> ConsistencyReport:
        issues = [*first.issues, *(second.issues if second else [])]
        return self._report_from_issues(
            issues,
            source="deterministic checks and Consistency Agent"
            if second
            else "deterministic checks",
        )

    def _report_from_issues(
        self,
        issues: list[ConsistencyIssue],
        *,
        source: str,
    ) -> ConsistencyReport:
        if any(issue.severity in BLOCKING_SEVERITIES for issue in issues):
            verdict = "fail"
        elif issues:
            verdict = "warning"
        else:
            verdict = "pass"

        summary = (
            f"{source} found {len(issues)} continuity issue"
            f"{'' if len(issues) == 1 else 's'}."
            if issues
            else f"{source} found no continuity issues."
        )
        return ConsistencyReport(verdict=verdict, issues=issues, summary=summary)

    def _world_rule_issues(
        self,
        universe_id: uuid.UUID,
        timeline_id: uuid.UUID,
        lowered_content: str,
    ) -> list[ConsistencyIssue]:
        issues: list[ConsistencyIssue] = []
        rules = self._db.scalars(
            select(MemoryEntry)
            .where(
                MemoryEntry.universe_id == universe_id,
                MemoryEntry.timeline_id == timeline_id,
                MemoryEntry.memory_type == "world_rule",
            )
            .limit(20)
        ).all()
        for rule in rules:
            lowered_rule = rule.content.casefold()
            markers = self._world_rule_violation_markers(lowered_rule)
            if (
                ("cannot" in lowered_rule or "never" in lowered_rule or "forbidden" in lowered_rule)
                and self._rule_subject_appears(lowered_rule, lowered_content)
                and self._affirmative_violation_marker_appears(lowered_content, markers)
            ):
                issues.append(
                    ConsistencyIssue(
                        severity="high",
                        issue_type="world_rule",
                        issue="Generated content may violate a world rule.",
                        explanation=f"Stored world rule: {rule.content}",
                        suggested_fix=(
                            "Rewrite the scene to obey the rule or create a causal exception."
                        ),
                        affected_entities=[
                            AffectedEntity(
                                entity_type="memory_entry",
                                entity_id=str(rule.id),
                                name="World rule",
                            )
                        ],
                    )
                )
        return issues

    def _world_rule_violation_markers(self, lowered_rule: str) -> tuple[str, ...]:
        if any(marker in lowered_rule for marker in ("copy", "copied", "duplicate", "clone")):
            return ("copy", "copied", "duplicate", "duplicated", "clone", "cloned")
        if any(marker in lowered_rule for marker in ("recover", "recovered", "restore")):
            return ("recover", "recovered", "restore", "restored", "reclaim", "reclaimed")
        return ("violate", "violated", "break", "broke", "bypass", "bypassed")

    def _affirmative_violation_marker_appears(
        self,
        lowered_content: str,
        markers: tuple[str, ...],
    ) -> bool:
        for marker in markers:
            pattern = re.compile(rf"\b{re.escape(marker)}\b")
            for match in pattern.finditer(lowered_content):
                window = lowered_content[max(0, match.start() - 48) : match.end() + 24]
                if any(
                    negation in window
                    for negation in (
                        "cannot ",
                        "can't ",
                        "do not ",
                        "does not ",
                        "did not ",
                        "must not ",
                        "not ",
                        "never ",
                        "no ",
                        "without ",
                    )
                ):
                    continue
                return True
        return False

    def _branch_leakage_issues(
        self,
        universe_id: uuid.UUID,
        timeline_id: uuid.UUID,
        content: str,
    ) -> list[ConsistencyIssue]:
        lowered_content = content.casefold()
        current_timeline = self._db.get(Timeline, timeline_id)
        sibling_timelines = self._db.scalars(
            select(Timeline).where(
                Timeline.universe_id == universe_id,
                Timeline.id != timeline_id,
            )
        ).all()
        issues: list[ConsistencyIssue] = []
        for timeline in sibling_timelines:
            if timeline.name and timeline.name.casefold() in lowered_content:
                issues.append(
                    ConsistencyIssue(
                        severity="high",
                        issue_type="branch",
                        issue="Generated content references another timeline branch.",
                        explanation=(
                            "Content for "
                            f"{current_timeline.name if current_timeline else 'this timeline'} "
                            f"references sibling branch {timeline.name}."
                        ),
                        suggested_fix=(
                            "Remove cross-branch facts unless this is explicitly "
                            "framed as metadata."
                        ),
                        affected_entities=[
                            AffectedEntity(
                                entity_type="timeline",
                                entity_id=str(timeline.id),
                                name=timeline.name,
                            )
                        ],
                    )
                )
        return issues

    def _characters(self, universe_id: uuid.UUID) -> list[Character]:
        return list(
            self._db.scalars(
                select(Character).where(Character.universe_id == universe_id)
            )
        )

    def _find_context_relationship(
        self,
        context: EpisodeContextPack,
        source: str,
        target: str,
    ):
        normalized_source = self._normalize(source)
        normalized_target = self._normalize(target)
        for relationship in context.relationships:
            if (
                self._normalize(relationship.source_character) == normalized_source
                and self._normalize(relationship.target_character) == normalized_target
            ):
                return relationship
        return None

    def _manual_agent_input(self, *, universe: Universe, timeline: Timeline, content: str) -> str:
        issue_counts = self._existing_issue_counts(universe.id)
        return (
            "Universe continuity validation request.\n\n"
            f"Universe: {universe.title}\n"
            f"Premise: {universe.premise or 'None'}\n"
            f"Timeline: {timeline.name}\n"
            f"Existing open issues: {issue_counts}\n\n"
            "Content to validate:\n"
            f"{content}"
        )

    def _generated_episode_agent_input(
        self,
        context: EpisodeContextPack,
        generated: GeneratedEpisode,
    ) -> str:
        return (
            "Validate this generated episode before persistence.\n\n"
            "Episode Context Pack:\n"
            f"{context.model_dump_json(indent=2)}\n\n"
            "Generated Episode:\n"
            f"{generated.model_dump_json(indent=2)}"
        )

    def _existing_issue_counts(self, universe_id: uuid.UUID) -> dict[str, int]:
        rows = self._db.execute(
            select(ConsistencyCheck.severity, func.count(ConsistencyCheck.id))
            .where(ConsistencyCheck.universe_id == universe_id, ConsistencyCheck.status == "open")
            .group_by(ConsistencyCheck.severity)
        ).all()
        return {str(severity): int(count) for severity, count in rows}

    def _rule_subject_appears(self, lowered_rule: str, lowered_content: str) -> bool:
        meaningful_terms = [
            term
            for term in lowered_rule.replace(".", " ").replace(",", " ").split()
            if len(term) >= 6 and term not in {"cannot", "should", "forbidden"}
        ]
        return any(term in lowered_content for term in meaningful_terms)

    def _is_dead(self, status: str | None) -> bool:
        normalized = (status or "").casefold()
        return any(marker in normalized for marker in ("dead", "deceased", "killed"))

    def _normalize(self, value: str | None) -> str:
        return " ".join((value or "").casefold().split())
