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

只要 Completion Lease 仍为 active，任何 commit、PR、部分 CI 成功、repair request、merge 或 release-in-progress 都只能作为进度证据，不能作为“任务完成”的依据。Executor 必须公开持久化的 ACTIVE completion guard；只有 Reconcile 产生 terminal DONE evidence 并释放该 Lease 后，宿主/前台代理才允许向用户报告工程任务完成。对话超时或前台会话结束不能覆盖此契约。

### 7. 修复

失败 Gate 消耗有界 repair budget。修复动作由宿主推理层决定，完成后重新验证当前计划所要求的 Gate；不应因为历史上存在 PR/CI/Release 阶段而强制重新走无关步骤。

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

While a Completion Lease is active, commits, PR creation, partial CI success, repair requests, merges, and releases in progress are progress evidence only. Executor publishes a durable ACTIVE guard. A host/foreground agent may report engineering completion only after Reconcile emits terminal DONE evidence and releases the lease. Chat/session termination never overrides this contract.

### Waiting and blocking

Asynchronous states are WAITING only for gates selected by the plan. BLOCKED is reserved for missing permission/credentials, material product ambiguity, unauthorized destructive action, exhausted repair budget, or an unrecoverable external platform condition.
