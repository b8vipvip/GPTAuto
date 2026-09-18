# GPTAuto Protocol

GPTAuto makes engineering work goal-bound rather than turn-bound. A worker MUST continue or resume until the Definition of Done is satisfied or an explicit escalation condition is reached.

## Completion contract

Commit created, PR opened, Actions queued/running, PR CI passed, merge completed, and release started are intermediate states. DONE requires final verification of the requested outcome and all required gates.

## Canonical flow

GOAL -> INSPECT -> IMPLEMENT -> PR -> WAIT_CI -> MERGE -> MAIN_CI -> RELEASE -> VERIFY -> DONE

Failure: WAIT_CI, MAIN_CI, RELEASE or VERIFY -> ANALYZE -> FIX -> WAIT_CI.

Durable task state is the handoff between invocations.

## Stop policy

Enter BLOCKED only for unavailable permissions/credentials, a material ambiguous product decision, an unauthorized destructive/high-risk action, exhausted bounded repair budget, or an external platform condition the worker cannot repair.

Waiting for CI is not completion.

## Actions governance

Safe CI/test/policy workflows may be deduplicated or retried. Release/deploy/publish workflows are side-effectful and MUST NOT be blindly cancelled or replayed. Governor, Recovery, Housekeeping and Policy Check are governance workflows.

## Branch lifecycle

The default branch is protected. Aggressive cleanup is opt-in: every non-default branch whose tip commit is older than seven days may be deleted, using tip commit time as the age proxy.

## Integration invariant

GPTAuto owns orchestration state; a host such as GPTWork owns project-specific build, test, release and runtime adapters.
