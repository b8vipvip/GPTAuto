# GPTAuto v0.3 可观测性与审计日志 / Observability & Audit Log

## 中文（默认）

GPTAuto v0.3 每次任务状态持久化时生成可审计文件。默认目录：

    .gptauto/logs/<TASK_ID>/
      task.log
      state.json
      events.jsonl
      summary.md

- `task.log`：最适合人工阅读和直接发给 ChatGPT。
- `state.json`：完整任务状态、Dynamic Gates、DoD、evidence、repair 次数。
- `events.jsonl`：逐事件审计轨迹，适合分析 WAITING、失败、修复和状态转换。
- `summary.md`：最终摘要，快速判断 DONE/BLOCKED、Gate 与 DoD 完成率。

默认 `.gptauto/task.json` 是当前任务恢复点。日志根目录可用 CLI 全局参数 `--log-root` 改写。

### 如何交给 ChatGPT 分析

最方便的方式是告诉 ChatGPT：**仓库名 + GPTAuto Task ID**，例如“检查 qnbot 的 GPTAuto 任务 GA-xxxx”。如果日志已经提交/上传为 GitHub artifact 且连接可读，ChatGPT 可以直接定位；否则上传该任务的 `task.log` 或 `state.json`。要完整诊断时把整个任务目录打包上传。

敏感信息：evidence 可能包含 URL、错误输出或运行元数据。宿主不得把 token、secret、cookie、密码写入 evidence/log。

## English

GPTAuto v0.3 writes four audit artifacts under `.gptauto/logs/<TASK_ID>/`: a human-readable log, machine state JSON, JSONL event stream, and Markdown summary. Share the repository plus Task ID when the logs are repository-accessible; otherwise attach `task.log` or `state.json`.
