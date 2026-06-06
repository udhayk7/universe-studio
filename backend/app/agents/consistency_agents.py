from __future__ import annotations

from agents import Agent, RunConfig, Runner, set_default_openai_key
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.schemas.consistency import ConsistencyReport

CONSISTENCY_AGENT_INSTRUCTIONS = """
You are the Consistency Agent for Universe Studio.

Validate generated story content against universe memory before it is committed.

Check:
- Character consistency: dead characters acting alive, knowledge not learned,
  abrupt personality shifts.
- Relationship consistency: unexplained betrayal, friendship, romance, or hostility shifts.
- Timeline consistency: events before causes, deleted or altered events referenced as true.
- World rules: generated scenes must obey stored universe rules.
- Branch consistency: facts from one branch must not leak into another branch.
- Impossible events: contradictions in location, state, causality, or sequence.

Rules:
- Return only structured issues.
- Use severity low, medium, high, or critical.
- Critical means the episode should not be committed.
- Prefer precise affected entities and actionable suggested fixes.
- If the content is valid, return verdict pass and an empty issues list.
"""


class ConsistencyAgentRunner:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for consistency checks.")
        set_default_openai_key(settings.openai_api_key)
        self._run_config = RunConfig(model=settings.openai_model)
        self._agent = Agent(
            name="Consistency Agent",
            instructions=CONSISTENCY_AGENT_INSTRUCTIONS,
            output_type=ConsistencyReport,
        )

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        reraise=True,
    )
    def check(self, input_text: str) -> ConsistencyReport:
        result = Runner.run_sync(
            self._agent,
            input_text,
            run_config=self._run_config,
        )
        return ConsistencyReport.model_validate(result.final_output)
