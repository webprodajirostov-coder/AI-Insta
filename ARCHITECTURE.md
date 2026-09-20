# AI-Insta — Architecture

## 1. Product Vision

AI-Insta is a scalable AI content engine for creating short-form vertical content.

The system is not a single Reel generator. It is an account-aware content production system where account, audience, positioning, knowledge, strategy, content ideas and production profiles are data/configuration rather than hardcoded business logic.

Reels are the first production format.

The first production account is a sales psychology / self-development account used as the initial implementation and validation case.

---

## 2. Core Architecture

The target content lifecycle is:

Account
→ Knowledge
→ Research
→ ResearchInsight
→ ContentIdea
→ ContentConcept
→ ProductionProfile
→ Scenario
→ Audio / Visual
→ Assembly
→ FinalAsset
→ Analytics
→ Learning
→ Knowledge

The system must preserve separation between:

- content intelligence;
- content strategy;
- content generation;
- media production;
- output validation;
- analytics and learning.

---

## 3. Core Entities

### Account

Defines the content account and its business/content context.

Expected areas:

- identity;
- audience;
- positioning;
- products;
- tone of voice;
- CTA;
- content strategy;
- production preferences.

### Knowledge

Persistent account-specific knowledge used by the content engine.

Expected areas:

- audience pains;
- desires;
- objections;
- beliefs;
- expertise;
- products;
- content pillars.

### ResearchInsight

A structured observation derived from research.

It should contain enough context to explain:

- what was observed;
- where it came from;
- why it matters;
- what content implications it creates.

### ContentIdea

A candidate content unit derived from knowledge and research.

Expected areas:

- source insight;
- content pillar;
- hook;
- angle;
- objective.

### ContentConcept

A production-ready creative concept derived from an idea.

Expected areas:

- idea reference;
- narrative;
- format;
- production profile;
- CTA.

### ProductionProfile

Defines how a concept should be produced.

Production profiles are configuration, not hardcoded pipeline branches.

Initial profiles:

- SIMPLE;
- STANDARD;
- ADVANCED.

Current validated production path is SIMPLE.

### Scenario

A concrete production plan containing scenes, timing, voiceover/overlay requirements, visual prompts and other media instructions.

### Media Assets

Generated or resolved production assets.

Examples:

- audio;
- visuals;
- music;
- subtitles;
- future media types.

### AssemblyPlan

Defines how resolved assets are combined into the final media output.

### FinalAsset

The validated final output produced by the pipeline.

Current canonical output:

`output/final.mp4`

---

## 4. Pipeline

The current pipeline stages are:

1. research
2. analysis
3. concept
4. scenario
5. audio
6. visual
7. assembly
8. output

Research and analysis may currently be skipped for controlled production and recovery flows.

All later production stages must follow the lifecycle contract.

---

## 5. Lifecycle Contract

Allowed stage statuses:

- research: completed / skipped / failed
- analysis: completed / skipped / failed
- concept: completed / failed
- scenario: completed / failed
- audio: completed / failed
- visual: completed / waiting / failed
- assembly: completed / failed
- output: completed / failed

`pending` is the initial internal state.

`waiting` is reserved for visual provider work that has not completed.

Completed is a terminal production state.

A completed job must contain:

- valid lifecycle;
- all required stages completed or allowed skipped;
- valid assembly;
- valid final output;
- output owned by the current job;
- existing validated `output/final.mp4`.

A completed job must not be re-rendered or regenerate external media.

---

## 6. Idempotency

The pipeline must be safe to run repeatedly.

If a job is already completed:

- no media generation;
- no provider submission;
- no re-render;
- no mutation of the final output.

Repeated execution must preserve the final output byte-for-byte.

External provider calls must only happen at explicit generation boundaries.

---

## 7. Recovery

The pipeline must support recovery from:

- visual waiting;
- visual failure;
- other recoverable incomplete states.

Recovery must reuse existing valid assets where possible.

A failed or waiting job must not be silently treated as completed.

Historical invalid fixtures are not repaired merely to satisfy validators. New production logic must prevent creation of invalid states.

---

## 8. Provider Boundary

ODIRouter is the current image provider.

The provider boundary is isolated from:

- visual resolution;
- visual polling;
- assembly;
- output validation;
- job lifecycle.

A provider failure must remain visible in the job state.

Testing must distinguish:

- no-provider tests;
- controlled provider tests;
- production generation.

No provider call should occur during tests unless explicitly intended.

---

## 9. Ownership and Isolation

Each job owns its:

- `job.json`;
- media assets;
- assembly plan;
- output.

Assets and plans must not silently reference another job.

The assembly plan must resolve media paths inside the current job directory.

This is required for:

- reliable recovery;
- reproducibility;
- parallel jobs;
- safe cleanup.

---

## 10. Design Principles

### Configuration over hardcoding

Account-specific data must not be embedded into pipeline logic.

### Deterministic state transitions

Every stage transition must be explicit and validated.

### Idempotency

Repeated execution must not create duplicate external work.

### Isolation

Jobs and assets must remain independent.

### Provider abstraction

External providers must remain replaceable.

### Validation at boundaries

Invalid states should be rejected early.

### Recovery over recreation

Existing valid assets should be reused whenever possible.

### Vertical scalability

The architecture must support additional production profiles and content formats without rewriting the core pipeline.

---

## 11. Current Product Boundary

The production layer is currently more mature than the content-intelligence layer.

Validated today:

- job lifecycle;
- recovery;
- idempotency;
- audio resolution;
- visual generation boundary;
- ODIRouter integration;
- assembly;
- output validation;
- finalization;
- job and asset ownership.

The next major development focus is Content Intelligence.

---

## 12. Next Architectural Layer

The next target layer is:

Account
→ Knowledge
→ ResearchInsight
→ ContentIdea
→ ContentConcept
→ ProductionProfile
→ Scenario

This layer must be implemented without weakening the existing production pipeline.
