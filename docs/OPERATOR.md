# GPTAuto v0.5 操作与验证 / Operator UX

## 修改项目时如何启动真实 GPTAuto 任务

对 ChatGPT/Work 明确写：

> @GitHub 使用 GPTAuto 执行 GPTWork 的本次修改。开始时创建真实 TASK_ID，并在整个任务中持续绑定 branch、commit、PR、Actions Run、merge SHA 和 Artifact；不要使用 smoke-test TASK_ID。按我的最终目标持续执行到 DONE/BLOCKED，完成后告诉我 TASK_ID。

完成后验证时只需要：

> @GitHub 检查 GPTWork 最近一次真实 GPTAuto 任务，自动定位 TASK_ID、PR、Actions Run 和 gptauto Artifact，读取日志并验证 GPTAuto 是否正常工作。

如果你已经知道 ID，也可以说：

> @GitHub 检查 GPTWork 的 GPTAuto 任务 GA-xxxxxxxxxxxx，读取对应日志并验证执行链。

CLI 可运行 `gptauto report`，它会返回最近 TASK_ID、Artifact 名、绑定引用和可直接交给 ChatGPT 的分析提示词。

## 自动同步

v0.5 将消费仓库检查频率从每 6 小时缩短为每小时。同步工作流还会同步自身模板，因此后续同步机制的改进也能下发。发现新版本时建立 PR，并尝试启用 GitHub auto-merge；只有目标仓库允许 auto-merge 且所需检查满足时才会自动合并，否则 PR 保持打开。

不在 canonical GPTAuto 保存跨仓库 PAT。真正的“发布后秒级广播”仍需要 GitHub App 或一个有多个仓库权限的凭据，v0.5 不会为了速度引入这种高权限秘密。

## English

Use a real GPTAuto task ID for the whole ChatGPT/Work engineering run, bind repository references as execution progresses, and use `gptauto report` for a shareable diagnostic locator. Consumer sync now runs hourly, self-updates its sync workflow, opens a PR, and attempts GitHub auto-merge after repository checks pass.
