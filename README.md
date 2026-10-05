# GPTAuto

[中文](#中文) · [English](#english)

> 当前版本：**v0.15.10**

<a id="中文"></a>
## 中文（默认）

GPTAuto 是一个**按最终目标持续执行**的 GitHub 工程任务生命周期协议与参考实现。

它解决的不是“自动跑几个 Actions”，而是让同一个工程任务从用户目标开始，经过开发、PR、CI、失败修复、重新验证、合并、main 验证，以及需要时的正式 Release，直到取得可验证的最终证据。在此之前，任务始终保持 ACTIVE。

当前 canonical 协议的核心约束是：

> **Evidence 可以来自多个执行器，Decision Authority 只能有一个。**

## 核心原则

**任务边界由最终目标决定，不由对话轮次、PR、某一次 CI 或某个 Workflow run 决定。**

```text
GOAL → PLAN / DoD → EXECUTE → VERIFY → TERMINAL EVIDENCE → DONE
```

可选 Gate 包括：`INSPECT`、`IMPLEMENT`、`COMMIT`、`PR`、`PR_CI`、`MERGE`、`MAIN_CI`、`RELEASE`、`DEPLOY`、`RUNTIME_VERIFY`。

例如：

- “修改 README 并提交”不强制 Release。
- “修复 Actions 直到 CI 全绿”以当前任务 CI 全绿为终态。
- “把代码合并到 main”要求 Merge，并验证合并后的 main。
- “修复并发布 v1.2.3 正式版”必须完成 PR → CI → Merge → main CI → Release → Release evidence，不能把“已合并”误判为 DONE。

`queued` / `running` / “等待 Actions”都是中间态，不是 DONE。

## Task Protocol v2：持久任务，短生命周期执行

从 v0.14.0 开始，GPTAuto 不再把“阻止某一个 ChatGPT turn 退出”当成任务连续性的基础。核心不变量是：

> **Task lifecycle is persistent; ChatGPT executions are disposable.**

`gptauto.task-state/v2` 是唯一终态权威。前台 ChatGPT、GPTWork、Observer、Executor、Repair、Reconcile 都不能独立决定 DONE。一次前台 execution 可以结束，但只要 canonical Task State 不是 `DONE`，工程任务仍然存活。

Canonical 状态收敛为：

```text
RUNNING
WAITING_GITHUB
REPAIR_REQUIRED
USER_ACTION_REQUIRED
DONE
```

失败进入 `REPAIR_REQUIRED` 时，Task State 生成绑定 `task_id + generation + current head` 的 continuation identity。Continuation Host（例如 GPTWork）只消费这个状态：等待时不需要保持旧 turn；需要修复时恢复同一任务/PR；只有 `DONE` 才关闭任务。

旧 Exit Guard / Completion Lease 字段仅作为兼容投影，不再拥有第二套终态决策权。

## v0.15.4：快速修复与 CI 快速路径

v0.15.4 的重点是**缩短失败 → 修复 → 再验证 → 合并/发布的 wall-clock time，同时不放松最终验证门槛**。

当前控制面已经实现：

1. **Repair patch 先做 targeted validation。** 根据实际改动文件只运行对应语言/构建族的快速检查；局部验证失败时不 push，也不浪费完整 CI。
2. **瞬时基础设施失败只重跑 failed jobs。** `ci_policy` 识别明确 transient evidence 后，只调用一次 `rerun-failed-jobs`，不会把已经成功的 matrix job 全部重跑。
3. **新 HEAD 立即淘汰旧 HEAD。** PR `synchronize` 后，Observer 会取消旧提交上仍 queued/running 的产品 workflow run，避免 runner 为 superseded commit 继续工作。
4. **短 CI 做事件合并。** `workflow_run: in_progress` 可以在 Observer 内短轮询，几十秒内即将结束的 CI 不必额外走一次 Observer → Executor 往返。
5. **Executor 对等待中的 CI 使用有界短轮询。** merge gate 在最新 workflow 仍 queued/in_progress 时先短等，不把正常等待误判为失败。
6. **5 分钟 watchdog 只是保险。** 它用于 GitHub 丢事件、审批恢复或控制面异常后的自愈；精确 HEAD 的 CI 正常 queued/running 时 watchdog 会跳过，不把 5 分钟周期当常规调度器。
7. **三层 Repair。** Tier 1 确定性修复 → Tier 2 Copilot CLI → Tier 3 前台恢复；同一 generation 只允许一个 repair owner。
8. **消费仓库可叠加产品侧快速路径。** 按文件选择 CI matrix、Cargo/npm/Python/Tauri/installer cache，以及让 Release 复用同一精确 merge SHA 的 main-CI artifact。GPTAuto 保留最终 full merge/release gate，不用“少跑检查”换取速度。

## Canonical 完整任务链路

```text
用户最终目标
    │
    ▼
1. 创建 Task / canonical state
   task_id / repo / DoD / expected_version
   release_required / generation / current head
    │
    ▼
2. Foreground 执行开发
   branch → code → checks → push → PR
    │
    ▼
3. Observer【只接收产品事件】
   PR / product CI / merge evidence
   取消 superseded runs
   合并短 in-progress CI 事件
    │
    ▼
4. Orchestrator / Executor【唯一生命周期/调度决策权威】
    │
    ├─ CI_RUNNING  → WAIT / bounded poll
    ├─ transient CI_FAILED → rerun failed jobs once
    ├─ CI_FAILED   → REPAIR_REQUIRED
    ├─ CI_GREEN    → MERGE
    ├─ MERGED      → POST_MERGE_VALIDATE
    ├─ RELEASE_REQUIRED → RELEASE
    └─ DoD 全部满足 → DONE
    │
    ▼
5. Repair（需要时）
   Tier 1 deterministic
      ↓ no patch
   Tier 2 Copilot CLI
      ↓ unavailable / unsafe / validation failed
   Tier 3 foreground handoff
      │
      └─ patch → targeted validation → push → PR CI
    │
    ▼
6. Merge main
    │
    ▼
7. Reconcile 显式验证 expected merge SHA
    │
    ▼
8. Post-merge CI
    │
    ├─ failure → recovery / repair
    └─ success
          │
          ▼
9. release_required ?
    │                 │
    NO               YES
    │                 ▼
    │          canonical Release workflow
    │                 │
    │                 ▼
    │          Release Proof Validator
    │          - GitHub Release 已 published
    │          - tag 指向 expected merge SHA
    │          - 必需 assets/artifacts 存在
    │
    └────────┬────────┘
             ▼
10. Terminal Evidence → DONE
```

## 应用方法（消费仓库）

下面是 v0.15.4 推荐的实际接入方式。

### 1. 先准备产品 CI

消费仓库至少要有一个真正验证产品代码的 workflow。

推荐名称：

```text
CI
```

也兼容：

```text
Build and Test
```

Post-merge Reconcile 会显式 `workflow_dispatch` 这个产品验证 workflow，因此它必须支持：

```yaml
on:
  pull_request:
  push:
    branches: [main]
  workflow_dispatch:
```

如果产品 workflow 不是 `CI` / `Build and Test`，设置 repository variable：

```text
GPTAUTO_POST_MERGE_WORKFLOW=<workflow name 或 .github/workflows/xxx.yml>
```

发布型任务还需要一个启用的 canonical workflow：

```text
Release
```

Release 必须发布真正的 GitHub Release evidence；仅 workflow 绿色或 tag 存在都不等于发布完成。

### 2. Bootstrap Consumer Sync

把 canonical 模板：

```text
consumer-template/gptauto-sync.yml
```

安装到消费仓库：

```text
.github/workflows/gptauto-sync.yml
```

第一次接入也可以直接把这些 managed paths 一次性复制到消费仓库：

```text
.github/gptauto/
.github/actions/upload-gptauto-log/action.yml
.github/workflows/gptauto-sync.yml
.github/workflows/gptauto-observer.yml
.github/workflows/gptauto-executor.yml
.github/workflows/gptauto-repair.yml
.github/workflows/gptauto-reconcile.yml
```

之后不再每小时检查 canonical GPTAuto。**只有 GPTAuto 发布新版本时**才会触发一次 Consumer Sync；canonical Release 会等待所有注册消费仓库完成 PR/CI/合并并把默认分支 `VERSION` 升级到目标版本后才正式发布。也可以在 Actions 页面手动运行 `workflow_dispatch`，选择：

```text
operation = sync
```

同步始终通过分支/PR 进入消费仓库，产品 CI 仍是安全门槛。

### 3. 配置自动化凭据

从 v0.15.10 起，GPTAuto 的推荐配置收敛为 **2 Token 模型**：

**`GPTAUTO_GITHUB_TOKEN`**

统一承担非 Copilot 的 GitHub 自动化职责，包括 Consumer release fan-out、Consumer Sync、Executor、Repair push、PR/merge 与 Reconcile。对消费仓库建议授予：

```text
Contents: Read and write
Pull requests: Read and write
Workflows: Read and write
Actions: Read and write
Checks: Read
```

canonical GPTAuto 仓库中的同名 secret 还需要能够访问所有已注册消费仓库，以便在新版本发布时发送 `repository_dispatch` 并等待消费仓库升级收敛。

旧的 `GPTAUTO_CONSUMER_TOKEN`、`GPTAUTO_SYNC_TOKEN`、`GPTAUTO_EXECUTOR_TOKEN` 仍作为兼容回退读取，因此已有仓库可以无中断迁移；新安装不再要求创建这三个独立 PAT。

**`GPTAUTO_COPILOT_TOKEN`（可选但推荐独立）**

仅用于 Tier 2 Copilot CLI。它与 GitHub 仓库自动化凭据保持隔离，需要 Copilot Requests 权限；是否能实际调用 Copilot 仍取决于该账户/仓库可用的 Copilot entitlement/allowance。

GPTAuto v0.15.10 不要求 `GPTAUTO_AI_API_KEY`，也不依赖 `openai/codex-action` 才能维持核心生命周期。

### 4. 使用三层 Repair

当产品 PR CI 失败时，标准路径是：

```text
CI failure
   ↓
ci_policy
   ├─ 明确 transient → rerun failed jobs once
   └─ 普通代码/测试失败
          ↓
Tier 1 deterministic repair
          ↓ no patch
Tier 2 Copilot CLI
          ↓ no safe patch
Tier 3 FOREGROUND_RECOVERY_REQUIRED
```

Tier 1 / Tier 2 生成 patch 后不会直接 push，而是先执行：

```text
python -m gptauto.validation
```

只有 targeted validation 通过、PR HEAD 仍与 repair lease 一致、且写凭据满足要求时，Apply job 才会 commit/push。push 后新的 PR HEAD 会重新触发产品 CI；旧 HEAD 的 queued/running run 会被取消。

### 5. 在消费仓库启用产品侧快速 CI

GPTAuto 的控制面优化不会替代产品仓库自己的 CI 设计。为了取得最大收益，建议消费仓库继续实现：

```text
changed-path classification
→ 只运行受影响的 PR CI matrix
→ dependency cache
→ 最终 merge/main 保留完整验证
→ main CI 针对精确 merge SHA 产出 release-ready artifact
→ Release 校验 provenance/digest 后复用同 SHA artifact
```

这样 Repair 阶段可以快，而最终 Merge / Release 仍保持完整证据链。

### 6. Host / GPTWork 的完成规则

前台 Host 不允许把下面状态当作完成：

```text
PR 已提交
CI queued/running
Repair 已触发
PR 已合并但 main CI 未验证
Release workflow 已启动但 GitHub Release 未发布
```

只有 canonical state 给出：

```text
terminal_done = true
allow_foreground_exit = true
```

才能关闭工程任务。

如果当前前台 execution 被产品运行时中断，状态应保持可恢复，例如：

```text
SUSPENDED_AWAITING_HOST_RESUME
```

而不是伪装成 DONE 或声称“后台会继续”但没有持久 task state。

## 单一状态权威

Observer、Executor、Repair、Reconcile、Release 不允许分别维护一套“任务是否完成”的结论。它们只提交 evidence，由 canonical state 解释。

示例：

```json
{
  "task_id": "GA-xxxx",
  "repo": "owner/repo",
  "pr": 123,
  "expected_version": "1.2.3",
  "release_required": true,
  "phase": "RELEASE_VERIFY",
  "generation": 7,
  "head_sha": "...",
  "merge_sha": "...",
  "repair_owner": "repair_pipeline",
  "ci": "success",
  "merge": "success",
  "post_merge_ci": "success",
  "release": "pending",
  "terminal_done": false,
  "allow_foreground_exit": false
}
```

`task_id + generation + head_sha` 去重只是**幂等安全网**，不能与 Orchestrator 分享终态决策权。

## Repair Owner：禁止双重修复权威

每个 generation 同时只能有一个 repair owner。

自动修复链路中：

```text
repair_owner = repair_pipeline
```

Tier 1 / Tier 2 / Tier 3 都属于同一个 repair lease，而不是三套并行修复权威。

如果已经进入 `FOREGROUND_RECOVERY_REQUIRED`，前台才接手当前 generation；新的 HEAD 会让旧 repair lease 自动 superseded。

## Merge 不是发布完成

Release 型任务只有在所有要求的终态证据同时成立后才能 DONE：

```text
PR merged
AND expected merge SHA is on main
AND post-merge CI succeeded
AND GitHub Release is actually published
AND release tag resolves to expected SHA
AND required release assets exist
AND no active repair/recovery generation remains
```

“PR merged”、“Release workflow green”或“tag 存在”中的任何单项都不能释放任务。

## 单向控制面

GPTAuto 控制面必须保持单向：

```text
产品事件 → Observer → Executor → Repair/Reconcile → CI/Release → terminal evidence

GPTAuto Observer / Executor / Repair / Reconcile
                       └── X ──> 不得反馈成新的产品 Observer 调度输入
```

Observer 只监听产品事件；GPTAuto 自身控制 workflow 不能形成 Observer → Executor → Reconcile 的自激循环。

## 快速开始（GPTAuto 自身开发/验证）

```bash
python -m unittest discover -s tests -v
python -m compileall -q gptauto
python -m gptauto.cli init --goal "把代码合并到 main" --repo owner/repo --out task.json
python -m gptauto.cli status task.json
```

v0.15.4 快速路径相关的自测主要覆盖：

```text
tests/test_validation.py   targeted validation / changed-language planning
tests/test_templates.py    superseded cancellation / CI coalescing /
                           failed-jobs-only retry / watchdog insurance /
                           three-tier repair / credential isolation
```

消费仓库默认审计日志位于：

```text
.gptauto/logs/<TASK_ID>/
```

包括：

```text
task.log
state.json
events.jsonl
summary.md
```

进一步说明：

- `docs/PROTOCOL.md`
- `docs/REPAIR_PIPELINE.md`
- `docs/INTEGRATION.md`
- `docs/CONSUMER_MANAGEMENT.md`
- `docs/OBSERVABILITY.md`
- `docs/V0.15.4.md`

---

<a id="english"></a>
## English

GPTAuto is a persistent GitHub engineering-task lifecycle protocol. A task stays alive until its requested definition of done has terminal evidence; a PR, one successful job, or a merge alone is not necessarily DONE.

### v0.15.4 fast path

v0.15.4 reduces repair and CI wall-clock time without weakening terminal gates:

- repair patches run targeted validation before push/full CI;
- clearly transient failures get one failed-jobs-only retry;
- PR head changes cancel queued/running runs for superseded heads;
- short in-progress CI is coalesced before an unnecessary Observer → Executor hop;
- Executor performs bounded short polling instead of treating normal queued/running CI as failure;
- the five-minute watchdog is recovery insurance, not the normal scheduler;
- repair is one lease with deterministic → Copilot CLI → foreground fallback tiers;
- consumer repositories can add path-selective PR matrices, dependency caches, and exact-SHA main-CI artifact reuse for Release while keeping a full final gate.

### Consumer installation

1. Provide a product validation workflow named `CI` or `Build and Test` with `pull_request`, default-branch `push`, and `workflow_dispatch`. If you use another workflow, set repository variable `GPTAUTO_POST_MERGE_WORKFLOW`.
2. Bootstrap `consumer-template/gptauto-sync.yml` as `.github/workflows/gptauto-sync.yml`, or copy all GPTAuto managed paths once.
3. Configure `GPTAUTO_GITHUB_TOKEN` with repository-scoped Contents/Pull requests/Workflows/Actions write and Checks read permissions. Legacy `GPTAUTO_SYNC_TOKEN` / `GPTAUTO_EXECUTOR_TOKEN` remain accepted during migration.
4. Configure `GPTAUTO_COPILOT_TOKEN` separately when Tier 2 Copilot CLI is desired.
5. Run **GPTAuto Consumer Sync** with `operation=sync`. Future canonical updates are proposed through CI-gated sync PRs only when GPTAuto publishes a new version.
6. For release tasks, provide an enabled `Release` workflow that publishes verifiable GitHub Release evidence for the exact expected merge SHA.

### Repair lifecycle

```text
product CI failure
  → transient policy: rerun failed jobs once, or
  → Tier 1 deterministic repair
  → Tier 2 Copilot CLI
  → Tier 3 foreground recovery
  → targeted validation
  → head revalidation
  → push same PR
  → new PR CI
  → merge
  → explicit post-merge validation
  → optional Release proof
  → DONE
```

`gptauto.task-state/v2` remains the sole terminal authority. Foreground executions are disposable; the task lifecycle is persistent.
