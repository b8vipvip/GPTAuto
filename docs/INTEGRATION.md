# GPTWork integration contract

GPTAuto is standalone first. GPTWork later supplies adapters for repository inspection, branch/commit changes, PR creation/merge, Actions status/logs, safe retries, release invocation and final runtime verification.

GPTAuto supplies the durable task contract, state machine, repair budget, completion semantics and escalation semantics.

Suggested mapping:
- INSPECT: inspect repository, PRs, branches and current CI.
- IMPLEMENT: edit/test/commit on a work branch.
- PR: create or update PR.
- WAIT_CI: observe required checks; never finish the user task here.
- ANALYZE/FIX: inspect failed jobs, repair and return to CI.
- MERGE: merge after required PR gates pass.
- MAIN_CI: validate merged default-branch SHA.
- RELEASE: create/verify a release when required.
- VERIFY: verify artifacts/runtime/acceptance criteria.
- DONE: report final completed and remaining results.

Persist task state outside transient chat context so later invocations resume deterministically.
