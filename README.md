# GPTAuto

[中文](#中文) · [English](#english)

<a id="中文"></a>
## 中文（默认）

GPTAuto 是一个**按最终目标持续执行**的 GitHub 工程任务生命周期协议与参考实现。

它解决的不是“自动跑几个 Actions”，而是同一个工程任务从用户目标开始，经过开发、PR、CI、修复、合并、main 验证、正式发布，直到拿到可验证的终态证据。在此之前，任务始终保持 ACTIVE。

当前 canonical 协议的核心约束是：

> **Evidence 可以来自多个执行器，Decision Authority 只能有一个。**

### 核心原则

**任务边界由最终目标决定，不由对话轮次、PR、某一次 CI 或某个 Workflow run 决定。**

    GOAL → PLAN / DoD → EXECUTE → VERIFY → TERMINAL EVIDENCE → DONE

可选 Gate 包括：`INSPECT`、`IMPLEMENT`、`COMMIT`、`PR`、`PR_CI`、`MERGE`、`MAIN_CI`、`RELEASE`、`DEPLOY`、`RUNTIME_VERIFY`。

例如：
- “修改 README 并提交”不强制 Merge/Release。
- “修复 Actions 直到 CI 全绿”以当前任务 CI 全绿为终态。
- “把代码合并到 main”要求 Merge，并验证合并后的 main。
- “修复并发布 v1.2.3 正式版”必须完成 PR → CI → Merge → main CI → Release → Release evidence，不能把“已合并”误判为 DONE。

`queued` / `running` / “等待 Actions”都是中间态，不是 DONE。

## Task Protocol v2：持久任务，短生命周期执行

从 v0.14.0 开始，GPTAuto 不再把“阻止某一个 ChatGPT turn 退出”当成任务连续性的基础。核心不变量改为：

> **Task lifecycle is persistent; ChatGPT executions are disposable.**

`gptauto.task-state/v2` 是唯一终态权威。前台 ChatGPT、GPTWork、Observer、Executor、Reconcile 都不能独立决定 DONE。一次 ChatGPT execution 可以结束，但只要 canonical Task State 不是 `DONE`，工程任务仍然存活。

Canonical 状态收敛为 `RUNNING`、`WAITING_GITHUB`、`REPAIR_REQUIRED`、`USER_ACTION_REQUIRED`、`DONE`。失败进入 `REPAIR_REQUIRED` 时，Task State 生成绑定 `task_id + generation + current head` 的 `continuation_key`。Continuation Host（例如 GPTWork）只消费这个状态：等待时不需要保持旧 turn；需要修复时恢复同一任务/PR；只有 `DONE` 才关闭任务。

旧的 Exit Guard/Completion Lease 字段仅作为兼容投影，不再拥有第二套终态决策权。任务连续性来自持久 Task State + continuation，而不是某次对话是否仍存活。

## Canonical 完整任务链路

```text
用户最终目标
    │
    ▼
1. 创建 Task + Completion Lease
   task_id / repo / DoD / expected_version
   release_required / phase=ACTIVE
    │
    ▼
2. Foreground 执行开发
   branch → code → checks → push → PR
    │
    ▼
3. Observer【只接收产品事件】
   PR / product CI / merge evidence
   GPTAuto 控制面事件不得反馈进入 Observer
    │
    ▼
4. Orchestrator【唯一生命周期/调度决策权威】
    │
    ├─ CI_RUNNING  → WAIT
    ├─ CI_FAILED   → REPAIR_REQUIRED
    ├─ CI_GREEN    → MERGE
    ├─ MERGED      → POST_MERGE_VALIDATE
    ├─ RELEASE_REQUIRED → RELEASE
    └─ DoD 全部满足 → DONE
    │
    ▼
5. PR CI
    │
    ├─ failure → 唯一 repair_owner 修复同一 PR → push → 回到验证
    │
    └─ success
          │
          ▼
6. Merge main
          │
          ▼
7. 验证 expected merge SHA 已进入 main
          │
          ▼
8. Post-merge CI
    │
    ├─ failure → recovery / repair → 重新验证
    │
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
    │          - tag 指向 expected main/merge SHA
    │          - 必需 artifacts/assets 存在
    │                 │
    └────────┬────────┘
             ▼
10. Terminal Evidence
             │
             ▼
11. Completion Lease = DONE
    terminal_done=true
    allow_foreground_exit=true
             │
             ▼
12. Foreground 才允许结束工程任务
```

### 单一状态权威

Observer、Executor、Reconcile、Release 不允许分别维护一套“任务是否完成”的结论。它们只提交 evidence。

Canonical Task State 由 Orchestrator 解释并进行唯一状态迁移，例如：

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
  "repair_owner": "foreground",
  "ci": "success",
  "merge": "success",
  "post_merge_ci": "success",
  "release": "pending",
  "terminal_done": false,
  "allow_foreground_exit": false
}
```

task/head/generation 去重只是一道**幂等安全网**，不能成为主要调度机制，也不能与 Orchestrator 分享终态决策权。

### Repair Owner：禁止双重修复权威

每个 generation 同时只能有一个 repair owner：

```text
repair_owner = foreground
```

表示前台宿主必须修复同一 PR / 当前 HEAD 对应的失败，push 后重新进入验证。

如果未来明确配置 autonomous AI provider，可以使用：

```text
repair_owner = gptauto_ai
```

此时 foreground 不得同时修改同一 repair generation。

没有 AI provider 时，`repair_request` 必须产生明确的 `FOREGROUND_RECOVERY_REQUIRED`，不能永久悬挂，也不能假装后台仍有人修复。

### 前台任务生命周期协议

Foreground 不允许在下面这种状态正常结束：

```text
Completion Lease = ACTIVE
terminal_done = false
allow_foreground_exit = false
```

尤其禁止把：

```text
PR 已提交，CI 正在运行，我继续关注。
```

当成工程任务终态。

GitHub Actions 本身不能重新唤醒一个已经结束的 ChatGPT turn。因此 Host/Bridge 必须在允许前台结束前重新读取 canonical task state。

如果产品运行时确实迫使当前 turn 中断，应记录为类似：

```text
SUSPENDED_AWAITING_HOST_RESUME
```

而不是 DONE，也不能声称“后台继续盯着”。

### Merge 不是发布完成

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

“PR merged”、“Release workflow green”或“tag 存在”中的任何单项都不能释放 Completion Lease。

### 单向控制面

GPTAuto 控制面必须是单向的：

```text
产品事件 → Observer → Orchestrator/Executor → Reconcile → CI/Release → terminal evidence

