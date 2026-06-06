# Cinematic Rendering Layer

Universe Studio now includes a lightweight storyboard pipeline:

```text
Episode -> Scenes -> Shots -> Storyboard Images
```

## Backend

- `shots` stores one planned cinematic shot per scene.
- `storyboard_images` stores one persisted image payload per shot.
- `ShotPlannerService` creates deterministic shot plans from episode scenes.
- `StoryboardService` renders shots into storyboard frames.
- `OpenAIStoryboardImageProvider` uses OpenAI image generation with `gpt-image-1`.
- Rendering requires `OPENAI_API_KEY`; image-generation failures now surface as backend errors instead of persisting placeholder frames.

## APIs

```http
GET /api/v1/shots/{shot_id}
GET /api/v1/storyboards/{episode_id}
POST /api/v1/episodes/{episode_id}/storyboard/render
```

Render payload:

```json
{
  "regenerate_images": false
}
```

## Frontend

Storyboard route:

```text
/universes/[id]/episodes/[episodeId]/storyboard
```

The page displays:

- Episode summary
- Scene grouping
- Shot metadata
- Camera angle
- Duration
- Generated storyboard frame
- Provider/model status

## Video Adapter Foundation

The video generation phase is represented by provider contracts only:

- `RunwayVideoProvider`
- `VeoVideoProvider`
- `KlingVideoProvider`
- `LumaVideoProvider`

These providers intentionally return `not_implemented` until the media-generation phase begins.

## Validation

Validated locally:

- Alembic migrated to `202606070005`.
- Shot planning created persisted shots.
- Storyboard rendering created persisted frames.
- `GET /storyboards/{episode_id}` returned storyboard-ready JSON.
- `GET /shots/{shot_id}` returned shot and image data.
- Frontend storyboard route rendered successfully.
- Backend lint passed.
- Backend tests passed.
- Frontend lint passed.
- Frontend typecheck passed.
