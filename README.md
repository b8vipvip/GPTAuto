# GPTAuto

[中文](#中文) · [English](#english)

<a id="中文"></a>
## 中文（默认）

GPTAuto 是一个**按最终目标持续执行**的 GitHub 工程工作协议与参考实现。v0.6.2 在 v0.6 的仓库侧 Observer 基础上补齐了跨事件任务关联与完成语义：PR、合并后的 main push、main CI、Release 会先反查并绑定到同一个 PR TASK_ID；PR merged 不再直接等于 DONE。版本型开发标题（如 `v0.5.81: ...`）或“发布 / 正式版 / release / publish”语义会恢复 Release 型 DoD；`chore:` / `docs:` / `test:` / `ci:` / `build:` / `deps:` / `refactor:` 等仅引用版本号的维护任务不会被误判为发布。Observer 会回查历史成功的 main CI 与 Release run，因此二者谁先完成都能最终进入 DONE。

### 核心原则

**任务边界由最终目标决定，不由对话轮次决定。**

流程模型：

    GOAL → PLAN / DoD → EXECUTE selected gates → VERIFY DoD → DONE

可选 Gate 包括：`INSPECT`、`IMPLEMENT`、`COMMIT`、`PR`、`PR_CI`、`MERGE`、`MAIN_CI`、`RELEASE`、`DEPLOY`、`RUNTIME_VERIFY`。

例如：
- “修改 README 并提交”不强制 Merge/Release。
- “修复 Actions 直到 CI 全绿”以 CI 目标达成为终态，不强制 Release。
- “把代码合并到 main”要求 Merge，但仓库 Observer 仍会等待 post-merge CI 作为完成证据。
- “修复并发布 v1.2.3 正式版”选择 PR、CI、Merge、main CI、Release 等必要 Gate。

`queued/running` 仍然只是 WAITING；但只有当 CI 本身属于当前任务的动态计划时，它才会阻止 DONE。所有 DoD 条目必须有通过状态和证据，才能进入 DONE。

### 快速开始

    python -m unittest discover -s tests -v
    python -m gptauto.cli init --goal "把代码合并到 main" --repo owner/repo --out task.json
    python -m gptauto.cli status task.json

可以使用多个 `--gate` 和 `--done` 显式覆盖自动规划，供 GPTWork 等宿主的推理层传入更准确的计划。

v0.6.2 同时支持 native host TASK_ID 与 repository observer 自动捕获；消费仓库可安装 `consumer-template/gptauto-observer.yml` 与 `consumer-template/gptauto-sync.yml`。Observer 会将 PR/main CI/Release 重新关联到同一个任务；Consumer Sync 支持原生 `github.token`，也支持在仓库禁止 Actions 创建 PR 时使用最小权限 `GPTAUTO_SYNC_TOKEN`。

默认审计日志生成在 `.gptauto/logs/<TASK_ID>/`，包含 `task.log`、`state.json`、`events.jsonl`、`summary.md`；宿主工作流可使用内置 upload action 自动归档为 `gptauto-<TASK_ID>` Artifact。详见 `docs/OBSERVABILITY.md`、`docs/PROTOCOL.md` 与 `docs/INTEGRATION.md`。

<a id="english"></a>
## English

GPTAuto is a goal-bound GitHub engineering workflow protocol and reference implementation. v0.6.2 correlates PR, post-merge push, main CI and release events back to one PR-derived TASK_ID. Merge is no longer terminal observer evidence: normal merged tasks wait for post-merge CI, while versioned/release-oriented tasks wait for both post-merge CI and successful release evidence.

Core lifecycle:

    GOAL → PLAN / DoD → EXECUTE selected gates → VERIFY DoD → DONE

Available gates include `INSPECT`, `IMPLEMENT`, `COMMIT`, `PR`, `PR_CI`, `MERGE`, `MAIN_CI`, `RELEASE`, `DEPLOY`, and `RUNTIME_VERIFY`.

Consumer Sync can use the native repository `GITHUB_TOKEN` where Actions is allowed to create PRs, or an optional least-privilege `GPTAUTO_SYNC_TOKEN` when that repository policy is disabled. Policy denial now leaves a prepared sync branch plus an actionable workflow summary instead of a misleading sync failure.
