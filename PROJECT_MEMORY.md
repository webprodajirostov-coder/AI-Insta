# AI-Insta — Project Memory

## Purpose

This file is the operational entry point for continuing AI-Insta work after a chat change, environment change, or interruption.

It does **not** replace the detailed architecture/product documents. It tells us where the project is, which documents are authoritative, what has been completed, and what the next product/architectural investigation is.

## Current checkpoint

**Branch:** `feature/scenario-generation-orchestration`

**Latest repository checkpoint:** `64904a8` — `Fix ResearchInsight generator import in E2E test`

**Runtime validation:** `155 tests — OK`

The current validated vertical slice is:

`Raw Research → ResearchInsight → ContentIdea → ContentConcept → ProductionProfile → Scenario → Job → Audio/Visual → Assembly → validated final MP4`

The latest E2E test confirms this full path, including persistence of ResearchInsight context inside the Job.

The Job persists the resolved ProductionProfile definition as an execution snapshot. Execution-time consumers use that Job snapshot rather than re-resolving mutable global production profiles.

## Current execution model

`Content Creation → ResearchInsight → Idea → Concept → Scenario v2 → Job → Audio lifecycle → Visual lifecycle → AssemblyPlan v2 → Render → Validation → Completed`

Domain chain:

`Account → Knowledge → Research → ResearchInsight → ContentIdea → ContentConcept → ProductionProfile → Scenario → Scene → MediaAsset → AssemblyPlan → FinalAsset`

Execution chain:

`create_content → ContentCreationOrchestrator → Job Service → Job → PipelineOrchestrator → production stages`

## Current product boundary

The first usable product slice is now technically present as a controlled end-to-end path.

The next goal is **product validation**, not another domain layer:

1. provide a real Research input;
2. generate ResearchInsights through the configured LLM provider;
3. generate exactly one ContentIdea;
4. generate exactly one ContentConcept;
5. resolve the supported ProductionProfile;
6. generate Scenario;
7. create the Job;
8. run the production pipeline;
9. obtain a validated vertical final MP4.

Do not add Instagram scraping/API, analytics, learning, STANDARD/ADVANCED profiles, or new orchestration layers before this product smoke path is validated.

Research input should remain source-agnostic. Instagram/competitor collectors can be added later behind the existing Research contract.

## Next action

Run a real product smoke test through:

`python -m src.create_content --account ... --research ...`

using a valid Research JSON input and the configured LLM/provider environment.

Inspect the resulting Job and final MP4. Record any runtime/provider issues as the next concrete product gaps.

If the real smoke path succeeds, make the next checkpoint around the first usable content unit rather than expanding the architecture.

## Architectural invariants

1. Scenario does not create MediaAsset.
2. MediaAsset does not modify Scenario.
3. ProductionProfile describes production capability/constraints/defaults, not specific content.
4. Scenario contains concrete production decisions.
5. AssemblyPlan contains resolved execution instructions.
6. Renderer consumes AssemblyPlan and resolved assets only.
7. Renderer does not generate assets.
8. Job is an execution envelope, not a domain entity.
9. Creating a Job does not start production.
10. Production starts through PipelineOrchestrator.
11. READY assets are reusable and must not be regenerated.
12. generation_required=true + no asset → generation lifecycle.
13. generation_required=false + no asset → failure.
14. Assembly consumes READY assets only.
15. FinalAsset appears only after Assembly + output validation.
16. Account-supported production profiles are validated before Scenario provider generation.
17. Job execution consumes the persisted ProductionProfile snapshot.
18. ResearchInsight references must be preserved and validated through Job creation.
19. `job_creator.py` is legacy architecture and must not return.

## Document catalog

### Operational documents

| Document | Purpose | Authority |
|---|---|---|
| `PROJECT_MEMORY.md` | Entry point, current checkpoint, resume instructions, document catalog | Current operational state |
| `WORKLOG.md` | Chronological record of completed work, decisions, tests and checkpoints | Historical project record |
| `PROJECT_MAP.md` | Current system map, entities, execution flow and boundaries | Architectural navigation |
| `ROLES_AND_BOUNDARIES.md` | Responsibilities and forbidden cross-layer behavior | Boundary contract |

### Existing source-of-truth documents

| Document | Purpose |
|---|---|
| `ARCHITECTURE.md` | Detailed architectural principles and production lifecycle |
| `PRODUCT_SPEC.md` | Product-level requirements and acceptance criteria |
| `ROADMAP.md` | Product phases and intended development direction |
| `docs/DEVELOPMENT_WORKFLOW.md` | How assistant and user divide design/runtime responsibilities |

When documents overlap, use the more specific document for the specific question. `PROJECT_MEMORY.md` only records the current checkpoint and points to the detailed source.

## Working protocol

1. Read this file first.
2. Read `WORKLOG.md` for the latest completed slices.
3. Read the relevant section of `PROJECT_MAP.md` and `ROLES_AND_BOUNDARIES.md`.
4. Inspect the actual current code before designing the next change.
5. Design the smallest architectural/product slice that closes a real gap.
6. Implement through GitHub.
7. Inspect the diff.
8. User runs runtime tests in Replit/Codespace.
9. Record the result in `WORKLOG.md` and update this checkpoint.
10. Only then move to the next slice.

## Environment continuity

Replit/Codespace is a runtime boundary, not the project source of truth.

The GitHub repository plus the documents listed above are the durable project state. A new chat should resume from `PROJECT_MEMORY.md`, not from assumptions about the previous conversation.
