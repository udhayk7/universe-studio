from __future__ import annotations

from agents import Agent, RunConfig, Runner, set_default_openai_key
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.schemas.timeline_branching import TimelineImpactAnalysis

TIMELINE_AGENT_INSTRUCTIONS = """
You are the Timeline Agent for Universe Studio.

Analyze a proposed change to story history and identify the immediate downstream impact.

Rules:
- Do not generate an episode.
- Do not create video, voice, or images.
- Treat the original timeline and branch point as source material.
- Identify affected characters, relationships, and future events.
- Build a concise alternate history summary that can be stored as branch memory.
- Do not invent unrelated lore; stay causally connected to the modified event.
"""


class TimelineAgentRunner:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for timeline analysis.")
        set_default_openai_key(settings.openai_api_key)
        self._run_config = RunConfig(model=settings.openai_model)
        self._timeline_agent = Agent(
            name="Timeline Agent",
            instructions=TIMELINE_AGENT_INSTRUCTIONS,
            output_type=TimelineImpactAnalysis,
        )

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        reraise=True,
    )
    def analyze(self, input_text: str) -> TimelineImpactAnalysis:
        result = Runner.run_sync(
            self._timeline_agent,
            input_text,
            run_config=self._run_config,
        )
        return TimelineImpactAnalysis.model_validate(result.final_output)
