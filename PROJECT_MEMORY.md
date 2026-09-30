# AI-Insta — Project Memory

## Purpose

This file is the operational entry point for continuing AI-Insta work after a chat change, environment change, or interruption.

It does **not** replace the detailed architecture/product documents. It tells us where the project is, which documents are authoritative, what has been completed, and what the next product/architectural investigation is.

## Current checkpoint

**Branch:** `feature/concept-profile-ownership`

**Latest repository checkpoint:** `92a6a8396b75056be732640cf6ae231e4ca92447` — `Test system-owned ContentConcept profile`

Previous implementation commit:
`2376286b0b313d00b8acbdcd059b8b49e92b03bf` — `Make ContentConcept production profile system-owned`

**Latest real product smoke:** Job `20260930_212719` completed successfully through the public `src.create_content` entry point with a real Research input and configured ODIRouter/Kling visual provider.

**Final output validation:**
- status: completed
- video: H.264
- resolution: 1080x1920
- duration: 8.0s
- audio: AAC
- final file: `data/jobs/20260930_212719/output/final.mp4`
- size: 345330 bytes

**Test status:** the focused regression test and full unittest suite have **not yet been rerun after the latest two commits**. The real product smoke itself passed.

### Latest architectural fix

A real smoke exposed that the LLM could return a ContentConcept `production_profile` different from the ContentIdea profile, even though the prompt instructed it to inherit the profile.

The architecture was corrected so that `production_profile` is now **system-owned** at the ContentConcept boundary:

- ContentConceptGenerator always sets `production_profile` from `ContentIdea.production.profile`.
- A provider-supplied profile is ignored/overridden.
- A regression test verifies that a deliberately wrong provider profile is replaced by the Idea profile.
- Domain validation no longer needs to reject a provider mismatch because the mismatch cannot survive the generator boundary.

This is now validated by the real end-to-end smoke: the previous ContentConcept profile mismatch no longer blocks Job creation or production.

### Current validated vertical slice

`Raw Research → ResearchInsight → ContentIdea → ContentConcept → system-owned ProductionProfile → Scenario → Job → Audio/Visual → Assembly → validated final MP4`

The real smoke also confirmed asynchronous Kling visual generation and resume/idempotent completion after the Replit session was interrupted/reloaded.

## Current execution model

`Content Creation → ResearchInsight → Idea → Concept → Scenario v2 → Job → Audio lifecycle → Visual lifecycle → AssemblyPlan v2 → Render → Validation → Completed`

Domain chain:

`Account → Knowledge → Research → ResearchInsight → ContentIdea → ContentConcept → ProductionProfile → Scenario → Scene → MediaAsset → AssemblyPlan → FinalAsset`

Execution chain:

`create_content → ContentCreationOrchestrator → Job Service → Job → PipelineOrchestrator → production stages`

## Current product boundary

The first usable product slice is now technically present as a real provider-backed end-to-end path.

The next goal is **architecture/product hardening of the first real content unit**, not adding another domain layer.

The immediate next investigation is:

1. remove `production_profile` from the LLM ContentConcept output responsibility entirely;
2. inspect the generated Job artifacts and final Reel for remaining product-quality/contract gaps;
3. reconcile PRODUCT_SPEC / ROADMAP / PROJECT_MAP with the actual implementation and remove stale checkpoint language;
4. identify the smallest real product bottleneck;
5. explicitly record what is out of scope for the next slice.

Do not add Instagram scraping/API, analytics, learning, STANDARD/ADVANCED profiles, or new orchestration layers before the current product bottleneck is identified.

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
19. ContentConcept production profile is system-owned and inherited from ContentIdea.
20. `job_creator.py` is legacy architecture and must not return.

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
