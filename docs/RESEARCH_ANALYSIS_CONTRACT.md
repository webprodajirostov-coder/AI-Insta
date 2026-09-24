# Research Analysis Contract

## Purpose

The Research Analysis layer converts a `ResearchRecord` into structured research observations that can later become `ResearchInsight` entities.

It is an intermediate research-stage contract. It is not a content concept generator.

## Pipeline boundary

```text
ResearchRecord
    |
    v
ResearchAnalyzer
    |
    v
ResearchAnalysisResult
    |
    v
ResearchInsight
    |
    v
ContentIdea
    |
    v
ContentConcept
```

## Input

The analyzer accepts a validated `ResearchRecord` belonging to the current account.

Required input fields:

- `research_id`
- `account_id`
- `source`
- `raw_material`

The analyzer may use source metadata and raw material as context.

The analyzer must not require a ContentIdea, ContentConcept, Scenario, or ProductionProfile.

## ResearchAnalysisResult

The intermediate result contains research observations only:

```json
{
  "research_id": "research_001",
  "account_id": "sales_psychology_001",
  "summary": "Short factual synthesis of the source material.",
  "patterns": [
    "Observed recurring pattern or mechanism."
  ],
  "observations": [
    "Specific observation that may support a later ResearchInsight."
  ]
}
```

### Field rules

- `research_id`: required string; must match the input ResearchRecord.
- `account_id`: required string; must match the input ResearchRecord.
- `summary`: required string; describes the analyzed material without turning it into a content concept.
- `patterns`: required list of strings; recurring patterns or mechanisms identified in the material.
- `observations`: required list of strings; concrete observations suitable for later insight extraction.

The result is deterministic at the domain boundary: provider/network concerns must not leak into this contract.

## What belongs in Research Analysis

Allowed:

- core meaning of the source material
- recurring psychological or communication patterns
- observed framing
- observed audience trigger
- evidence-backed interpretation of the source
- distinctions between explicit claims and inferred patterns

Not allowed:

- final content angle for our account
- target emotion for our Reel
- final hook copy
- CTA
- production instructions
- visual prompts
- audio instructions
- monetization claims about our product

The legacy analyzer fields `core_meaning` and `viral_hook_trigger` are therefore treated as possible research observations, not as a final creative concept.

The legacy fields `our_angle` and `target_emotion` do not belong in this layer.

## ResearchInsight boundary

`ResearchInsight` is the normalized reusable observation derived from research.

A ResearchAnalysisResult may produce zero, one, or several ResearchInsights.

The conversion should preserve:

- source/research reference
- account ownership
- observation
- evidence
- relevance
- content implications
- confidence

A ResearchInsight may describe why a research observation matters for the account, but it must remain an observation rather than becoming a finished creative concept.

## Provider boundary

The analyzer must depend on an abstract analysis capability, not directly on HTTP or ODIRouter.

Conceptually:

```text
ResearchAnalyzer
    |
    v
ResearchAnalysisProvider
    |
    +-- deterministic/mock provider (tests)
    |
    +-- ODIRouter provider (production)
```

Provider-specific concerns remain outside the domain contract:

- API keys
- HTTP requests
- model names
- model fallback
- timeout/retry policy
- response parsing
- network errors

Tests for the research domain must not call ODIRouter.

## Legacy analyzer migration

`src/analyzer.py` remains untouched during the first implementation.

Reusable logic:

- extracting the source's core meaning
- identifying psychological hooks/triggers as observations

Not carried forward:

- direct `requests.post`
- hardcoded ODIRouter URL
- model fallback list
- API key loading
- writing `data/analyses/analysis_video_N.json`
- `our_angle`
- `target_emotion`
- account-independent global file naming

The new implementation is a clean replacement rather than a compatibility wrapper.

## MVP implementation order

1. Add validation for `ResearchAnalysisResult`.
2. Add a pure `ResearchAnalyzer` boundary with a deterministic provider.
3. Add tests for account ownership, research ownership, required fields, and separation from creative fields.
4. Add an ODIRouter-backed provider only after the domain contract is green.
5. Add the ResearchAnalysisResult -> ResearchInsight mapping.
6. Connect the resulting ResearchInsight to ContentIdea through existing `research_refs`.

## Non-goals

This layer does not:

- generate Reels
- create scenarios
- call media providers
- decide production profiles
- replace the existing production pipeline
- turn competitor material directly into publishable content
