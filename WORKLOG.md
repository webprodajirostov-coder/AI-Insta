# AI-Insta — Worklog

## 2026-09-30 — Checkpoint: Job ProductionProfile snapshot at audio execution

### Goal

Close the remaining execution-time configuration leak in the audio stage: after Job creation, audio generation must use the persisted Job ProductionProfile snapshot rather than re-reading the mutable global profile store.

### Implemented

Audio execution now loads the ProductionProfile through `load_job_production_profile()` in:

- `src/audio_generator.py`;
- `generate_audio()`;
- `generate_mock_music()`.

The previous runtime path from Scenario → `data/production_profiles/{profile}.json` was removed from audio generation.

Regression coverage mutates the global `simple.json` after the Job snapshot is created and verifies that both music generation paths still follow the Job snapshot.

### Validation

Focused audio suite:

`Ran 4 tests in 1.376s`

`OK`

Full regression suite:

`Ran 143 tests in 47.084s`

`OK`

The full end-to-end pipeline also reached a completed Job with validated H.264/AAC 1080x1920 output.

### Architectural inspection after the slice

Current production execution paths inspected:

- Audio reads the Job ProductionProfile snapshot.
- Assembly reads the Job ProductionProfile snapshot.
- Pipeline audio stage and dry-run read the Job ProductionProfile snapshot.
- Visual execution consumes Scenario scene decisions and does not resolve ProductionProfile.
- Scenario/Job creation uses the already resolved profile workspace artifact; it does not re-resolve a global profile at execution time.

The only remaining static-profile lookup is the explicit compatibility fallback inside `load_job_production_profile()` for older Jobs that do not contain `production.profile_definition`. This is a legacy compatibility path, not the current Job contract.

### Checkpoint

**Status: complete.**

### Next architectural question

Decide whether to close the legacy compatibility fallback and make the Job ProductionProfile snapshot mandatory for all execution-time consumers.

Before changing code, inspect all tests/fixtures that still create Jobs with only `production.profile` and no `production.profile_definition`.

The intended contract is:

`Job creation resolves ProductionProfile once → Job persists the snapshot → all execution stages consume only that snapshot`.

Do not refactor unrelated pipeline code until this contract is closed.

---

This is the chronological record of meaningful architectural work. It records what was actually implemented and validated, not every chat message.

## 2026-09-30 — Checkpoint: canonical ProductionProfile resolution

### Goal

Prevent Content Creation callers from bypassing the canonical ContentConcept → ProductionProfile relationship by supplying an arbitrary profile file.

### Implemented

`ContentCreationOrchestrator` now:

1. creates ContentIdea;
2. creates ContentConcept;
3. loads the Account and ContentConcept;
4. reads `concept.production_profile`;
5. resolves the profile through `ProductionProfileStore.resolve_for_account()`;
6. writes the resolved profile into the job workspace;
7. passes that resolved profile to ScenarioJobOrchestrator.

The public Content Creation API no longer accepts an arbitrary `production_profile_path`.

The CLI no longer manually derives the profile path from Account baseline settings.

### Validation

Regression suite:

`Ran 139 tests in 43.598s`

`OK`

Additional regression coverage verifies that an Account supporting only `simple` rejects a ContentConcept requesting `standard` before the Scenario provider is called.

### Checkpoint

**Status: complete.**

### Next architectural question

Inspect `ScenarioJobOrchestrator` as the bridge between resolved Scenario/Profile and Job.

Verify that it:

- consumes the exact generated Scenario;
- consumes the resolved ProductionProfile;
- does not re-resolve the profile;
- does not regenerate the Scenario;
- does not derive a conflicting profile from Account;
- creates the Job without starting Production;
- preserves Scenario/Profile identity and ownership in Job inputs.

No code change should be made until this contract is inspected.

---

## Previous completed production foundation

### Job and pipeline lifecycle

Established:

- Job as execution envelope;
- explicit stage lifecycle;
- PipelineOrchestrator as canonical execution boundary;
- Job creation separate from production;
- terminal completed/failed behavior;
- explicit waiting semantics for asynchronous visual generation.

### Visual lifecycle

Established:

- READY asset reuse;
- active generation detection;
- provider submission;
- provider polling;
- completed download;
- failure propagation;
- no regeneration of READY visual;
- resume from waiting.

### Audio lifecycle

Established:

- type-aware READY asset resolution;
- music and TTS separation;
- mock music generation for controlled production;
- explicit failure when TTS is enabled without a provider.

### AssemblyPlan v2

Established:

- Scene-aware plan;
- concrete resolved visual/audio asset references;
- no generation instructions in AssemblyPlan;
- path/job isolation;
- renderer consumes resolved assets only.

### Asset resolvers

Established:

- READY-only resolution;
- entity/type validation;
- same-job ownership;
- physical path existence;
- path containment;
- ambiguous asset rejection.

### Job stage transitions

Established:

- explicit allowed transitions;
- visual waiting → completed on resume;
- rejection of invalid backwards transitions;
- output completion reserved for finalization.

### Resume and idempotency

Established:

- waiting visual job resumes without restarting completed work;
- completed jobs validate and return without re-rendering;
- provider calls are not repeated for already READY assets.

### Account → ProductionProfile compatibility

Established:

- Account declares supported complexity levels;
- unsupported profile is rejected;
- rejection occurs before Scenario provider call;
- backward compatibility retained when supported-complexity list is absent.

### Content Creation Result Contract

Established:

`ContentCreationResult` explicitly reports:

- created;
- waiting;
- completed;
- failed.

The high-level content creation entry point maps Job state to this result rather than returning only a path.

---

## Current architecture invariants

- Scenario does not create MediaAsset.
- MediaAsset does not modify Scenario.
- ProductionProfile describes capability/constraint/default.
- Scenario contains concrete production decisions.
- AssemblyPlan contains resolved execution instructions.
- Renderer consumes resolved assets only.
- Job creation does not start production.
- PipelineOrchestrator owns production execution.
- READY assets are reused.
- generation_required=false + no asset is failure.
- Assembly consumes READY assets only.
- FinalAsset exists only after validated output.
- Unsupported Account/Profile combinations fail before provider generation.
- Legacy `job_creator.py` stays outside the current architecture.

## How to resume

When starting a new chat:

1. Read `PROJECT_MEMORY.md`.
2. Read the latest section of `WORKLOG.md`.
3. Inspect the files named under **Next architectural question**.
4. Compare the implementation with `PROJECT_MAP.md` and `ROLES_AND_BOUNDARIES.md`.
5. Continue only from the first unresolved contract.

The project should never restart from the beginning merely because the chat or runtime environment changed.
