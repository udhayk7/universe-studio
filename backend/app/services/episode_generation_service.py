from __future__ import annotations

import logging
import uuid
from collections import Counter

from sqlalchemy.orm import Session

from app.agents.episode_agents import EpisodeAgentRunner
from app.schemas.consistency import ConsistencyIssue, ConsistencyReport
from app.schemas.episode_generation import EpisodeContextPack, EpisodeOutline
from app.services.agent_trace_service import AgentTraceService
from app.services.consistency_service import ConsistencyService
from app.services.episode_historian_service import EpisodeHistorianService
from app.services.episode_persistence_service import (
    EpisodePersistenceResult,
    EpisodePersistenceService,
)
from app.services.job_service import JobService

logger = logging.getLogger(__name__)


class ConsistencyBlockedEpisodeError(ValueError):
    def __init__(
        self,
        *,
        report: ConsistencyReport,
        blocking_issues: list[ConsistencyIssue],
    ) -> None:
        self.report = report
        self.blocking_issues = blocking_issues
        super().__init__(self._message())

    def _message(self) -> str:
        if not self.blocking_issues:
            return "Consistency validation blocked episode persistence."

        first_issue = self.blocking_issues[0]
        affected = ", ".join(
            entity.name or entity.entity_id or entity.entity_type
            for entity in first_issue.affected_entities
        )
        affected_text = f" Affected: {affected}." if affected else ""
        fix_text = (
            f" Suggested fix: {first_issue.suggested_fix}"
            if first_issue.suggested_fix
            else ""
        )
        return (
            "Consistency validation blocked episode persistence: "
            f"[{first_issue.severity.upper()}] {self._sentence(first_issue.issue)} "
            f"{self._sentence(first_issue.explanation)}{affected_text}{fix_text}"
        )

    def result_data(self) -> dict[str, object]:
        return {
            "error_type": "consistency_blocked",
            "consistency_verdict": self.report.verdict,
            "consistency_summary": self.report.summary,
            "consistency_issues": len(self.report.issues),
            "consistency_blockers": [
                issue.model_dump(mode="json", exclude_none=True)
                for issue in self.blocking_issues
            ],
            "consistency_report": self.report.model_dump(mode="json"),
        }

    def _sentence(self, text: str) -> str:
        stripped = text.strip()
        if stripped.endswith((".", "!", "?")):
            return stripped
        return f"{stripped}."


