# GPTAuto Consumer Lifecycle

## States

- discovered
- registered
- syncing
- pr_created
- ci_running
- merged
- failed
- removed

## Release fan-out

A GPTAuto release selects consumers from `.gptauto/consumers.json` where:

- `status=active`
- `auto_sync=true`

The release workflow creates a dispatch plan. Consumer repositories still update through their own PR and CI gates.

## Safety

GPTAuto does not overwrite consumer repositories directly. The sync path is:

Release -> dispatch -> consumer sync PR -> consumer CI -> merge -> status update