GPTAuto Observer / Executor / Reconcile / Release
                       └── X ──> 不得反馈成新的 Observer 调度输入
```

Reconcile 是 post-merge authority，负责触发/验证 post-merge CI 和必要的 Release，并直接提交终态 evidence。

v0.13.24 起，Observer 的 `workflow_run` ingress 只订阅产品 CI；GPTAuto 自身控制面 workflow 和 Release 不再形成 Observer → Executor → Reconcile 的自激循环。Reconcile 的 workflow catalog 仍是单一 discovery authority，但使用完整分页读取，避免 workflow 数量超过 100 时漏掉 Release。

### Completion Lease

只要最终目标没有满足：

```text
completion_lease = ACTIVE
terminal_done = false
allow_foreground_exit = false
```

只有真正取得最终 DoD evidence 后：

```text
completion_lease = DONE
terminal_done = true
allow_foreground_exit = true
```

前台才能汇报任务完成。

### 快速开始

    python -m unittest discover -s tests -v
    python -m gptauto.cli init --goal "把代码合并到 main" --repo owner/repo --out task.json
    python -m gptauto.cli status task.json

消费仓库可安装 canonical Consumer Sync。默认审计日志位于 `.gptauto/logs/<TASK_ID>/`，包括 `task.log`、`state.json`、`events.jsonl`、`summary.md`。

进一步协议与集成说明见：
- `docs/PROTOCOL.md`
- `docs/INTEGRATION.md`
- `docs/OBSERVABILITY.md`

<a id="english"></a>

## English

### Task Protocol v2: persistent tasks, disposable executions

Starting with v0.14.0, GPTAuto no longer treats preventing a particular ChatGPT turn from exiting as the basis of task continuity.

> **Task lifecycle is persistent; ChatGPT executions are disposable.**

`gptauto.task-state/v2` is the sole terminal authority. ChatGPT, GPTWork, Observer, Executor, and Reconcile do not independently decide DONE. A foreground execution may end while the engineering task remains alive.

The canonical lifecycle converges on `RUNNING`, `WAITING_GITHUB`, `REPAIR_REQUIRED`, `USER_ACTION_REQUIRED`, and `DONE`. A repair transition creates a continuation identity bound to `task_id + generation + current head`. A Continuation Host such as GPTWork waits without keeping an old turn alive, resumes the same task/PR when continuation is required, and closes the task only on canonical DONE.

Legacy Exit Guard and Completion Lease fields are compatibility projections only. They are not additional terminal authorities.




### v0.14.1：显式 Post-merge 调度

v0.14.1 收敛 post-merge 链路：Reconcile 不再等待一个“可能由 merge push 自动产生”的产品 CI。由 GitHub Actions `GITHUB_TOKEN` 完成的 merge 不保证再次触发 workflow，因此这种轮询不是可靠协议。

现在 Reconcile 从 workflow catalog 解析唯一产品验证工作流（默认 `CI` / `Build and Test`，非标准名称可显式配置），确认 default branch 仍精确指向目标 merge SHA，然后通过 `workflow_dispatch` **主动启动一次** post-merge validation，记录该 run ID，并只验证这个 run。若工作流不可 dispatch、main 已移动或配置不明确，则立即产生明确恢复错误，不再空转 300 秒等待不存在的 run。

GitHub 的 `workflow_run` 过滤能力只能按 workflow 名称和完成事件筛选，不能按 conclusion/event 在 workflow 创建前过滤。因此少量由 job-level `if:` 产生的 `Skipped` run 属于 GitHub 触发模型的可见副产物；GPTAuto 的目标是不让它们形成控制面自激或重复决策。v0.14.1 不用“把 Skipped 伪装成 success”的方式隐藏它们。

### v0.14.1: explicit post-merge scheduling

Reconcile no longer polls for a product CI run that may never be created after a token-driven merge. It resolves the canonical product validation workflow, verifies that the default branch still equals the target merge SHA, explicitly dispatches exactly one `workflow_dispatch` run, records its run ID, and validates only that run. Non-dispatchable or ambiguous workflows fail immediately with actionable recovery evidence instead of a 300-second registration poll.

A small number of visible `Skipped` runs can still be created by GitHub because `workflow_run` cannot pre-filter on conclusion/event before the workflow run exists. They are acceptable only as non-authoritative trigger artifacts: they must not create control-plane feedback or duplicate lifecycle decisions.
