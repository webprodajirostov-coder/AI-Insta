# AI-Insta — Product Specification

## 1. Product

AI-Insta is an account-aware AI content engine for scalable short-form content production.

The product is not a single Reel generator.

Reels are the first production format used to validate the architecture.

The system must support multiple accounts, niches, products, content pillars and production profiles without rewriting the core pipeline.

---

## 2. Primary User Flow

The target product flow is:

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
→ Validation
→ FinalAsset
→ Publish
→ Performance
→ Learning
→ Knowledge

The first usable product does not need every layer to be fully automated.

The initial priority is a reliable vertical slice from account context to validated final content.

---

## 3. Account

An Account represents a content-producing entity.

Account-specific information must be stored as configuration/data rather than embedded into core business logic.

An account may contain:

- positioning;
- audience;
- products;
- content pillars;
- tone of voice;
- content constraints;
- recurring themes;
- business context.

Adding another account should not require modifying the production pipeline.

---

## 4. Knowledge

Knowledge is reusable account context.

Knowledge provides the semantic foundation for:

- research interpretation;
- content ideas;
- content concepts;
- strategy;
- scenario generation.

Knowledge must remain independent from media production.

---

## 5. Research and ResearchInsight

Research represents collected external or internal information.

ResearchInsight is a normalized, reusable interpretation of research.

A ResearchInsight may contain:

- source;
- topic;
- observation;
- relevance;
- evidence;
- content implications.

Raw research and content intelligence must remain separate entities.

---

## 6. ContentIdea

ContentIdea represents a possible piece of content before production.

It should be possible to:

- create an idea;
- evaluate an idea;
- connect an idea to knowledge;
- connect an idea to research insights;
- develop an idea into a content concept.

An idea is not yet a production job.

---

## 7. ContentConcept

ContentConcept transforms an idea into a production-ready content direction.

A concept should define:

- core message;
- audience problem;
- content angle;
- hook direction;
- value;
- CTA direction;
- relevant knowledge;
- relevant research insights.

The concept layer connects content strategy with production.

---

## 8. ProductionProfile

ProductionProfile defines how a concept should be produced.

Initial profiles:

### SIMPLE

The currently validated production path.

### STANDARD

A richer production configuration with additional scenes and visual structure.

### ADVANCED

A more configurable production mode for complex content.

Production profiles are configuration, not separate pipeline implementations.

---

## 9. Scenario

Scenario converts a ContentConcept and ProductionProfile into executable scene instructions.

The scenario must contain the information required by downstream production stages.

For vertical short-form video, scenes may define:

- scene number;
- duration;
- voiceover text;
- visual prompt;
- overlay text;
- text position;
- music cue.

The scenario generator must remain independent from the media providers.

---

# 10. Production Pipeline

The current production pipeline is:

research
→ analysis
→ concept
→ scenario
→ audio
→ visual
→ assembly
→ output

Research and analysis may be skipped when their inputs are already available.

The production pipeline operates on an isolated job directory.

---

# 11. Stage Status Contract

Allowed stage statuses:

- pending;
- completed;
- skipped;
- failed;
- waiting.

`waiting` is currently applicable to the asynchronous visual stage.

The valid successful production sequence is:

research → analysis → concept → scenario → audio → visual → assembly → output

Research and analysis may use `skipped`.

The output stage is terminal.

A completed job must not be regenerated or mutated by a normal rerun.

---

# 12. Job Completion Contract

A job is considered successfully completed only when:

1. All required stages are completed or explicitly skipped.
2. No required stage remains pending.
3. No stage is waiting or failed.
4. The final output exists.
5. The output belongs to the current job.
6. The output passes validation.
7. The final file is located at:

`<job_dir>/output/final.mp4`

Completed is a terminal state.

---

# 13. Idempotency

The production system must be idempotent.

If a completed job is executed again:

- no new provider generation should occur;
- no new rendering should occur;
- the final output should not change;
- the job should remain completed.

Idempotency also applies to already completed individual production stages where possible.

---

# 14. Recovery

Failed or interrupted jobs must be recoverable.

Recovery should:

- preserve valid existing assets;
- continue from the first incomplete stage;
- avoid unnecessary provider calls;
- avoid regenerating valid assets;
- produce the same valid output contract.

A failed job must not require starting the entire production process from zero when valid assets already exist.

---

# 15. Provider Boundary

External media providers must remain behind explicit provider interfaces.

The current image provider is ODIRouter.

The provider lifecycle is asynchronous:

pending
→ generating / waiting
→ ready
→ completed

Provider calls must occur only at explicit generation boundaries.

Tests and recovery paths should not make external provider calls unless generation is actually required.

---

# 16. Ownership and Isolation

Every asset must belong to its current job.

Assets must not be silently reused from another job.

Job media is isolated under the job directory.

The current output contract is:

`<job_dir>/output/final.mp4`

This ownership rule applies to:

- audio;
- visual assets;
- intermediate files;
- assembly inputs;
- final output.

---

# 17. Current Validated Output

The current validated production path produces vertical video with:

- H.264 video;
- 1080×1920 resolution;
- AAC audio;
- validated final MP4 output.

The current regression fixture also validates an 8-second output.

The exact duration is not a universal product requirement; it belongs to the current production configuration.

---

# 18. Acceptance Criteria

A production feature is considered valid only when it survives more than the happy path.

Validation should cover:

### Normal path

The feature works from valid input to valid output.

### Invalid state

Invalid lifecycle transitions and malformed states are rejected.

### Recovery

A failed or interrupted job can continue from valid existing state.

### Idempotency

Repeating a completed operation does not duplicate work or mutate the result.

### Ownership

Assets cannot silently cross job boundaries.

### Provider boundary

External generation occurs only when explicitly required.

### Output validation

The final artifact satisfies the required media contract.

---

# 19. Product Versions

## V0 — Production Foundation

Completed foundation:

- job model;
- staged pipeline;
- scenario → media production;
- provider boundary;
- asset ownership;
- isolation;
- lifecycle transitions;
- recovery;
- idempotency;
- final output validation.

## V1 — Content Intelligence

Target:

Account
→ Knowledge
→ ResearchInsight
→ ContentIdea
→ ContentConcept

## V2 — End-to-End Content Generation

Target:

ContentConcept
→ ProductionProfile
→ Scenario
→ Media
→ FinalAsset

with a single high-level content creation entry point.

## V3 — Analytics

Connect published assets with performance data.

## V4 — Learning

Use performance data to generate reusable signals for future content strategy and knowledge.

---

# 20. Non-Goals

The following are not current priorities:

- building every possible content format;
- supporting every provider immediately;
- complex analytics before the content intelligence layer exists;
- automatic learning before reliable performance data exists;
- replacing configuration with hardcoded account-specific logic;
- adding production complexity before the SIMPLE path is stable.

---

# 21. Product Principle

The system should grow by adding:

- accounts;
- knowledge;
- products;
- content pillars;
- research sources;
- strategies;
- production profiles;
- providers;

without rewriting the core production pipeline.

The architecture should separate:

**what content should be produced**

from

**how that content is produced.**

Content intelligence determines the former.

Production infrastructure determines the latter.
