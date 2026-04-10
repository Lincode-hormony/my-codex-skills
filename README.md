# 我的 Codex Skills

这是我个人用的 skill 仓库。

## 目录结构

```text
skills/
  export/
```

## 当前已有的 Skill

### `export`

`export` 这个 skill 用来把当前 Codex 会话导出成一个可读的 Markdown 文件。

它现在可以：

- 导出当前会话内容
- 保留原始 rollout 顺序
- 包含聊天消息、工具调用、工具输出和运行时事件
- 记录相关源码文件路径和 memory 文件位置
- 支持按 rollout 文件或 session id 指定导出目标

技能目录在 `skills/export`。
