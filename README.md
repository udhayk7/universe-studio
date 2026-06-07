# Universe Studio

> Create Worlds, Not Clips

Universe Studio is a persistent generative world engine that enables AI to remember characters, relationships, world state, timeline history, and alternate futures across stories.

Unlike traditional AI storytelling tools that generate isolated scenes, Universe Studio maintains a living universe where every generated event becomes part of a persistent memory system. Characters evolve, relationships change, timelines branch, and future episodes remain consistent with past events.

The platform combines world generation, character memory, episode creation, timeline branching, consistency validation, agent orchestration, and cinematic storyboard generation into a single creative environment.

---

# Overview

Current AI storytelling systems generate content.

Universe Studio generates continuity.

A creator can start with a simple idea, script, scene, or premise and automatically build an evolving universe containing:

- Persistent characters
- World lore
- Locations
- Events
- Relationships
- Timeline history
- Alternate futures

Every generated episode updates the universe memory.

Future generations remember the past.

---

# Problem Statement

Modern AI story and video generation tools suffer from a fundamental limitation:

They generate content but do not remember it.

Common issues include:

- Characters changing personality between scenes
- Relationships resetting between episodes
- Inconsistent world-building
- Forgotten events
- Broken continuity
- No timeline branching
- No alternate futures

Current workflow:

text Prompt   ↓ Generation   ↓ Done 

Every generation starts over.

There is no persistent world state.

---

# Solution

Universe Studio introduces a memory-first storytelling architecture.

Instead of generating isolated outputs, the platform creates a persistent universe that acts as the source of truth.

Workflow:

text Universe    ↓ Timeline    ↓ Episode    ↓ Memory Update    ↓ Future Generation 

Core innovations:

- Persistent world memory
- Character memory engine
- Timeline branching
- Alternate future generation
- Agent-based orchestration
- Consistency validation
- Knowledge graph visualization
- Storyboard generation

The result is an AI-native universe capable of maintaining long-term continuity.

---

# Features

### Universe Creation

Create entire universes from:

- Ideas
- Premises
- Scripts
- Scenes

---

### World Extraction

Automatically extract:

- Characters
- Locations
- Objects
- Events
- Relationships
- World rules

---

### Character Memory Engine

Maintain:

- Character traits
- Goals
- Motivations
- Relationships
- Emotional history
- Timeline-specific states

---

### Character Dossiers

Detailed character profiles including:

- Identity
- Memory
- Relationships
- Arc progression
- Timeline state

---

### Knowledge Graph Explorer

Interactive graph visualization of:

- Characters
- Events
- Locations
- Relationships
- World objects

---

### Episode Generation

Generate future episodes using:

- Existing world memory
- Character state
- Timeline history

---

### Timeline Branching

Create alternate futures from historical events.

Example:

text Timeline A Maya survives  Timeline B Maya dies 

Both futures evolve independently.

---

### Alternate Future Generation

Regenerate future storylines while preserving continuity.

---

### Consistency Engine

Detect:

- Character contradictions
- Timeline conflicts
- Relationship inconsistencies
- World-state violations

---

### Agent Trace System

Visualize agent collaboration across:

- Historian Agent
- Story Agent
- Director Agent
- Timeline Agent
- Consistency Agent

---

### Storyboard Generation

Convert generated episodes into cinematic storyboard frames using OpenAI image generation.

---

### Visual Episode Viewer

View generated episodes alongside storyboard visuals and scene breakdowns.

---

# Tech Stack

## Frontend

- Next.js 15
- TypeScript
- Tailwind CSS
- ShadCN UI
- React Flow
- Zustand
- TanStack Query
- Framer Motion

## Backend

- FastAPI
- SQLAlchemy
- Alembic
- OpenAI Agents SDK

## Database

- PostgreSQL
- pgvector
- Neo4j

## Storage

- Supabase Storage

## AI

- OpenAI Responses API
- GPT-5
- OpenAI Agents SDK
- OpenAI Image Generation

## Intended Hosting Architecture

- Vercel (Frontend)
- Railway (Backend)
- Supabase (Database & Storage)
- Neo4j Aura (Knowledge Graph)

---

# Codex / OpenAI Usage

OpenAI technologies were used extensively throughout development.

### Architecture Design

- System architecture planning
- Agent workflow design
- Memory architecture design
- Timeline branching architecture

### Database Design

- PostgreSQL schema generation
- Neo4j graph modeling
- Timeline commit architecture
- Memory engine design

### Agent Architecture

