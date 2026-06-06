# Judge Presentation Assets

## 3-Minute Pitch

Hi, we built Universe Studio.

The tagline is: create worlds, not clips.

Most AI video tools generate isolated moments. You type a prompt, get a clip, and the next prompt starts from scratch. Characters forget what happened. Relationships do not carry forward. Timelines collapse into vibes.

Universe Studio takes a different approach. We treat the universe as the source of truth.

A user can enter an idea, script, scene, or screenplay. The system extracts characters, locations, objects, events, relationships, and world rules. That becomes persistent memory. Future episodes are generated from that memory, not from a blank prompt.

Our demo universe is Memory Market 2094, where memories are bought and sold as currency. It has eight characters, six locations, dozens of relationships, a memory graph, character dossiers, two completed episodes, and two timelines.

The core demo moment is branching. Timeline A is Maya survives. Timeline B is Maya dies. When we branch history, the future changes. Character states, relationships, events, and generated episodes diverge.

We also built an agent trace system. Judges can open an episode and see the Historian Agent retrieving memory, the Story Agent building structure, the Director Agent writing scenes, the Consistency Agent validating continuity, and Memory Update committing new facts.

The key idea is this: Universe Studio is not another generator. It is a memory and continuity engine for cinematic worlds.

## 5-Minute Pitch

Universe Studio is an AI-powered platform for persistent cinematic universes.

The problem is that current AI media tools are clip-first. They can create visually impressive moments, but they do not maintain durable story state. If a character dies in one output, the next prompt may bring them back. If two characters betray each other, the system does not naturally carry that forward. If a world has rules, those rules are not enforced across future generations.

Our thesis is that future AI storytelling needs memory first.

Universe Studio converts an idea, script, scene, or screenplay into a structured universe:

- Characters
- Goals
- Fears
- Relationships
- Locations
- Objects
- Events
- World rules
- Timelines

That universe becomes the source of truth. Every future episode is generated from memory.

The demo universe is Memory Market 2094. Memories are bought and sold as currency. The seed includes eight major characters, six locations, 48 relationships, more than 29 events, two completed episodes, and two timelines.

The most important feature is timeline branching. Timeline A is Maya survives the Vault Collapse. Timeline B is Maya dies. We branch at a historical event and regenerate the future from that changed state. The alternate future changes character states, relationship strength, event history, and the episode itself.

The second important feature is transparency. We built an Agent Trace System. When an episode is generated, the UI shows:

- Historian Agent
- Story Agent
- Director Agent
- Consistency Agent
- Memory Update

Judges can inspect what each agent retrieved, generated, validated, and committed.

Continuity is enforced by the Consistency Engine. It checks character contradictions, relationship contradictions, timeline contradictions, world rule violations, branch leakage, and impossible events before content is committed.

Our final demo is deterministic so it always works during judging. Click Demo Mode, open Memory Market 2094, inspect character dossiers, explore the memory graph, compare timelines, open episodes, and inspect agent traces.

Universe Studio is the foundation for AI-native entertainment where the product is not a prompt box. The product is a persistent world.

## Slide Outline

1. Title
   - Universe Studio
   - Create worlds, not clips.

2. Problem
   - AI tools generate isolated clips.
   - Story state is lost between prompts.

3. Insight
   - Cinematic generation needs persistent universe memory.

4. Product
   - Extract a universe from idea, script, scene, or screenplay.
   - Generate future episodes from memory.

5. Core System
   - PostgreSQL stores durable entities.
   - Neo4j stores graph relationships.
   - Agents coordinate generation and validation.

6. Demo Universe
   - Memory Market 2094
   - Memories are currency.

7. Wow Moment
   - Timeline A: Maya survives.
   - Timeline B: Maya dies.
   - Future changes consistently.

8. Agent Trace
   - Historian -> Story -> Director -> Consistency -> Memory Update.

9. Continuity
   - Consistency checks before persistence.

10. Roadmap
    - Media generation
    - Voice and image continuity
    - Collaborative writers room
    - Production-grade timeline merge tools

## One-Sentence Close

Universe Studio is a versioned memory engine for AI cinematic worlds, where every future story remembers the past.
