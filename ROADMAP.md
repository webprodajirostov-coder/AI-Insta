# AI-Insta — Roadmap

## 1. Product Direction

AI-Insta is an account-aware AI content engine for scalable short-form content production.

The system is designed around:

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

The first production format is vertical short-form video (Reels).

The first account is used as a validation case, not as a hardcoded product architecture.

---

## 2. Current Phase

### PHASE 0.2 — Content Intelligence

Goal:

Build the layer that converts account knowledge and research into structured content concepts that can enter the existing production pipeline.

---

## 3. PHASE 0.2.1 — Account + Knowledge

Create configuration-driven account structure.

Target:

Account
→ Knowledge

Knowledge should contain explicit and reusable context such as:

- positioning;
- audience;
- products;
- content pillars;
- tone of voice;
- constraints;
- recurring themes;
- business context.

The core pipeline must not contain account-specific business logic.

---

## 4. PHASE 0.2.2 — Research Insight

Create a normalized representation of research findings.

Target:

Research
→ ResearchInsight

ResearchInsight should preserve:

- source;
- topic;
- observation;
- relevance;
- evidence;
- optional content implications.

The goal is to separate raw research from usable content intelligence.

---

## 5. PHASE 0.2.3 — Content Idea

Convert knowledge and research insights into structured content ideas.

Target:

Knowledge + ResearchInsight
→ ContentIdea

A ContentIdea should contain enough information to be evaluated and developed without immediately entering production.

---

## 6. PHASE 0.2.4 — Content Concept

Convert an idea into a production-ready content concept.

Target:

ContentIdea
→ ContentConcept

A ContentConcept should define:

- core message;
- audience problem;
- angle;
- hook direction;
- value;
- CTA direction;
- relevant knowledge;
- relevant research insights.

---

## 7. PHASE 0.2.5 — Strategy → Production

Connect content intelligence with the existing production system.

Target:

ContentConcept
→ ProductionProfile
→ Scenario

The strategy layer decides what should be produced.

The production layer decides how it is produced.

These responsibilities must remain separated.

---

# PHASE 0.3 — End-to-End Content Generation

Target user flow:

Account
→ Knowledge
→ Research
→ Insight
→ Idea
→ Concept
→ ProductionProfile
→ Scenario
→ Audio / Visual
→ Assembly
→ Validation
→ FinalAsset

Target entry point:

`python -m src.create_content`

The command should create and process a content job without requiring manual manipulation of internal job files.

---

# PHASE 0.4 — Production Profiles

Introduce configuration-driven production profiles.

## SIMPLE

Current validated production path.

Minimal number of scenes and assets.

## STANDARD

More scenes, richer visual structure and stronger production configuration.

## ADVANCED

More complex visual/audio composition and configurable production logic.

Adding a profile must not require rewriting the core pipeline.

---

# PHASE 0.5 — Analytics

Connect published content with performance data.

Target:

FinalAsset
→ PublishedAsset
→ PerformanceData

Initial analytics should support:

- views;
- engagement;
- retention;
- clicks;
- conversions;
- other available platform metrics.

Analytics must remain separate from production execution.

---

# PHASE 0.6 — Learning Loop

Use performance data to improve future content decisions.

Target:

Analytics
→ Learning
→ Knowledge / Strategy

The learning layer should produce reusable signals rather than directly modifying production logic.

---

# 8. Development Strategy

Build vertical slices instead of isolated infrastructure layers.

Each major feature should ideally pass through:

data model
→ logic
→ integration
→ validation
→ recovery
→ idempotency

The existing production pipeline must remain stable while Content Intelligence is added.

---

# 9. Current Product Progress

The production foundation is approximately 60–65% of the path toward the first usable product.

This is a directional product estimate, not a code-completion percentage.

The strongest completed area is production infrastructure:

- job model;
- staged pipeline;
- visual provider boundary;
- asset ownership;
- isolation;
- lifecycle transitions;
- recovery;
- idempotency;
- final output validation.

The main remaining product work is:

- Account;
- Knowledge;
- ResearchInsight;
- ContentIdea;
- ContentConcept;
- Strategy Engine;
- end-to-end content creation;
- additional production profiles;
- analytics;
- learning loop.

---

# 10. First Product Readiness

The first usable product should allow:

1. Creating a new account without rewriting the core system.
2. Defining account knowledge and strategy.
3. Generating research insights.
4. Creating content ideas.
5. Turning ideas into content concepts.
6. Selecting a production profile.
7. Generating a scenario.
8. Producing media automatically.
9. Recovering failed jobs.
10. Re-running completed jobs safely.
11. Producing an isolated validated final asset.
12. Attaching performance data to published content.

The system should remain configuration-driven and extensible for additional niches, accounts, products, pillars, profiles and providers.
