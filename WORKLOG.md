# AI-Insta — Worklog

This is the chronological record of meaningful architectural work. It records what was actually implemented and validated, not every chat message.

## 2026-09-30 — Checkpoint: Job ProductionProfile snapshot

### Goal

Ensure a Job continues production with the exact resolved ProductionProfile selected during Content Creation, instead of reloading a mutable global profile definition later.

### Finding

The previous flow stored only:

`job.production.profile = profile_id`

while Audio and Assembly could reload `data/production_profiles/<profile_id>.json`.

That allowed profile drift for an existing or waiting Job if the static profile file changed after Job creation.

### Implemented

- `job_service.create_job()` now persists the resolved ProductionProfile definition inside `job.json` as `production.profile_definition`.
- Added `load_job_production_profile()` as the canonical Job-level resolver.
- Assembly now consumes the Job profile snapshot.
- Audio now consumes the Job profile snapshot.
- Pipeline dry-run now consumes the Job profile snapshot.
- The static ProductionProfileStore remains a compatibility fallback for legacy Jobs without a snapshot.
- Snapshot/profile-id mismatch is rejected.
- Removed accidental duplicate profile resolution/imports from ContentCreationOrchestrator.

### Validation added

- Job E2E asserts the persisted profile snapshot.
- ProductionProfileStore tests verify the snapshot is authoritative.
- ProductionProfileStore tests reject snapshot/profile-id mismatch.

### Runtime checkpoint

Before this slice: `139 tests — OK`.

**This slice still requires a fresh full runtime suite in Replit.**

### Status

Implementation complete; runtime validation pending.

### Next architectural question

After the test run, inspect the remaining Job/production contract for any other execution-time data that is re-derived from mutable global sources instead of being fixed by the Job.

Do not broaden this into general refactoring. Continue only where a concrete source-of-truth violation exists.

---

## Previous completed checkpoint — canonical ProductionProfile resolution

### Goal

Prevent Content Creation callers from bypassing the canonical ContentConcept → ProductionProfile relationship by supplying an arbitrary profile file.

### Implemented

`ContentCreationOrchestrator` now:

1. creates ContentIdea;
2. creates ContentConcept;
3. loads Account and ContentConcept;
4. reads `concept.production_profile`;
5. resolves the profile through `ProductionProfileStore.resolve_for_account()`;
6. writes the resolved profile into the temporary workspace;
7. passes that resolved profile to ScenarioJobOrchestrator.

The public Content Creation API no longer accepts an arbitrary `production_profile_path`.

### Validation

`Ran 139 tests in 43.598s`

`OK`

### Status

Complete.

---

## Completed production foundation

### Job and pipeline lifecycle

- Job as execution envelope;
- explicit stage lifecycle;
- PipelineOrchestrator as canonical execution boundary;
- Job creation separate from production;
- terminal completed/failed behavior;
- explicit waiting semantics for asynchronous visual generation.

### Visual lifecycle

- READY asset reuse;
- active generation detection;
- provider submission;
- provider polling;
- completed download;
- failure propagation;
- resume from waiting;
- no regeneration of READY visual.

### Audio lifecycle

- type-aware READY asset resolution;
- music/TTS separation;
- mock music generation;
- explicit TTS failure without provider.

### AssemblyPlan v2

- Scene-aware plan;
- resolved visual/audio references;
- no generation instructions;
- path/job isolation;
- renderer consumes resolved assets only.

### Asset resolvers

- READY-only resolution;
- type/entity validation;
- same-job ownership;
- physical path validation;
- ambiguous asset rejection.

### Job stage transitions

- explicit allowed transitions;
- visual waiting → completed on resume;
- invalid backwards transitions rejected;
- output completion reserved for finalization.

### Resume and idempotency

- waiting visual Jobs resume without restarting completed work;
- completed Jobs validate and skip;
- READY assets do not trigger provider calls.

### Account → ProductionProfile compatibility

- Account declares supported complexity levels;
- unsupported profile rejected before Scenario provider call.

### Content Creation Result Contract

`ContentCreationResult` explicitly reports created/waiting/completed/failed.

---

## How to resume

Read `PROJECT_MEMORY.md`, then this file. Inspect the current unresolved contract before making changes.
