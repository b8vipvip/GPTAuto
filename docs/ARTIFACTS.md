# GPTAuto Artifact 自动归档 / Artifact Archiving

## 中文（默认）

GPTAuto v0.3.1 提供仓库内可复用的 GitHub Actions 上传动作：

    ./.github/actions/upload-gptauto-log

宿主项目在运行 GPTAuto 后传入 Task ID，即可把：

    .gptauto/logs/<TASK_ID>/

自动归档为：

    gptauto-<TASK_ID>

Artifact 默认保留 30 天。任务目录包含 `task.log`、`state.json`、`events.jsonl`、`summary.md`。

推荐宿主工作流：

    - name: Upload GPTAuto diagnostics
      if: always()
      uses: ./.github/actions/upload-gptauto-log
      with:
        task-id: ${{ steps.gptauto.outputs.task-id }}
        retention-days: '30'

这里使用 `if: always()` 很重要：即使任务 BLOCKED 或后续步骤失败，也应保留诊断证据。

### 一键诊断

仓库还提供 `GPTAuto Diagnostics` 手动工作流。已有 JSON task state 时，可以传入 Task ID 与 task_state_json，工作流会重新生成审计目录并上传 Artifact。

以后告诉 ChatGPT **仓库名 + Task ID**；若还需要定位 Actions，可再给 Run ID。连接 GitHub 后，ChatGPT 可检查对应 workflow run、jobs、失败日志和 Artifact 元数据。若当前连接不能直接下载二进制 Artifact，则下载 Artifact 后把 `task.log` 或整个压缩包拖入聊天即可。

### 安全

不要把 token、cookie、password、secret 或完整 Authorization header 写入 evidence。Artifact 可能保存到 GitHub 一段时间，应按仓库敏感级别调整 retention-days。

## English

GPTAuto v0.3.1 ships a reusable local composite action that uploads `.gptauto/logs/<TASK_ID>/` as `gptauto-<TASK_ID>`. Use it with `if: always()` so failed or blocked executions still retain evidence. The default retention is 30 days.
