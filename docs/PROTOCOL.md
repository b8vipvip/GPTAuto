# GPTAuto Protocol v0.1

GPTAuto makes engineering work goal-bound rather than turn-bound. A worker MUST continue or resume until the Definition of Done is satisfied or an explicit escalation condition is reached.

## Definition of Done

A chat response, commit, pushed branch, opened PR, queued/running Actions run, green PR CI, merge, green main CI, tag, or started release is an intermediate milestone. DONE requires the requested outcome's final acceptance evidence.

For a normal fix the minimum evidence is: requested change implemented, required PR/default-branch checks passed, and final behavior verified. For a release task, the requested release must additionally exist and its required artifacts/acceptance checks must be verified.

## Canonical flow

    GOAL -> INSPECT -> IMPLEMENT -> PR -> WAIT_CI -> MERGE -> MAIN_CI -> RELEASE -> VERIFY -> DONE

Failures from CI/release/verification flow to ANALYZE -> FIX -> WAIT_CI. Durable task state is the handoff between invocations.

## WAITING is not completion

Queued, requested, pending, waiting and in-progress Actions are asynchronous WAITING conditions. They must never be converted to DONE just because the current worker invocation is ending. Persist the task and resume reconciliation.

## Stop policy

Enter BLOCKED only for unavailable permissions/credentials, a material ambiguous product decision, an unauthorized destructive/high-risk action, exhausted bounded repair budget, or an external platform condition the worker cannot repair.

## Repair policy

Transient infrastructure failures may receive one bounded safe retry. Deterministic code/test failures require ANALYZE and FIX. Release/deploy/publish operations are side-effectful and are never blindly replayed.

## Actions governance

Policy Check enforces workflow invariants. Governor may cancel stale safe workflows while excluding release/deploy/publish. Recovery performs bounded retries only for completed safe workflows. Housekeeping handles repository lifecycle policy separately from task correctness.

## Branch lifecycle

The default branch is protected. Aggressive cleanup is opt-in: every non-default branch whose tip commit is older than seven days may be deleted, using tip commit time as the age proxy.

## Integration invariant

GPTAuto owns orchestration state, completion semantics, retry budget and escalation. A host such as GPTWork owns project-specific reasoning and adapters for editing code, tests, PR actions, release execution and runtime acceptance checks.
