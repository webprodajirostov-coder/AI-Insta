# Development Workflow

This repository follows an architecture-first development workflow.

## Default sequence

GitHub → inspect → design → edit → commit/PR → runtime test → analyze

### Assistant responsibilities

The assistant should:
- inspect repository source and related files through GitHub/project tooling;
- search all relevant references before changing a contract;
- design the change and explain its dependency/impact;
- edit repository files through GitHub tooling;
- create a branch/commit/PR when appropriate;
- inspect the resulting diff;
- analyze runtime test results returned by the user.

### User / Codespace responsibilities

The user should run only checks that require the runtime environment, including:
- pytest / unittest;
- ffmpeg / MoviePy;
- real external APIs and providers;
- .env-dependent checks;
- network-dependent checks.

The user returns the command output for joint analysis.

## Source inspection rule

Do not ask the user to run cat, sed, grep, find, or similar commands merely to inspect ordinary repository source files when the repository can be inspected through GitHub/project tooling.

Use Codespace commands only when the information is genuinely runtime-specific.

## Runtime boundary

External provider calls, environment variables, filesystem/runtime behavior, media rendering, and network-dependent checks belong to the runtime boundary.

Provider calls must never be introduced merely to validate static architecture or domain contracts.

## Architecture rule

Changes should preserve the separation between:
- Account / Knowledge;
- Research / ResearchInsight;
- ContentIdea;
- ContentConcept;
- ProductionProfile;
- Scenario;
- media generation;
- assembly;
- output validation.

Lower layers must consume explicit contracts rather than another module's internals.

## Test rule

Every meaningful domain or pipeline change should cover, where applicable:
1. valid path;
2. invalid state;
3. ownership/account isolation;
4. reference integrity;
5. recovery;
6. idempotency;
7. provider boundary.

Runtime tests are run by the user after repository changes are prepared.