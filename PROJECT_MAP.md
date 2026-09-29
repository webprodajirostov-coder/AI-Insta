# AI-Insta — Project Map

## 1. Product map

```
Account
  ↓
Knowledge
  ↓
Research / ResearchInsight
  ↓
ContentIdea
  ↓
ContentConcept
  ↓
ProductionProfile
  ↓
Scenario
  ↓
Audio / Visual
  ↓
AssemblyPlan
  ↓
FinalAsset
  ↓
Analytics
  ↓
Learning
  ↺ Knowledge
```

The first production format is vertical short-form video. The architecture is intended to remain account-aware and configuration-driven.

## 2. Current maturity

### Validated production foundation

- Job lifecycle
- PipelineOrchestrator
- Visual lifecycle
- Audio resolution/lifecycle
- Asset ownership and isolation
- AssemblyPlan v2
- Rendering
- Output validation/finalization
- Waiting/resume behavior
- Idempotent completed-job reruns

### Content intelligence currently implemented

- Account
- Knowledge input
- ContentIdea generation
- ContentConcept generation
- ContentConcept → ProductionProfile compatibility validation
- Canonical ProductionProfile resolution
- Scenario generation
- ContentCreationOrchestrator
- Scenario → Job orchestration

### Planned / not yet the current focus

- ResearchInsight automation
- richer strategy engine
- STANDARD profile
- ADVANCED profile
- analytics
- learning loop

## 3. Execution map

```
create_content
    ↓
ContentCreationOrchestrator
    ├─ ContentIdeaGenerator
    ├─ ContentConceptGenerator
    ├─ ProductionProfileStore
    └─ ScenarioJobOrchestrator
             ↓
          Job Service
             ↓
            Job
             ↓
    PipelineOrchestrator
      ├─ Audio
      ├─ Visual
      ├─ Assembly
      └─ Output / Validation
```

Content Creation is a high-level orchestration boundary. It prepares content artifacts and creates the execution envelope. It does not duplicate the production pipeline.

## 4. Domain ownership

| Entity | Owns |
|---|---|
| Account | Account-specific identity, audience, strategy and production support |
| Knowledge | Reusable account knowledge |
| ContentIdea | Candidate content direction |
| ContentConcept | Production-ready creative direction |
| ProductionProfile | Production capability and constraints |
| Scenario | Concrete scene-level production decisions |
| MediaAsset | Generated/resolved media state |
| AssemblyPlan | Resolved instructions for combining assets |
| FinalAsset | Validated final output |
| Job | Execution state/envelope |

## 5. Critical boundaries

### Content intelligence → production

Content intelligence decides **what** should be produced.

Production infrastructure decides **how** it is produced.

### ProductionProfile → Scenario

The profile constrains and configures scenario generation. It is not a second Scenario.

### Scenario → Media

Scenario contains generation decisions. Media lifecycle turns those decisions into assets.

### Media → Assembly

Assembly receives resolved READY assets. Generation instructions do not leak into the resolved AssemblyPlan.

### Assembly → Output

Rendering creates the output; validation/finalization owns the terminal completion contract.

## 6. Job ownership

Each Job owns:

- job.json
- input content artifacts
- media assets
- assembly plan
- output

Cross-job asset/path references are invalid.

## 7. Current profile model

Account declares supported complexity levels.

ContentConcept selects `production_profile`.

ProductionProfileStore resolves and validates that profile against the Account.

Scenario generation receives the resolved profile.

This is the current canonical path:

```
Account.supported_complexity_levels
             ↓
ContentConcept.production_profile
             ↓
ProductionProfileStore
             ↓
validated ProductionProfile
             ↓
ScenarioGenerator
             ↓
Scenario
```

## 8. Production lifecycle

```
created
  ↓
audio
  ↓
visual
  ├─ ready → assembly
  └─ waiting → resume → ready
  ↓
assembly
  ↓
output validation
  ↓
completed
```

Failure is terminal for the normal run path. Retry semantics are a future explicit feature and must not be introduced implicitly.

## 9. Legacy architecture boundary

`job_creator.py` belongs to the historical architecture and must not participate in the current production path.

`run_ready_pipeline()` remains only as a compatibility wrapper around the canonical `PipelineOrchestrator`.

## 10. Navigation

For detailed principles see `ARCHITECTURE.md`.

For product requirements see `PRODUCT_SPEC.md`.

For planned phases see `ROADMAP.md`.

For development procedure see `docs/DEVELOPMENT_WORKFLOW.md`.
