# GPTAuto Consumer Sync Architecture

## Release fan-out

A GPTAuto release is the source event. Active consumers are selected from
`.gptauto/consumers.json` and receive a sync request.

```text
Release published
      |
      v
Consumer Registry
      |
      v
repository_dispatch
      |
      v
Consumer Sync PR
      |
      v
Consumer CI
      |
      v
Merge + status update
```

## Lifecycle states

Consumers use a shared lifecycle vocabulary:

- discovered
- registered
- syncing
- pr_created
- ci_running
- merged
- failed
- removed

## Safety rules

- Consumer updates are PR based.
- Runtime and workflow files are upgraded atomically.
- A failed sync does not leave a partially upgraded consumer.
- Scheduled sync remains a recovery path; release fan-out is the fast path.
