# AI-Insta — Roles and Boundaries

## 1. Why this document exists

The project is developed with a deliberate separation between architecture/design work and runtime verification.

The goal is to prevent:
- duplicate sources of truth;
- orchestration logic leaking into domain entities;
- production stages bypassing PipelineOrchestrator;
- runtime environment becoming the project memory.

## 2. Human / assistant roles

### Assistant — architect + implementer

The assistant is responsible for:

- repository inspection;
- architecture analysis;
- identifying the next real contract gap;
- designing changes;
- editing repository code;
- creating commits/branches/PRs when appropriate;
- reviewing diffs;
- designing tests;
- interpreting runtime test results;
- maintaining project documentation/checkpoints.

The assistant should not invent runtime results.

### User — runtime operator + project partner

The user is responsible for:

- running runtime-dependent commands in Replit/Codespace;
- running unittest/pytest suites;
- running ffmpeg/MoviePy checks;
- supplying real provider credentials when needed;
- executing real external API/provider calls;
- returning command output;
- helping validate product intent and priorities.

The user should not need to inspect ordinary source files manually when GitHub/project tooling can provide them.

## 3. Domain boundaries

### Account

Responsible for account context and supported production capabilities.

Must not contain pipeline execution logic.

### Knowledge

Responsible for reusable account knowledge.

Must not generate media or mutate Jobs.

### ContentIdea

Responsible for a candidate content direction.

Must not create a Job or invoke media providers.

### ContentConcept

Responsible for turning an idea into a production-ready creative direction.

Must not own media generation or pipeline execution.

### ProductionProfile

Responsible for production capabilities, constraints and defaults.

Must not contain content-specific scene decisions.

### ProductionProfileStore

Responsible for canonical profile loading and Account compatibility validation.

Must be the canonical resolver when a ContentConcept selects a profile.

### Scenario

Responsible for concrete production decisions at scene level.

Must not create MediaAssets.

### ScenarioGenerator

Responsible for generating a Scenario from validated content context and ProductionProfile.

Must not call media providers.

### ScenarioJobOrchestrator

Responsible for bridging a generated Scenario + resolved ProductionProfile into a Job.

Must not become a second profile resolver or second Scenario generator.

### Job Service

Responsible for creating/loading/updating the Job execution envelope.

Creating a Job must not start production.

### PipelineOrchestrator

Responsible for production execution and stage transitions.

It is the canonical production execution boundary.

### Media lifecycle components

Responsible for asset generation, polling, resolution and readiness.

They must not rewrite Scenario semantics.

### Asset Resolver

Responsible for resolving existing READY assets within the current Job.

Must enforce Job ownership and physical path isolation.

### AssemblyPlan

Responsible for resolved execution instructions.

It may contain concrete asset IDs/paths, but must not contain generation instructions.

### Renderer / Assembly

Responsible for combining resolved inputs.

Must not generate assets or call external providers.

### Finalizer / Output Validation

Responsible for validating and completing the terminal output contract.

Output completion must not be faked by ordinary stage mutation.

## 4. Cross-layer rules

1. Lower layers consume explicit contracts from upper layers.
2. No component silently derives a second source of truth for an already resolved decision.
3. Generation and resolution are different operations.
4. Domain entities do not execute production.
5. Job creation and production execution remain separate.
6. Provider calls happen only at explicit generation boundaries.
7. READY assets are authoritative and reusable.
8. Assembly consumes resolved assets only.
9. Final completion requires output validation.
10. Legacy `job_creator.py` must not return.

## 5. Development boundary

The normal development loop is:

```
inspect
→ design
→ implement
→ diff review
→ runtime test
→ analyze
→ checkpoint
```

A test failure caused by a test fixture or implementation mistake is fixed at the appropriate layer; it is not used as a reason to weaken an architectural contract.

## 6. Change discipline

Before changing a contract:

- search all references;
- inspect producers and consumers;
- inspect tests;
- identify ownership;
- define valid and invalid states;
- implement the smallest coherent slice;
- add regression coverage;
- run the runtime suite;
- update the project checkpoint.

Do not refactor stable code merely because a cleaner alternative exists.
