# AI-Insta — Project Memory

## Purpose

Operational entry point for continuing AI-Insta after a chat or runtime-environment change.

## Current checkpoint

**Branch:** `feature/scenario-generation-orchestration`

**Runtime checkpoint before current slice:** `139 tests — OK`

**Current slice:** Job ProductionProfile snapshot.

The previous architectural slice established:

`ContentIdea → ContentConcept → canonical ProductionProfile → Scenario → Job`

The current slice closes the next source-of-truth boundary:

`resolved ProductionProfile → Job snapshot → production stages`

### Current implementation state

A newly created Job now persists the exact resolved ProductionProfile definition in:

`job.json → production.profile_definition`

Assembly, Audio and pipeline dry-run consume that snapshot. Legacy Jobs without the snapshot may fall back to the static profile store.

Snapshot/profile-id mismatch is rejected.

### Runtime status

**Implementation complete. Fresh full test suite is still required.**

### Next step

User runs:

```
git pull origin feature/scenario-generation-orchestration
python -m unittest discover -s tests -v
```

If the suite is green, record the result here and in `WORKLOG.md`.

Then inspect whether any other execution-time production configuration is re-derived from mutable global files instead of being fixed by the Job.

## Current execution model

`Content Creation → Job → Scenario v2 → Audio lifecycle → Visual lifecycle → AssemblyPlan v2 → Render → Validation → Completed`

## Domain chain

`ContentIdea → ContentConcept → ProductionProfile → Scenario → Scene → MediaAsset → AssemblyPlan → FinalAsset`

## Critical invariants

1. Scenario does not create MediaAsset.
2. MediaAsset does not modify Scenario.
3. ProductionProfile describes production capability/constraints/defaults.
4. Scenario contains concrete production decisions.
5. AssemblyPlan contains resolved execution instructions.
6. Renderer consumes AssemblyPlan and resolved assets only.
7. Renderer does not generate assets.
8. Job is an execution envelope, not a domain entity.
9. Creating Job does not start production.
10. Production starts through PipelineOrchestrator.
11. READY assets are reusable.
12. generation_required=true + no asset → generation lifecycle.
13. generation_required=false + no asset → failure.
14. Assembly consumes READY assets only.
15. FinalAsset appears only after Assembly + output validation.
16. Account/Profile compatibility is validated before Scenario provider generation.
17. A Job uses its persisted ProductionProfile snapshot for execution.
18. `job_creator.py` is legacy architecture and must not return.

## Document catalog

- `PROJECT_MEMORY.md` — current checkpoint and resume instructions.
- `WORKLOG.md` — completed work and architectural history.
- `PROJECT_MAP.md` — system/domain/execution map.
- `ROLES_AND_BOUNDARIES.md` — responsibilities and forbidden dependencies.
- `ARCHITECTURE.md` — detailed architectural principles.
- `PRODUCT_SPEC.md` — product requirements.
- `ROADMAP.md` — product direction.
- `docs/DEVELOPMENT_WORKFLOW.md` — development procedure.

The continuity documents complement the existing source-of-truth documents; they do not replace them.

## Development loop

`inspect → design → implement → diff review → runtime test → checkpoint → next contract`

The project must not restart from the beginning because the chat or runtime environment changes.