class EpisodeGenerationService:
    def __init__(
        self,
        db: Session,
        *,
        agent_runner: EpisodeAgentRunner | None = None,
    ) -> None:
        self._db = db
        self._job_service = JobService(db)
        self._trace_service = AgentTraceService(db)
        self._agent_runner = agent_runner or EpisodeAgentRunner()

    def generate(
        self,
        *,
        job_id: uuid.UUID,
        universe_id: uuid.UUID,
        prompt: str | None,
        timeline_id: uuid.UUID | None = None,
    ) -> EpisodePersistenceResult:
        self._job_service.update(
            job_id,
            status="running",
            progress=8,
            message="Historian Agent reading universe memory",
        )

        historian_run = self._trace_service.start(
            universe_id=universe_id,
            job_id=job_id,
            agent_name="Historian Agent",
            input_summary="Universe ID and active timeline memory requested.",
        )
        raw_context = EpisodeHistorianService(self._db).build_context_pack(
            universe_id=universe_id,
            prompt=prompt,
            timeline_id=timeline_id,
        )
        context = self._agent_runner.run_historian_agent(self._historian_input(raw_context))
        self._trace_service.complete(
            historian_run,
            output_summary=(
                f"Built context with {len(context.characters)} characters, "
                f"{len(context.relationships)} relationships, "
                f"{len(context.events)} events, and {len(context.memory_entries)} memories."
            ),
        )

        self._job_service.update(
            job_id,
            progress=32,
            message="Story Agent shaping episode outline",
        )
        story_run = self._trace_service.start(
            universe_id=universe_id,
            job_id=job_id,
            agent_name="Story Agent",
            input_summary="Episode context pack and user request.",
        )
        outline = self._agent_runner.run_story_agent(self._story_input(context))
        self._trace_service.complete(
            story_run,
            output_summary=f"Created outline '{outline.title}' with {len(outline.beats)} beats.",
        )

        self._job_service.update(
            job_id,
            progress=62,
            message="Director Agent writing cinematic scenes",
        )
        director_run = self._trace_service.start(
            universe_id=universe_id,
            job_id=job_id,
            agent_name="Director Agent",
            input_summary="Episode context pack and approved story outline.",
        )
        generated_episode = self._agent_runner.run_director_agent(
            self._director_input(context, outline)
        )
        self._trace_service.complete(
            director_run,
            output_summary=(
                f"Generated '{generated_episode.title}' with "
                f"{len(generated_episode.scenes)} scenes."
            ),
        )

        self._job_service.update(
            job_id,
            progress=78,
            message="Consistency Agent validating continuity",
        )
        consistency_run = self._trace_service.start(
            universe_id=universe_id,
            job_id=job_id,
            agent_name="Consistency Agent",
            input_summary=(
                "Generated episode, branch-aware memory, character states, "
                "and world rules."
            ),
        )
        consistency_service = ConsistencyService(self._db)
        consistency_report = consistency_service.validate_generated_episode(
            context=context,
            generated=generated_episode,
        )
        logger.info(
            "Full consistency report for episode generation job %s:\n%s",
            job_id,
            consistency_report.model_dump_json(indent=2),
        )
        blocking_issues = consistency_service.blocking_issues(consistency_report)
        severity_counts = Counter(issue.severity for issue in consistency_report.issues)
        logger.info(
            "Consistency decision for episode generation",
            extra={
                "job_id": str(job_id),
                "universe_id": str(universe_id),
                "timeline_id": context.timeline_id,
                "verdict": consistency_report.verdict,
                "severity_counts": dict(severity_counts),
                "blocker_count": len(blocking_issues),
                "should_persist": not blocking_issues,
            },
        )
        self._trace_service.complete(
            consistency_run,
            output_summary=(
                f"Verdict {consistency_report.verdict}; found "
                f"{len(consistency_report.issues)} issue"
                f"{'' if len(consistency_report.issues) == 1 else 's'}."
            ),
        )
        if blocking_issues:
            logger.warning(
                "Episode persistence blocked by consistency validation",
                extra={
                    "job_id": str(job_id),
                    "universe_id": str(universe_id),
                    "timeline_id": context.timeline_id,
                    "blocker_count": len(blocking_issues),
                    "first_blocker": blocking_issues[0].model_dump(
                        mode="json",
                        exclude_none=True,
                    ),
                },
            )
            consistency_service.persist_report(
                universe_id=universe_id,
                timeline_id=uuid.UUID(context.timeline_id),
                report=consistency_report,
            )
            raise ConsistencyBlockedEpisodeError(
                report=consistency_report,
                blocking_issues=blocking_issues,
            )

        self._job_service.update(
            job_id,
            progress=88,
            message="Memory Update committing validated consequences",
        )
        memory_run = self._trace_service.start(
            universe_id=universe_id,
            job_id=job_id,
            agent_name="Memory Update",
            input_summary=(
                "Validated episode, scene outcomes, relationship deltas, "
                "and memory changes."
            ),
        )
        result = EpisodePersistenceService(self._db).persist_episode(
            context=context,
            outline=outline,
            generated=generated_episode,
        )
        self._trace_service.attach_episode_to_job_runs(
            job_id=job_id,
            episode_id=result.episode.id,
        )
        self._trace_service.complete(
            memory_run,
            output_summary=(
                f"Created {len(result.memory_entries)} memory entries, "
                f"{len(result.events)} events, and {len(result.scenes)} scenes."
            ),
            episode_id=result.episode.id,
        )
        consistency_checks = consistency_service.persist_report(
            universe_id=universe_id,
            timeline_id=result.episode.timeline_id,
            episode_id=result.episode.id,
            report=consistency_report,
        )

        self._job_service.update(
            job_id,
            progress=94,
            message="Finalizing agent trace",
        )
        self._job_service.update(
            job_id,
            status="completed",
            progress=100,
            message="Episode generated",
            result_data={
                "episode_id": str(result.episode.id),
                "universe_id": str(universe_id),
                "scene_count": len(result.scenes),
                "memory_entries_created": len(result.memory_entries),
                "consistency_issues": len(consistency_checks),
                "consistency_verdict": consistency_report.verdict,
            },
            completed=True,
        )
        return result

    def _historian_input(self, context: EpisodeContextPack) -> str:
        return (
            "Retrieved Episode Context Pack from database memory:\n"
            f"{context.model_dump_json(indent=2)}\n\n"
            "Validate it for story generation without inventing or removing durable facts."
        )

    def _story_input(self, context: EpisodeContextPack) -> str:
        request = context.request_prompt or "No additional user direction."
        return (
            "Episode Context Pack:\n"
            f"{context.model_dump_json(indent=2)}\n\n"
            "Episode Request:\n"
            f"{request}\n\n"
            "Generate the next episode using the context above as source of truth."
        )

    def _director_input(self, context: EpisodeContextPack, outline: EpisodeOutline) -> str:
        request = context.request_prompt or "No additional user direction."
        return (
            "Episode Context Pack:\n"
            f"{context.model_dump_json(indent=2)}\n\n"
            "Episode Request:\n"
            f"{request}\n\n"
            "Episode Outline:\n"
            f"{outline.model_dump_json(indent=2)}\n\n"
            "Write the final episode scenes and durable memory updates."
        )
