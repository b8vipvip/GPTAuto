# GPTAuto v0.15.0 three-tier repair pipeline

## 中文（默认）

GPTAuto v0.15.0 将 CI 失败修复收敛为一个串行 Repair Pipeline，同一个 `TASK_ID + current HEAD` 同时只有一个 repair owner：`repair_pipeline`。

```text
CI failure
   |
   v
Tier 1 deterministic repair
   | no patch
   v
Tier 2 GitHub Copilot CLI
   | unavailable / Free allowance exhausted / no patch / unsafe apply
   v
Tier 3 foreground/host recovery
   |
   v
push repaired HEAD -> normal CI -> Executor/Reconcile -> terminal DONE
```

三个 Tier 是同一个 repair generation 的顺序阶段，不允许并行修改同一 PR。修复流水线本身不拥有 Merge、Release 或 DONE 权威；正常 CI、Executor、Reconcile 和 canonical Task State 仍然是唯一验证/终态链路。

## Tier 1：确定性修复

`gptauto.repair` 首先尝试无需 AI 的保守修复。目前内置支持：

- 由失败日志明确触发的 `cargo fmt` / `ruff format` / `black` / `prettier` 格式化修复。
- 可选 `.gptauto/repair-rules.json` 声明式 `version_sync`，用于 manifest / Cargo / installer / metadata 等已知版本漂移。

规则只允许“从 canonical source 捕获一个值，再替换明确 target regex 的单一 capture group”，不能在规则里运行任意 shell 命令。

示例：

```json
{
  "version_sync": [
    {
      "name": "product-version",
      "when_log_matches": ["version mismatch", "expected version"],
      "source": {
        "file": "extension/manifest.json",
        "regex": "\\\"version\\\"\\s*:\\s*\\\"([^\\\"]+)\\\""
      },
      "targets": [
        {
          "file": "native-core/Cargo.toml",
          "regex": "(?m)^version\\s*=\\s*\\\"([^\\\"]+)\\\""
        }
      ]
    }
  ]
}
```

规则触发错误、目标不唯一或文件不存在时，Tier 1 记录诊断并安全降级，不会猜测修改。

## Tier 2：Copilot CLI Free

Tier 1 没有产生 patch 时，workflow 安装 GitHub Copilot CLI，并以非交互模式请求它修改当前 checkout。

安全边界：

- generation job 使用 `actions/checkout` 的 `persist-credentials: false`。
- Copilot 只暴露 `edit,view,grep,glob`，显式允许 `write`；不暴露 shell/network/git push/merge/release 工具。
- 不使用 `--allow-all` / `--yolo`。
- Copilot 只负责形成 working-tree diff；单独的写权限 job 在再次确认 PR `HEAD_SHA` 后才应用 patch、commit、push。
- Copilot 的结论不是验证证据；新的 GitHub Actions run 才是验证权威。

认证优先使用可选 repository secret `GPTAUTO_COPILOT_TOKEN`，没有时尝试 workflow 的 `github.token`。对于个人 Free 账户，如果仓库/账户策略不允许 `github.token` 调用 Copilot，或当月 Free Copilot allowance 已耗尽，Tier 2 会失败软降级到 Tier 3，而不会让整个工程任务被误判为 DONE。

`GPTAUTO_COPILOT_TOKEN` 如需配置，应使用最小权限、仅限所需仓库的用户 token；不要把写仓库凭据暴露给 Copilot generation job。

## Tier 3：Foreground recovery

当以下任一条件发生时，repair workflow 产生 `FOREGROUND_RECOVERY_REQUIRED`：

- Tier 1 无 patch 且 Tier 2 不可用/额度耗尽/无 patch；
- 生成的 patch 无法安全 apply；
- 自动 push 被权限阻止；
- PR head 属于 fork，GPTAuto 不应把仓库写 token 推向外部 head。

Tier 3 会：

1. 更新原 PR 的去重 recovery comment；
2. 发布 `gptauto.foreground-exit-guard/v1` artifact；
3. 保留相同 `TASK_ID / PR / HEAD_SHA / FAILED_RUN_ID`；
4. 要求 Continuation Host 恢复同一任务，而不是创建替代 PR；
5. Completion Lease 继续 ACTIVE，直到修复后的 CI、Merge、post-merge CI、Release（若要求）全部产生 terminal evidence。

## Repair ownership invariant

Canonical Orchestrator 在 `REPAIR_REQUIRED` 时固定：

```text
repair_owner = repair_pipeline
```

Tier 1、Tier 2、Tier 3 只是该 owner 内部的顺序阶段。这样避免“Copilot 在改代码，同时 foreground 也在改同一 HEAD”的双重修复竞争。

## English

v0.15.0 replaces the optional paid-API repair path with one sequential three-tier repair owner: deterministic repair, Copilot CLI, then explicit foreground recovery. The AI generation job is credential-isolated and cannot push, merge, or publish. Every proposed patch is revalidated against the current PR head and applied by a separate write-capable job. If Copilot Free is unavailable or its allowance is exhausted, the same repair generation falls through to a durable foreground handoff instead of parking or completing the task.
