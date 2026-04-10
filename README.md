# 我的 Codex Skills

这是我个人用的 skill 仓库。

## 目录结构

```text
skills/
  export/
  test-init/
```

## Skill 列表

| Skill | 作用 | 目录 |
| --- | --- | --- |
| `export` | 导出当前 Codex 会话为可读的 Markdown 文件 | `skills/export` |
| `test-init` | 给 SPA 风格的网页游戏 demo 接入可复用的测试入口协议 | `skills/test-init` |

## Skill 说明

### `export`

`export` 这个 skill 用来把当前 Codex 会话导出成一个可读的 Markdown 文件。

它现在可以：

- 导出当前会话内容
- 保留原始 rollout 顺序
- 包含聊天消息、工具调用、工具输出和运行时事件
- 记录相关源码文件路径和 memory 文件位置
- 支持按 rollout 文件或 session id 指定导出目标

使用方式：

- 在需要导出当前会话记录时调用这个 skill
- 按提示提供文件名和输出目录，或者直接使用默认值

技能目录在 `skills/export`。

### `test-init`

`test-init` 这个 skill 用来给 SPA 风格的网页游戏 demo 项目接入一个稳定的测试入口，方便后续其他 skill 直接进入指定状态进行测试。

它现在可以：

- 检查项目是不是适合接入 test entry
- 接入基于 URL 的测试入口协议
- 提供 `window.__TEST_ENTRY__` 作为测试桥接入口
- 支持跳过登录、注入测试状态、直接打开目标页面
- 输出一份 test entry summary，给其他 skill 当作公共接口来用

使用方式：

- 在网页游戏 demo 需要做测试入口初始化时调用这个 skill
- 它会先检查项目结构，再按约定接入 test-entry 协议
- 接入完成后，其他 skill 可以通过 URL 参数或 `window.__TEST_ENTRY__` 使用这个入口

技能目录在 `skills/test-init`。
