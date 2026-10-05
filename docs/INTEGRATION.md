# GPTAuto v0.6.3 集成与自动同步 / Integration & Auto Sync

## 中文（默认）

GPTAuto 将真实 ChatGPT/Work 开发任务与 TASK_ID 绑定。宿主在开始执行用户最终目标时先运行 `gptauto init`，随后用 `gptauto bind` 持续写入 branch、head SHA、PR、Actions Run、merge SHA 和 Artifact。仓库侧 Observer 则负责在没有 native-host telemetry 时，从 GitHub 事件恢复同一任务的生命周期。

### v0.6.3：跨事件统一 TASK_ID

消费仓库的 `gptauto-observer.yml` 监听 PR、main push、`CI` / `Release` workflow completion 和 Release published。对于 push、main CI、Release 等没有直接 PR number 的事件，Observer 会先使用 commit → pull requests API 反查原 PR，再生成 TASK_ID。因此同一真实任务可以保持：

    PR → PR CI → Merge → main push → main CI → Release = one TASK_ID

版本型开发标题（如 `v0.5.81: ...`）或标题中的“release / publish / 发布 / 正式版”等语义会把任务恢复为 Release 型 DoD；`chore:` / `docs:` / `test:` / `ci:` / `build:` / `deps:` / `refactor:` 等维护标题具有非发布优先级，即使 PR 正文为了描述验证边界而出现 Release 字样也不会误判。PR merged 只进入 `VERIFY`；非发布任务至少等 main CI 成功，发布任务同时要求 main CI 与 Release 成功才进入 `DONE`。Observer 每次都会回查 merge SHA 上历史成功的 `CI` 与 `Release` run，所以 Release 先于 CI 或 CI 先于 Release 都不会卡死在 `VERIFY`。

模板默认跟踪名为 `CI` 和 `Release` 的工作流。消费仓库若使用其他工作流名称，应在 `workflow_run.workflows` 和模板中的 CI 查询条件同步调整。

### 自动同步

每个消费仓库安装 `consumer-template/gptauto-sync.yml` 为 `.github/workflows/gptauto-sync.yml`。它不再定时轮询 canonical GPTAuto。只有 GPTAuto 发布新版本时，canonical Release 才发送一次 release dispatch，消费仓库据此建立同步分支并创建 CI-gated PR。

GitHub 有一个仓库级安全开关：默认 `GITHUB_TOKEN` 即使声明 `pull-requests: write`，在关闭 **Allow GitHub Actions to create and approve pull requests** 时仍不能创建 PR。v0.6.3 不再把这种平台策略误报成同步代码故障：

- 推荐配置 repository secret `GPTAUTO_GITHUB_TOKEN`，统一承担 Sync、Executor、Repair push、PR/merge 与 Reconcile；旧 `GPTAUTO_SYNC_TOKEN` / `GPTAUTO_EXECUTOR_TOKEN` 只作为迁移兼容。
- 当操作不涉及 workflow 文件且仓库策略允许时，部分步骤仍可安全回退到 `github.token`；需要写 `.github/workflows/` 或自主 repair push 的步骤不会依赖不稳定的默认 token 权限。
- canonical GPTAuto 仓库也应配置 `GPTAUTO_GITHUB_TOKEN`，并授予对注册消费仓库的必要访问权限，用于新版本 release fan-out 与收敛检查。

Copilot CLI 使用独立的 `GPTAUTO_COPILOT_TOKEN`，不与仓库写权限 PAT 混用。

## English

v0.6.3 correlates PR, post-merge push, CI and release events back to the originating pull request before deriving the observer TASK_ID. A merged PR is no longer terminal evidence. Normal tasks wait for successful post-merge CI; release-oriented tasks wait for both post-merge CI and release success.

From v0.15.10, `GPTAUTO_GITHUB_TOKEN` is the primary credential for Consumer Sync, Executor, Repair push, PR/merge, and Reconcile. Legacy `GPTAUTO_SYNC_TOKEN` and `GPTAUTO_EXECUTOR_TOKEN` remain accepted as migration fallbacks. `GPTAUTO_COPILOT_TOKEN` stays isolated for Copilot CLI.
