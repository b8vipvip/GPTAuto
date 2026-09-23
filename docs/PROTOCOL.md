# GPTAuto 协议 v0.2 / GPTAuto Protocol v0.2

## 中文（默认）

### 1. 最终目标优先

GPTAuto 不定义一条适用于所有任务的固定流水线。收到目标后必须先进入 PLAN，形成该任务自己的 DoD 与动态 Gate 计划。

    GOAL → PLAN → EXECUTE → VERIFY → DONE

### 2. Dynamic Gates

Gate 是可选能力，不是固定阶段。只有被计划选中的 Gate 才能阻止任务完成。可选 Gate：INSPECT、IMPLEMENT、COMMIT、PR、PR_CI、MERGE、MAIN_CI、RELEASE、DEPLOY、RUNTIME_VERIFY。

宿主推理层应综合用户明确要求、仓库规则、风险等级和任务类型生成计划。内置 GoalPlanner 只作为 CLI/参考实现的安全启发式默认值；GPTWork 等宿主可以显式传入 gates 与 DoD 覆盖它。

### 3. Definition of Done

DoD 不再是字符串清单，而是带 `pending/passed/failed` 状态和 evidence 的验收条件。进入 DONE 必须同时满足：
1. 所有 required Gate 已 passed/skipped；
2. 所有 DoD 条目均为 passed；
3. 每个 DoD 条目保留验收证据。

因此 Commit、PR、CI、Merge、Release 都既不是天然“完成”，也不是天然“必需”。它们是否必要完全由当前目标决定。

### 4. WAITING 与中断

只有计划中的异步 Gate 才产生 WAITING。queued/requested/pending/in_progress 不能被误判为该 Gate 已完成。GPTAuto 应持久化状态并继续/恢复，而不是因为一轮对话结束就报告 DONE。

### 5. BLOCKED

仅在权限/凭据缺失、重大产品决策歧义、未授权高风险破坏性操作、修复预算耗尽或不可修复的外部平台条件下进入 BLOCKED。

### 6. 前台完成契约

只要 Completion Lease 仍为 active，任何 commit、PR、部分 CI 成功、repair request、merge 或 release-in-progress 都只能作为进度证据，不能作为“任务完成”的依据。Executor 必须公开持久化的 ACTIVE completion guard；只有 Reconcile 产生 terminal DONE evidence 并释放该 Lease 后，宿主/前台代理才允许向用户报告工程任务完成。对话超时或前台会话结束不能覆盖此契约。对于用户要求“修复并发布/推进到完成”的终态任务，宿主必须把 ACTIVE Completion Lease 视为“继续执行”而不只是“禁止宣布 DONE”：PR 创建、Actions 排队/运行、等待异步结果都不是允许结束前台工程回合的边界。宿主必须持续轮询/恢复，直到 terminal DONE，或进入确实需要用户操作的 BLOCKED。Executor 在 repair_request 且 AI Provider 不可用时必须发布机器可读的 Foreground Exit Guard：`foreground_disposition=CONTINUE_REQUIRED`、`allow_foreground_exit=false`、`terminal_done=false`，并绑定 TASK_ID、PR、HEAD_SHA、FAILED_RUN_ID。宿主在结束工程回合前必须重新读取该 guard；只要 exit 未获许可，就必须读取失败日志、修复同一 PR、push 并继续验证，不能把任务重新委托给无修复能力的 GPTAuto 后退出。

### 6.1 单一前台生命周期状态权威

对于终态工程任务，`lease_wait` 也不是“可以结束聊天、以后后台继续”的状态。GPTAuto 必须把所有 ACTIVE Lease（包括 `lease_wait`、`repair_request`、`verify`）投影为唯一的机器可读 `gptauto.host-control/v1`：`foreground_disposition=CONTINUE_REQUIRED`、`allow_foreground_exit=false`、`requires_foreground_poll=true`。提交任务的宿主必须消费这个 host-control：`lease_wait` 时继续轮询当前 task/HEAD，状态变化后立即重新决策；`repair_request` 时读取失败 run 并修复同一 PR；只有 terminal DONE 才能得到 `EXIT_ALLOWED`。状态汇报不能替代执行，也不得声称“继续盯着/后台等待”后结束回合，除非宿主确实具备并已启动可恢复的后台执行机制。

### 7. 修复

失败 Gate 消耗有界 repair budget。修复动作由宿主推理层决定，完成后重新验证当前计划所要求的 Gate；不应因为历史上存在 PR/CI/Release 阶段而强制重新走无关步骤。

AI Repair 是可选增强能力，不是任务连续性的前提。若 `repair_request` 发生时未配置 AI Provider，Executor 必须发布机器可读/持久化的 `FOREGROUND_RECOVERY_REQUIRED` handoff，绑定原 TASK_ID、PR、当前 head 与失败 run。宿主/前台代理应恢复同一个 PR、读取失败证据并继续修复；Completion Lease 保持 ACTIVE，直到重新通过 Gate 并产生 terminal DONE。缺少可选 AI Provider 本身不得把可修复任务永久停放或误报完成。

---

## English

### Goal-first execution

GPTAuto does not prescribe one fixed pipeline. Each task first enters PLAN, where the host derives a task-specific Definition of Done and selects only the gates required by the requested outcome.

    GOAL → PLAN → EXECUTE → VERIFY → DONE

