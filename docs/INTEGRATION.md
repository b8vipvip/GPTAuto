# GPTAuto v0.4 集成与自动同步 / Integration & Auto Sync

## 中文（默认）

v0.4 将真实 ChatGPT/Work 开发任务与 TASK_ID 绑定。宿主在开始执行用户最终目标时先运行 `gptauto init`，随后用 `gptauto bind` 持续写入 branch、head SHA、PR、Actions Run、merge SHA 和 Artifact。这样 TASK_ID 不再只是 CI smoke-test ID。

`gptauto latest` 可读取当前仓库最近登记的任务。任务注册表位于 `.gptauto/tasks/index.json`。真实宿主应把 task state/registry 作为 Artifact 或持久状态保存，而不是依赖聊天上下文。

### 自动同步

每个消费仓库安装 `consumer-template/gptauto-sync.yml` 为 `.github/workflows/gptauto-sync.yml`。它每 6 小时检查 canonical GPTAuto，发现 runtime/action 变化后自动建立同步 PR，由目标仓库自己的 CI 验证后再合并。

这种 pull 模式不要求 GPTAuto 仓库保存能写入所有项目的长期 PAT。若以后要求发布后立即推送，可再升级为 GitHub App/repository_dispatch。

## English

v0.4 binds real ChatGPT/Work engineering runs to one durable TASK_ID and records branch, commit, PR, workflow run, merge and artifact references. Consumer repositories periodically pull the canonical runtime and open a CI-gated update PR without granting GPTAuto a cross-repository write token.
