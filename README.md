# GPTAuto

[中文](#中文) · [English](#english)

<a id="中文"></a>
## 中文（默认）

GPTAuto 是一个**按最终目标持续执行**的 GitHub 工程工作协议与参考实现。v0.4.0 已加入可观测性、审计日志与 GitHub Actions Artifact 自动归档，让每个任务的 Gate、DoD、evidence、修复次数和最终状态都有机器可验证轨迹。它不再把所有任务强制塞进固定的“PR → CI → Merge → Release”流水线，而是先理解目标、生成该任务自己的 Definition of Done（DoD），再动态选择真正需要的 Gate。

### 核心原则

**任务边界由最终目标决定，不由对话轮次决定。**

流程模型：

    GOAL → PLAN / DoD → EXECUTE selected gates → VERIFY DoD → DONE

可选 Gate 包括：`INSPECT`、`IMPLEMENT`、`COMMIT`、`PR`、`PR_CI`、`MERGE`、`MAIN_CI`、`RELEASE`、`DEPLOY`、`RUNTIME_VERIFY`。

例如：
- “修改 README 并提交”不强制 Merge/Release。
- “修复 Actions 直到 CI 全绿”以 CI 目标达成为终态，不强制 Release。
- “把代码合并到 main”要求 Merge，但不自动要求发布版本。
- “修复并发布 v1.2.3 正式版”才选择 PR、CI、Merge、main CI、Release 等必要 Gate。

`queued/running` 仍然只是 WAITING；但只有当 CI 本身属于当前任务的动态计划时，它才会阻止 DONE。所有 DoD 条目必须有通过状态和证据，才能进入 DONE。

### 快速开始

    python -m unittest discover -s tests -v
    python -m gptauto.cli init --goal "把代码合并到 main" --repo owner/repo --out task.json
    python -m gptauto.cli status task.json

可以使用多个 `--gate` 和 `--done` 显式覆盖自动规划，供 GPTWork 等宿主的推理层传入更准确的计划。

v0.4.0 新增真实任务 TASK_ID 绑定与任务注册表：`gptauto bind` 可持续关联 branch、commit、PR、Actions Run、merge 和 Artifact，`gptauto latest` 可定位最近任务。消费仓库还可安装 `consumer-template/gptauto-sync.yml`，定时从 canonical GPTAuto 拉取更新并自动建立 CI 验证 PR。\n\n默认审计日志生成在 `.gptauto/logs/<TASK_ID>/`，包含 `task.log`、`state.json`、`events.jsonl`、`summary.md`；宿主工作流可使用内置 upload action 自动归档为 `gptauto-<TASK_ID>` Artifact。详见 `docs/OBSERVABILITY.md`、`docs/PROTOCOL.md` 与 `docs/INTEGRATION.md`。

<a id="english"></a>
## English

GPTAuto is a goal-bound GitHub engineering workflow protocol and reference implementation. Instead of forcing every task through a fixed PR/CI/Merge/Release pipeline, it derives a task-specific Definition of Done and selects only the gates required by the requested outcome.

Core lifecycle:

    GOAL → PLAN / DoD → EXECUTE selected gates → VERIFY DoD → DONE

Available gates include `INSPECT`, `IMPLEMENT`, `COMMIT`, `PR`, `PR_CI`, `MERGE`, `MAIN_CI`, `RELEASE`, `DEPLOY`, and `RUNTIME_VERIFY`.

A documentation commit does not inherently require a release. A “CI green” goal can finish at CI. A merge goal requires merge evidence but not a release. A release goal selects the full release-related chain. Asynchronous Actions states are WAITING only when their gate is part of the current plan.

Every DoD criterion requires explicit passed evidence before the task can enter DONE.
