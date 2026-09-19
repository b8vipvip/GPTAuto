# Repository Observer / 仓库自动观察

GPTAuto v0.6 增加仓库侧 Observer，使消费仓库即使被另一个 ChatGPT/Work 会话修改、且该宿主没有主动调用 GPTAuto CLI，也会从 GitHub 的 PR/push 事件自动生成可检索的 GPTAuto Artifact。

## 两种证据来源

- `native_host`: ChatGPT/Work 宿主主动创建 GPTAuto 任务并持续绑定目标、Gate、DoD、PR、Actions、Merge。证据最完整。
- `repository_observer`: GitHub 仓库根据实际 PR/push 自动生成。它能证明仓库里实际发生了什么，但不能伪造另一个聊天内部没有记录的推理、计划或“是否曾想过继续执行”。

Observer 的 Artifact 仍使用 `gptauto-GA-...`，并在 `state.json` / `summary.md` 标记 `provenance=repository_observer` 和 `task_type=observed`。同一个 PR 的 synchronize/close 使用稳定 TASK_ID，方便跨阶段关联。

## 用户体验

在其它 ChatGPT 会话完成 GPTWork 修改后，可以在新的会话直接说：

> @GitHub 刚刚我让 ChatGPT 执行了一轮 GPTWork 修复。检查 GPTWork 最近一次真实开发变更对应的 GPTAuto 日志、PR 和 Actions，排除 smoke/sync 任务，分析 GPTAuto 的工作状态和效果。

分析时应优先 native_host 证据；若没有，则使用 repository_observer，并明确哪些结论只能由 GitHub 外部行为支持。

## 自动安装

`gptauto-sync.yml` 会把 `gptauto-observer.yml` 同步到消费仓库，因此后续 GPTAuto 升级会自动下发 Observer。
