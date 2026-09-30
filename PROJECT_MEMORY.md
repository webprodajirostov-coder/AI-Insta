# AI-Insta — Project Memory

## Purpose

This file is the operational entry point for continuing AI-Insta work after a chat change, environment change, or interruption.

It does **not** replace the detailed architecture/product documents. It tells us where the project is, which documents are authoritative, what has been completed, and what the next architectural investigation is.

## Current checkpoint

**Branch:** `feature/scenario-generation-orchestration`

**Latest repository checkpoint:** `1f9045b` — `Record audio profile snapshot checkpoint`

**Runtime validation:** `143 tests — OK`

The current architectural slice is complete:

`ContentIdea → ContentConcept → canonical ProductionProfile → Scenario → Job → Production Pipeline`

The Job now persists the resolved ProductionProfile definition as an execution snapshot, and audio execution consumes that snapshot instead of re-reading the mutable global profile store.

The canonical production-profile resolution is now owned by `ContentCreationOrchestrator` through `ProductionProfileStore.resolve_for_account()`. Callers no longer choose an arbitrary profile path.

## Current execution model

`Content Creation → Job → Scenario v2 → Audio lifecycle → Visual lifecycle → AssemblyPlan v2 → Render → Validation → Completed`

Domain chain:

`ContentIdea → ContentConcept → ProductionProfile → Scenario → Scene → MediaAsset → AssemblyPlan → FinalAsset`

Execution chain:

`ContentCreationOrchestrator → Job Service → Job → PipelineOrchestrator → production stages`

## Next action

Inspect and close the remaining legacy compatibility path around the Job ProductionProfile snapshot.

Current execution-time consumers use `load_job_production_profile()` and therefore consume the persisted `job.production.profile_definition` snapshot. The only remaining static lookup is the compatibility fallback for older Jobs that have `production.profile` but no `production.profile_definition`.

Before changing code, inspect all tests/fixtures that still create Jobs without the snapshot.

Question to answer:

> Can the current Job contract now require `production.profile_definition` unconditionally, with the static profile store removed from execution-time fallback?

If yes, make that the next smallest architectural slice. Do not refactor unrelated pipeline code.

## Architectural invariants

1. Scenario does not create MediaAsset.
2. MediaAsset does not modify Scenario.
3. ProductionProfile describes production capability/constraints, not specific content.
4. Scenario contains concrete production decisions.
5. AssemblyPlan contains resolved execution instructions.
6. Renderer consumes AssemblyPlan and resolved assets only.
7. Renderer does not generate assets.
8. Job is an execution envelope, not a domain entity.
9. Creating Job does not start production.
10. Production starts through PipelineOrchestrator.
11. READY assets are reusable and must not be regenerated.
12. generation_required=true + no asset → generation lifecycle.
13. generation_required=false + no asset → failure.
14. Assembly consumes READY assets only.
15. FinalAsset appears only after Assembly + output validation.
16. Account-supported production profiles must be validated before Scenario provider generation.
17. `job_creator.py` is legacy architecture and must not return.

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
| `docs/DEVELOPMENT_WORKFLOW.md` | How assistant and user divide design/edit/runtime responsibilities |

When documents overlap, use the more specific document for the specific question. `PROJECT_MEMORY.md` only records the current checkpoint and points to the detailed source.

## Working protocol

1. Read this file first.
2. Read `WORKLOG.md` for the latest completed slices.
3. Read the relevant section of `PROJECT_MAP.md` and `ROLES_AND_BOUNDARIES.md`.
4. Inspect the actual current code before designing the next change.
5. Design the smallest architectural slice that closes a real contract.
6. Implement through GitHub.
7. Inspect the diff.
8. User runs runtime tests in Replit.
9. Record the result in `WORKLOG.md` and update this checkpoint.
10. Only then move to the next slice.

## Environment continuity

Replit/Codespace is a runtime boundary, not the project source of truth.

The GitHub repository plus the documents listed above are the durable project state. A new chat should resume from `PROJECT_MEMORY.md`, not from assumptions about the previous conversation.
