## 2026-09-30 — Checkpoint: System-owned ContentConcept ProductionProfile + second real E2E

### Goal

Close the ownership leak where the LLM could return a ContentConcept `production_profile` that differed from the canonical ContentIdea profile, then validate the fix through the real product entry point.

### Implemented

Branch:

`feature/concept-profile-ownership`

Commits:

- `2376286b0b313d00b8acbdcd059b8b49e92b03bf` — `Make ContentConcept production profile system-owned`
- `92a6a8396b75056be732640cf6ae231e4ca92447` — `Test system-owned ContentConcept profile`

The ContentConcept generator now unconditionally inherits `production_profile` from `ContentIdea.production.profile`. Provider output cannot override this system-owned constraint.

Regression coverage now verifies that a provider returning an intentionally wrong profile is overridden by the Idea profile.

### Real product smoke

Command:

`python -m src.create_content --account sales_psychology_001 --research data/research/sales_psychology_001/research_smoke_001.json`

Job:

`20260930_212719`

Initial run correctly:

- generated mock music;
- submitted one real ODIRouter/Kling visual generation request;
- persisted the visual as `generating`;
- returned `CONTENT CREATION: WAITING`.

After the Replit session was reloaded, the Job was resumed with:

`python3 -m src.job_pipeline data/jobs/20260930_212719`

The pipeline detected the already completed Job and validated the persisted final output rather than creating another production run.

### Final validation

- Job status: `completed`
- output validation: `OK`
- video: H.264
- resolution: 1080x1920
- duration: 8.0s
- audio: AAC
- final file: `data/jobs/20260930_212719/output/final.mp4`
- size: 345330 bytes

### Architectural conclusion

The ContentConcept production profile mismatch that previously blocked real smoke is closed.

The canonical ownership is now:

`ContentIdea.production.profile → ContentConcept.production_profile`

The provider is responsible for semantic/creative ContentConcept content, while the system owns production constraints.

The real smoke proves that this boundary survives the full path into Scenario/Job and does not prevent real production.

### Test status

The focused ContentConcept test and the full unittest suite were **not rerun after the latest two commits**. The real product smoke passed.

### Next step

Before implementing another feature:

1. run the focused ContentConcept tests and full unittest suite on this branch;
2. inspect the current LLM ContentConcept provider contract;
3. remove `production_profile` from the provider's requested creative output responsibility so the LLM is no longer asked to generate a system-owned field;
4. inspect the generated Job/final Reel for the smallest remaining product-quality or contract gap;
5. reconcile stale documentation and record the next explicit slice.

Do not add Instagram scraping/API, analytics, learning, STANDARD/ADVANCED profiles, or another orchestration layer yet.

---

## 2026-09-30 — Checkpoint: First real provider-backed content unit

### Goal

Validate the completed vertical slice through the public content-creation entry point with a real Research input and configured external providers, rather than only controlled test doubles.

### Runtime smoke

Command:

python -m src.create_content --account sales_psychology_001 --research data/research/sales_psychology_001/research_smoke_001.json

The initial run created Job 20260930_145833 and correctly stopped at visual waiting after submitting a real ODIRouter/Kling task.

Resume was performed through:

python -m src.job_pipeline data/jobs/20260930_145833

The existing visual asset was polled rather than regenerated. The Job then completed Assembly, rendering and output validation.

### Result

Validated real path:

Raw Research → ResearchInsight → ContentIdea → ContentConcept → ProductionProfile → Scenario → Job → Audio → Kling Visual → resume/poll → Assembly → Render → Output validation

Final output:

- Job: data/jobs/20260930_145833
- status: completed
- video: H.264
- resolution: 1080x1920
- duration: 8.0s
- audio: AAC
- final file: output/final.mp4

This is the first real provider-backed validation of the complete product path.

### Architectural conclusions

- The public create_content entry point can drive a real content unit from Research to final asset.
- ResearchInsight generation is connected to downstream content intelligence and Job validation.
- ContentConcept production-profile inheritance is enforced at the provider boundary rather than by weakening domain validation.
- Job ProductionProfile snapshot remains authoritative during execution.
- Visual generation has real asynchronous waiting/resume behavior.
- Existing generating/READY visual state is reused; no duplicate visual generation was created during resume.
- Assembly receives resolved READY assets only.
- Rendering remains outside asset generation.
- The current production architecture does not need another orchestration layer to complete this path.

### What is proven vs. what remains

Proven by real smoke:

- external LLM-backed ResearchInsight generation;
- downstream Idea/Concept/Scenario/Job creation;
- real ODIRouter/Kling visual generation;
- waiting/resume/poll behavior;
- Assembly → render → output validation;
- completed Job terminal state.

Still primarily test/fixture-level:

- broader Research source ingestion and collectors;
- content-quality evaluation of generated Ideas/Concepts/Scenarios;
- repeated multi-account/product usage at product scale;
- STANDARD/ADVANCED production profiles;
- publish, analytics and learning layers.

### Next step

Do an architecture/product checkpoint against the first real content unit before implementing another feature. Inspect the generated Job artifacts and final Reel, reconcile stale documentation, identify the smallest real product bottleneck, and explicitly keep later roadmap layers out of scope.

---

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
