# AI-Insta — Worklog

## 2026-09-30 — Checkpoint: Research → ResearchInsight → Content → FinalAsset vertical slice

### Goal

Close the first product-level vertical slice from raw research input through Content Intelligence, Scenario, Job and validated final Reel output.

### Implemented

ResearchInsight generation and persistence are now connected to Content Creation.

The current flow is:

`Raw Research → ResearchInsight → ContentIdea → ContentConcept → ProductionProfile → Scenario → Job → Pipeline → final.mp4`

Implemented/validated:

- Research records are validated against Account.
- ResearchInsight is generated from supplied Research and preserves the source Research reference.
- ContentIdea consumes persisted ResearchInsight data and writes `research_refs`.
- ContentConcept consumes the same ResearchInsight context and preserves `research_refs`.
- Job creation receives ResearchInsight context and validates those references before Job creation.
- Supplied ResearchInsight context is persisted under the Job.
- The Content Creation entry point can accept raw Research and invoke ResearchInsight generation automatically.
- The E2E test reaches a completed validated final MP4 while starting from raw Research.

### Validation

Focused E2E:

`Ran 1 test in 27.850s`

`OK`

Full regression suite:

`Ran 155 tests in 52.052s`

`OK`

### Architectural result

The first controlled end-to-end content slice is complete.

The remaining question is no longer whether the layers can be connected. It is whether the public entry point can produce a real content unit with configured external providers and a real Research input.

### Next step

Run a real product smoke test through:

`python -m src.create_content --account ... --research ...`

Use a valid Research JSON input and the configured LLM/provider environment.

Do not add source-specific collectors, analytics, learning, or additional production profiles before this smoke path is validated.

---

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

Full regression suite at that checkpoint:

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

---

This is the chronological record of meaningful architectural work. It records what was actually implemented and validated, not every chat message.

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
- Job execution consumes the persisted ProductionProfile snapshot.
- ResearchInsight references are preserved and validated through Job creation.
- Legacy `job_creator.py` stays outside the current architecture.

## How to resume

When starting a new chat:

1. Read `PROJECT_MEMORY.md`.
2. Read the latest section of `WORKLOG.md`.
3. Inspect the files named under **Next step**.
4. Compare the implementation with `PROJECT_MAP.md` and `ROLES_AND_BOUNDARIES.md`.
5. Continue only from the first unresolved product/architecture gap.

The project should never restart from the beginning merely because the chat or runtime environment changed.