### Dynamic gates

Gates are optional capabilities: INSPECT, IMPLEMENT, COMMIT, PR, PR_CI, MERGE, MAIN_CI, RELEASE, DEPLOY, and RUNTIME_VERIFY. Only selected required gates can block completion.

The host reasoning layer should plan from the explicit user request, repository policy, risk level, and task type. The built-in GoalPlanner is a conservative CLI/reference heuristic; hosts such as GPTWork may provide explicit gates and DoD criteria.

### Evidence-based DoD

Each DoD criterion has pending/passed/failed state plus evidence. DONE requires all required gates to be satisfied and every criterion to have passed evidence. Commit, PR, CI, merge, release, and deploy are therefore neither universally terminal nor universally mandatory.

### Foreground completion contract

While a Completion Lease is active, commits, PR creation, partial CI success, repair requests, merges, and releases in progress are progress evidence only. Executor publishes a durable ACTIVE guard. A host/foreground agent may report engineering completion only after Reconcile emits terminal DONE evidence and releases the lease. Chat/session termination never overrides this contract. For terminal engineering requests such as fix-and-release, an ACTIVE Completion Lease is a continuation obligation, not merely a prohibition on saying DONE: PR creation, queued/running Actions, and waiting for asynchronous results are not valid boundaries for ending the foreground engineering turn. The host must poll/recover until terminal DONE or a genuine user-action BLOCKED state. When a repair request has no available AI Provider, Executor must publish a machine-readable Foreground Exit Guard with foreground_disposition=CONTINUE_REQUIRED, allow_foreground_exit=false, terminal_done=false, bound to TASK_ID, PR, HEAD_SHA, and FAILED_RUN_ID. Before ending an engineering turn, the host must re-read this guard; while exit is denied it must inspect the failed run, repair the same PR, push, and continue verification rather than delegating back to an incapable GPTAuto and exiting.

### Single foreground lifecycle authority

For terminal engineering tasks, `lease_wait` is not permission to end the chat and claim background monitoring. Every ACTIVE lease, including `lease_wait`, `repair_request`, and `verify`, is projected as the single machine-readable `gptauto.host-control/v1` authority with `foreground_disposition=CONTINUE_REQUIRED`, `allow_foreground_exit=false`, and `requires_foreground_poll=true`. The submitting host must consume that authority: poll the current task/head while waiting, immediately re-decide on state changes, repair the same PR on `repair_request`, and exit only after terminal DONE yields `EXIT_ALLOWED`. A progress report is not a substitute for execution, and the host must not claim it will keep watching in the background unless a real resumable background executor has actually been started.

### Waiting and blocking

Asynchronous states are WAITING only for gates selected by the plan. BLOCKED is reserved for missing permission/credentials, material product ambiguity, unauthorized destructive action, exhausted repair budget, or an unrecoverable external platform condition.


### Consumer Sync workflow permission

Consumer Sync is atomic. If a canonical release changes `.github/workflows/*`, the repository must provide `GPTAUTO_SYNC_TOKEN` with Contents write, Pull requests write, and Workflows write. The default GitHub Actions token may not update workflow files. Sync detects this before push, leaves the installed VERSION unchanged, and creates/updates one deduplicated repository issue instead of repeatedly failing with a remote rejection. Releases that do not change workflow files continue to use the normal repository token.


### Authority invariant

`gptauto.orchestrator.canonicalize_task()` is the only lifecycle authority for phase, repair generation/owner, terminal DONE, Completion Lease and foreground-exit permission. Observer only records evidence; Executor/host-control transports and enforces the canonical projection and MUST NOT independently decide terminal state. Reconcile is the only post-merge execution authority, but terminal permission still comes from the canonical Orchestrator projection. Workflow availability uses one invariant everywhere: a workflow is usable unless its state explicitly starts with `disabled`.


### Control-plane event boundary

Observer ingress is product evidence only. `workflow_run` subscribes to `CI`, never to GPTAuto Observer/Executor/Reconcile or Release. Reconcile is the sole post-merge authority: it dispatches and verifies post-merge CI/Release and writes terminal evidence directly. Control-plane workflow completions MUST NOT feed back into Observer. Task/head idempotency remains a safety net, not the primary loop-prevention mechanism.


## 8. Task Protocol v2 / 持久任务与 Continuation Host

v0.14.0 将“任务生命周期”和“ChatGPT execution 生命周期”彻底分离。唯一终态权威是 `gptauto.task-state/v2`。一次 foreground execution 结束不会结束 Task；非 DONE 状态必须持久化。REPAIR_REQUIRED 产生绑定 task_id、generation、current head 的 continuation_key，供 GPTWork 等 Continuation Host 恢复同一任务和 PR。旧 Exit Guard/Completion Lease 仅保留为兼容视图，不得成为第二决策权威。

## Task Protocol v2 / Persistent tasks and Continuation Hosts

v0.14.0 separates task lifetime from ChatGPT execution lifetime. The sole terminal authority is `gptauto.task-state/v2`. Ending one foreground execution never closes a non-DONE task. REPAIR_REQUIRED emits a continuation_key bound to task_id, generation, and current head so a Continuation Host such as GPTWork can resume the same task and PR. Legacy Exit Guard/Completion Lease fields are compatibility views only and MUST NOT become a second decision authority.
