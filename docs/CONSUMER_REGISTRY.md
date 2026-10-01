# GPTAuto Consumer Registry

> 由 GPTAuto 维护的消费仓库生命周期记录。

最后更新时间：2026-10-01

## Active Consumers

| Repository | Version | Status | Auto Sync |
|---|---|---|---|
| b8vipvip/GPTWork | v0.15.4 | active | enabled |
| b8vipvip/chat2api | unknown | pending sync verification | enabled |
| b8vipvip/qnbot | unknown | pending sync verification | enabled |

## Consumer Lifecycle

```text
DISCOVERED
  ↓
REGISTERED
  ↓
SYNCING
  ↓
ACTIVE
  ↓
OUTDATED
  ↓
REMOVED
```

## Rules

- Active consumer 必须记录当前 GPTAuto 版本。
- 同步操作必须经过消费仓库 CI 验证。
- 卸载 GPTAuto 后保留历史记录，不直接删除生命周期信息。
- Release fan-out 只针对 `active + auto_sync=true` 的消费仓库。

## Sync History

| Date | Repository | Result |
|---|---|---|
| 2026-10-01 | GPTWork | pending automated verification |
