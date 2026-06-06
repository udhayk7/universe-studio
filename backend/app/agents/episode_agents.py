from __future__ import annotations

from agents import Agent, RunConfig, Runner, set_default_openai_key
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.schemas.episode_generation import EpisodeContextPack, EpisodeOutline, GeneratedEpisode

HISTORIAN_AGENT_INSTRUCTIONS = """
You are the Historian Agent for Universe Studio.

Validate and prepare the retrieved Episode Context Pack for downstream story generation.

Rules:
- The retrieved database memory is the source of truth.
- Preserve character names, relationships, events, locations, objects, goals, states, and knowledge.
- Do not invent new story facts.
- Do not write an episode.
- Do not create branches or alternate futures.
- Return the context pack in the requested structured schema.
"""

STORY_AGENT_INSTRUCTIONS = """
You are the Story Agent for Universe Studio.

Create an episode outline from the provided Episode Context Pack and Episode Request.

Rules:
- Use the memory context as source of truth.
- Do not ignore relationship history, known events, character goals, or current states.
- Do not create alternate timelines or branches.
- Do not write full scene dialogue.
- The episode must feel causally connected to existing memory.
- Include at least three concrete continuity references.
- Use existing characters and locations whenever possible.
- Create character pressure and development, not just plot mechanics.
"""

DIRECTOR_AGENT_INSTRUCTIONS = """
You are the Director Agent for Universe Studio.

Convert the episode outline into cinematic scenes with dialogue and memory updates.

Rules:
- Preserve the outline's causality and continuity references.
- Every scene must have a concrete location, characters, description, dialogue, and outcome.
- Dialogue should reveal motivation, relationship tension, or new knowledge.
- Do not introduce timeline branching, alternate futures, or video generation.
- Memory updates must be durable facts that future episodes can depend on.
- Relationship changes must be grounded in scene outcomes.
- Character state changes must reflect the emotional and physical consequences of the episode.
"""


class EpisodeAgentRunner:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for episode generation.")
        set_default_openai_key(settings.openai_api_key)
        self._run_config = RunConfig(model=settings.openai_model)
        self._historian_agent = Agent(
            name="Historian Agent",
            instructions=HISTORIAN_AGENT_INSTRUCTIONS,
            output_type=EpisodeContextPack,
        )
        self._story_agent = Agent(
            name="Story Agent",
            instructions=STORY_AGENT_INSTRUCTIONS,
            output_type=EpisodeOutline,
        )
        self._director_agent = Agent(
            name="Director Agent",
            instructions=DIRECTOR_AGENT_INSTRUCTIONS,
            output_type=GeneratedEpisode,
        )

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        reraise=True,
    )
    def run_historian_agent(self, input_text: str) -> EpisodeContextPack:
        result = Runner.run_sync(
            self._historian_agent,
            input_text,
            run_config=self._run_config,
        )
        return EpisodeContextPack.model_validate(result.final_output)

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        reraise=True,
    )
    def run_story_agent(self, input_text: str) -> EpisodeOutline:
        result = Runner.run_sync(
            self._story_agent,
            input_text,
            run_config=self._run_config,
        )
        return EpisodeOutline.model_validate(result.final_output)

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        reraise=True,
    )
    def run_director_agent(self, input_text: str) -> GeneratedEpisode:
        result = Runner.run_sync(
            self._director_agent,
            input_text,
            run_config=self._run_config,
        )
        return GeneratedEpisode.model_validate(result.final_output)
