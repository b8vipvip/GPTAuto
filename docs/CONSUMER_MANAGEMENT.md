# GPTAuto Consumer Management

## 中文（默认）

GPTAuto 消费仓库采用 **一个入口 Workflow + PR 管理** 的方式安装、更新和卸载。入口文件是：

```text
.github/workflows/gptauto-sync.yml
```

它来自 canonical 仓库：

```text
b8vipvip/GPTAuto/consumer-template/gptauto-sync.yml
```

### 新仓库安装

首次接入只需要把 canonical `consumer-template/gptauto-sync.yml` 放到目标仓库的：

```text
.github/workflows/gptauto-sync.yml
```

然后在目标仓库配置需要的 secrets：

- `GPTAUTO_GITHUB_TOKEN`：统一用于 Consumer Sync、Executor、Repair push、PR/merge 与 Reconcile。建议使用 fine-grained PAT，仅授予需要管理的仓库；Repository permissions 至少包含 **Contents: Read and write**、**Pull requests: Read and write**、**Workflows: Read and write**、**Actions: Read and write**、**Checks: Read**。
- `GPTAUTO_COPILOT_TOKEN`：可选但推荐独立配置，仅用于 Tier 2 Copilot CLI；需要 **Copilot Requests** account permission。

从 v0.15.10 起，新安装只需要以上两个逻辑 Token。旧的 `GPTAUTO_SYNC_TOKEN`、`GPTAUTO_EXECUTOR_TOKEN` 与 canonical 仓库中的 `GPTAUTO_CONSUMER_TOKEN` 继续作为兼容回退读取，方便现有仓库渐进迁移。

首次安装后：

1. 打开 **Actions → GPTAuto Consumer Sync → Run workflow**。
2. `operation` 选择 `sync`。
3. Sync 会从 canonical GPTAuto 拉取当前版本，生成 `chore/gptauto-sync-vX.Y.Z` 分支并创建 PR。
4. 目标仓库自己的 CI 仍然是安全门。PR 合并后 GPTAuto 才正式生效。

安装的 managed files 包括：

```text
.github/gptauto/
.github/actions/upload-gptauto-log/
.github/workflows/gptauto-sync.yml
.github/workflows/gptauto-observer.yml
.github/workflows/gptauto-executor.yml
.github/workflows/gptauto-repair.yml
.github/workflows/gptauto-reconcile.yml
```

### 更新

正常情况下不需要手工更新。**只有 GPTAuto 发布新版本时**，canonical Release 才会向已注册消费仓库发送一次同步事件，创建/刷新同步 PR，并等待消费仓库 CI、合并以及默认分支 `VERSION` 全部升级成功。升级完成后不会继续定时检查版本。也可以手工运行：

```text
Actions → GPTAuto Consumer Sync → Run workflow → operation=sync
```

同步是原子的：如果 canonical 版本包含 workflow 变化而 `GPTAUTO_GITHUB_TOKEN`（或兼容的旧 `GPTAUTO_SYNC_TOKEN`）缺少 Workflows write，Sync 不会只更新一部分文件或错误提升 VERSION，而会留下明确的阻塞 issue。

### 卸载

v0.15.1 起不需要手工找文件删除：

```text
Actions → GPTAuto Consumer Sync → Run workflow → operation=uninstall
```

Uninstall 会创建/刷新：

```text
chore/gptauto-uninstall
```

并提交一个卸载 PR。合并该 PR 后，上述 GPTAuto-managed `.github` runtime/action/workflow 文件会被移除，包括 `gptauto-sync.yml` 自身。

为避免误删业务数据，卸载**不会**自动删除：

- 产品源码或产品 workflow；
- `.gptauto/` 下已有 task state / audit / logs；
- `.gptauto/repair-rules.json` 等仓库自定义策略；
- Repository secrets。

确定不再使用 GPTAuto 后，可在仓库 Settings 中手工删除 `GPTAUTO_GITHUB_TOKEN`、`GPTAUTO_COPILOT_TOKEN`，以及迁移期遗留的 `GPTAUTO_SYNC_TOKEN`、`GPTAUTO_EXECUTOR_TOKEN`。

### 最便捷的管理方式

对于已安装的仓库，后续只有两个动作：

```text
sync       = 安装/升级到 canonical 当前版
uninstall  = 生成安全卸载 PR
```

对于一个全新的仓库，只需要先引入 **一个** `gptauto-sync.yml`，之后所有 GPTAuto runtime/workflow 都由它管理，不需要逐个复制五个 workflow。

如果通过 ChatGPT GitHub 连接器管理仓库，也可以直接要求：

```text
给 owner/repo 安装最新 GPTAuto
```

或：

```text
从 owner/repo 卸载 GPTAuto
```

执行时仍应遵守同样的 PR、安全权限和 CI gate，不直接绕过仓库保护规则。

## English

Consumer management is intentionally reduced to one bootstrap/manager workflow: `.github/workflows/gptauto-sync.yml`. A new repository needs only that one canonical file. Running it with `operation=sync` installs or updates the complete managed runtime through a CI-gated PR. Running it with `operation=uninstall` prepares a PR that removes only GPTAuto-managed `.github` files, including the manager workflow itself. Product code, `.gptauto` task/audit data, repository-specific repair policy, and secrets are preserved intentionally.
