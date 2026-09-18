# GPTAuto

GPTAuto is an autonomous GitHub engineering workflow protocol and reference implementation.

A task is complete only when its Definition of Done is satisfied. A chat turn, commit, pull request, merge, or queued/running Actions run is only an intermediate state.

State machine:

GOAL -> INSPECT -> IMPLEMENT -> PR -> WAIT_CI -> MERGE -> MAIN_CI -> RELEASE -> VERIFY -> DONE

Failures flow through ANALYZE -> FIX -> WAIT_CI. Durable task state allows later invocations to resume instead of restarting the conversation.

Components:
- Goal Contract and Definition of Done
- durable state machine and repair budget
- Actions Policy Check
- Actions Governor
- bounded Actions Recovery
- Repository Housekeeping
- CI/release gates and final verification

See docs/PROTOCOL.md and docs/INTEGRATION.md.

Quick check:

    python -m unittest discover -s tests -v
    python -m gptauto.cli init --goal "Ship a verified fix" --repo owner/repo --out task.json
    python -m gptauto.cli status task.json

GPTAuto is developed standalone first, then embedded into GPTWork.
