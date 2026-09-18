# GPTAuto

GPTAuto is an autonomous GitHub engineering workflow protocol and reference implementation.

**Core rule:** a task is goal-bound, not chat-turn-bound. A worker does not report completion merely because it created a commit/PR, entered an Actions queue, merged code, or started a release. It continues or resumes until the Definition of Done is verified, or an explicit BLOCKED condition requires human input.

State machine:

    GOAL -> INSPECT -> IMPLEMENT -> PR -> WAIT_CI -> MERGE -> MAIN_CI -> RELEASE -> VERIFY -> DONE
                                      |                    |          |          |
                                      +-> ANALYZE -> FIX <-+----------+----------+

## v0.1 capabilities

- durable task contract and history
- explicit Definition of Done
- bounded repair budget and BLOCKED escalation
- GitHub PR / Actions / release observation adapter
- autonomous reconciliation of WAIT_CI, MERGE, MAIN_CI, RELEASE and VERIFY
- queued/running Actions are WAITING, never DONE
- CLI task init/status/manual-step/reconcile commands
- Actions Policy Check, Governor, bounded Recovery and optional Housekeeping
- unit tests for happy path, failure repair, repair budget and async orchestration

## Quick start

    python -m unittest discover -s tests -v
    python -m gptauto.cli init --goal "Ship a verified fix" --repo owner/repo --out task.json
    python -m gptauto.cli step task.json accepted
    python -m gptauto.cli status task.json
    python -m gptauto.cli reconcile task.json --max-polls 1

GitHub observation uses the `gh` CLI and its existing authentication (`GH_TOKEN`, `GITHUB_TOKEN`, or `gh auth`).

See `docs/PROTOCOL.md` and `docs/INTEGRATION.md`.

GPTAuto is developed standalone first, then embedded into GPTWork.
