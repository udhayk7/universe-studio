# Agents

OpenAI Agents SDK definitions, prompts, tools, and orchestration boundaries live here.

- `definitions`: Agent declarations.
- `prompts`: Versioned prompt files or prompt builders.
- `tools`: Agent tool wrappers.
- `orchestrator`: Handoffs, guardrails, and multi-agent workflow composition.

Do not write generated world facts directly from an agent. Agents should emit structured proposals that services validate and the memory engine commits.