- Historian Agent
- Story Agent
- Director Agent
- Timeline Agent
- Consistency Agent

### Code Generation

- Frontend scaffolding
- Backend implementation
- API development
- Database models
- Repository patterns
- Service architecture

### API Integration

- OpenAI Responses API
- OpenAI Agents SDK
- OpenAI Image Generation

### Debugging & Testing

- Frontend debugging
- Backend debugging
- Migration validation
- API troubleshooting
- Consistency validation testing

### Documentation

- Architecture documentation
- Deployment documentation
- Validation reports
- Judge documentation

### Storyboard Generation

- Cinematic shot planning
- Storyboard prompt generation
- Visual rendering pipeline

### Prompt Engineering

- World extraction prompts
- Story generation prompts
- Consistency prompts
- Storyboard prompts

---

# Demo

### Demo Video

https://drive.google.com/file/d/14TKtCg9T5miy6Q_GiRhE5KEGDok0xbtT/view?usp=sharing

### Pitch Deck

https://drive.google.com/file/d/1Jrl83uMlEsQT-R4UjX9eH4nhW33qoMFM/view?usp=sharing


## Deployment Status

Universe Studio has been fully developed and validated in a local environment.

The following workflows were successfully verified:

- Universe creation
- World extraction
- Character memory
- Knowledge graph visualization
- Episode generation
- Timeline branching
- Alternate future generation
- Consistency validation
- Storyboard generation
- OpenAI image rendering

Due to time constraints during the hackathon submission window, public cloud deployment was not finalized before submission.

The project includes:

- Deployment documentation
- Infrastructure configuration
- Environment setup guides
- Hosting architecture specifications

The system is deployment-ready and can be hosted using the documented Vercel, Railway, Supabase, and Neo4j Aura architecture.

---

# Screenshots

## Landing Page

(Add screenshot)

## Universe Dashboard

(Add screenshot)

## Character Dossier

(Add screenshot)

## Memory Explorer

(Add screenshot)

## Timeline Branching

(Add screenshot)

## Storyboard Viewer

(Add screenshot)

## Consistency Dashboard

(Add screenshot)

---

# How to Run Locally

## Clone Repository

bash git clone <repository-url> cd universe-studio 

## Install Frontend

bash cd frontend pnpm install 

## Install Backend

bash cd ../backend  python -m venv .venv  source .venv/bin/activate  pip install -r requirements.txt 

## Configure Environment Variables

Create:

text .env frontend/.env.local backend/.env 

Configure:

env OPENAI_API_KEY=  DATABASE_URL=  NEO4J_URI= NEO4J_USER= NEO4J_PASSWORD=  SUPABASE_URL= SUPABASE_ANON_KEY= SUPABASE_SERVICE_ROLE_KEY= 

## Run Database Migrations

bash pnpm db:migrate 

## Start Backend

bash pnpm dev:backend 

## Start Frontend

bash pnpm dev:frontend 

Frontend:

text http://localhost:3000 

Backend:

text http://localhost:8000 

---

# Architecture

text User   ↓ Frontend (Next.js)   ↓ Backend (FastAPI)   ↓  ┌─────────────┬─────────────┬─────────────┐  ↓             ↓             ↓ PostgreSQL    Neo4j       OpenAI  ↓ Supabase Storage 

### Core Principle

Memory First. Generation Second.

The universe acts as the source of truth for all future generations.

---

# Future Roadmap

### Video Generation

Generate cinematic videos directly from generated episodes.

### Character Visual Consistency Engine

Maintain visual identity across scenes and episodes.

### Scene Editing

Modify scenes and regenerate affected futures.

### Partial Timeline Regeneration

Regenerate only impacted story segments after historical edits.

### Voice Generation

Character-specific voice synthesis and narration.

### Full Cinematic Production Pipeline

Transform persistent worlds into complete AI-generated films.

---

# Validation & Verification

Successfully validated:

✅ Frontend Build

✅ Backend Build

✅ Database Migrations

✅ Character Memory Engine

✅ Timeline Branching

✅ Storyboard Generation

✅ OpenAI Image Rendering

✅ Knowledge Graph Visualization

✅ Consistency Engine

✅ Agent Trace System

Validation reports and screenshots are included within the repository documentation.

---

# Team

### Team Members

- Udhay Krishna
- [Add Team Member]
- [Add Team Member]

---

## Final Statement

Traditional AI systems generate content.

Universe Studio generates evolving worlds.

Most AI systems forget.

Universe Studio remembers.

Create Worlds, Not Clips.
