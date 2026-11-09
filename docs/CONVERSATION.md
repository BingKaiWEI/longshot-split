# 项目缘起（原始对话记录 / Conversation Record）

> 用户明确要求：在 zcode 里面留下原来的对话记录。本文件即该要求的落实。

## 原始对话记录（2026-11-09 23:00，DSH 会话《长照片自动分割插件》）

用户原话：

> "我想在自己的gitee和github上做自己的一个应用，或者做一个插件适配所有agent，可以将手机发送的长照片自适应自动分割，等待会orca完整下来之后你来派发任务给glm，让他来做，可以学习一下别人做插件或者做应用的是什么模板和格式，记得在zcode里面留下原来的对话记录"

## 背景

- orca 安装包已完整落地（E:\Downloads\orca-windows-setup.exe，201.4MB，SHA512 已校验），派发条件已满足。
- 本任务由 DSH 派发台派给 GLM（ZCode）执行，任务包见仓库根目录 TASK.md。

## 项目定位

- CLI 工具：独立应用，人直接用 / 脚本用。
- MCP server（stdio）：适配所有支持 MCP 的 agent（Claude Code / ZCode / Qoder / OpenCode / Cursor / orca 编排的 agent 等）。
