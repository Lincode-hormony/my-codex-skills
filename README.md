# 我的 Codex Skills

这是我个人维护的 Codex skill 仓库，主要用于沉淀可重复复用的本地工作流。

## 目录结构

```text
skills/
  export/
  test-init/
  test-start/
```

## Skill 列表

| Skill | 用途 | 路径 |
| --- | --- | --- |
| `export` | 导出当前 Codex 会话为可读的 Markdown 记录 | `skills/export` |
| `test-init` | 为 SPA 风格网页游戏 demo 建立或扩展可复用的 test-entry 契约 | `skills/test-init` |
| `test-start` | 启动本地开发服务，并返回一个经过契约校验的启动链接 | `skills/test-start` |

## 安装方式

克隆这个仓库后，把需要的 skill 目录复制到本机的 Codex skills 目录即可。

常见本地目录：

```text
C:/Users/<你的用户名>/.codex/skills/
```

例如：

```powershell
Copy-Item -Recurse -Force .\skills\test-start C:\Users\<你的用户名>\.codex\skills\test-start
Copy-Item -Recurse -Force .\skills\test-init C:\Users\<你的用户名>\.codex\skills\test-init
```

## `test-start`

`test-start` 用来消费项目里已经存在的 `test-entry-summary` 契约，并返回一个可直接使用的本地启动链接。

适用场景：

- 启动当前项目的本地 test-entry 环境
- 只拿一个可用链接，而不是重新读一遍项目内部实现
- 直接打开某个已支持页面
- 避免端口冲突
- 当页面不支持时，把流程引导回 `test-init`

### 它会做什么

- 校验 `test-entry-summary.json`
- 规划一个当前机器上空闲的本地端口
- 用平台安全的方式启动 dev server
- 校验 HTTP 是否真正可访问
- 返回一个经过契约约束的唯一启动链接

### 它不会做什么

- 不修改项目的 test-entry 基座
- 不编造不受支持的 screen
- 不通过 UI 手动点来模拟不受支持页面
- 不会只因为进程存在或端口在监听就直接返回链接

### 一个很重要的执行规则

skill 自带的脚本路径要从 skill 目录解析，但脚本执行时的工作目录必须保持在**目标项目根目录**。

正确模式：

```powershell
python C:/Users/<你的用户名>/.codex/skills/test-start/scripts/check_summary.py
```

注意：执行这条命令时，你的 shell 当前目录应当已经是目标项目根目录。

### 当前启动策略

`test-start` 现在会优先走项目契约里定义的最稳妥路径：

- 如果项目契约里定义了 `preferred_direct_launch`，那么“基础启动”会优先返回这个直达链接，而不是强行返回普通首页。
- 如果你请求的是某个具体 screen 或 preset，且契约支持 `bypass`，那么在你没有明确指定别的 auth 模式时，会默认补上 `testAuth=bypass`。
- 如果 normal launch 返回的 URL 里包含契约定义的预处理参数，那么必须原样返回，不能再降级成裸 `base_url`。

### 典型用法

让 Codex 启动并给一个基础链接：

```text
$test-start 给我一个基础链接
```

可能得到的结果：

```text
http://127.0.0.1:4174/?testEntry=1&testScreen=champion-select&testAuth=bypass&testPreset=champion-select-default
```

如果你要直达某个模块：

```text
$test-start 打开 shop 页面
```

期望结果类似：

```text
http://127.0.0.1:4174/?testEntry=1&testScreen=shop&testAuth=bypass
```

### 主要脚本

- `scripts/check_summary.py`
- `scripts/plan_dev_server.py`
- `scripts/start_dev_server.py`
- `scripts/finalize_launch.py`
- `scripts/record_verified_alias.py`

## `test-init`

`test-init` 是这套流程里的“契约生产者”，负责为项目建立或扩展持久化的 test-entry 能力。

适用场景：

- 项目里还没有有效的 `test-entry-summary`
- 下游 skill 返回了 `next_action=use-test-init`
- 某个页面确实不在当前契约里，需要永久加入

### 它会产出什么

- 基于 URL 的 `testEntry` 协议支持
- 只在 dev/test 环境暴露的 `window.__TEST_ENTRY__`
- 稳定的公开 screen 名称
- 更新后的 `test-entry-summary.json`

### 同样重要的执行规则

和 `test-start` 一样，脚本路径要从 skill 目录解析，但执行时的工作目录要保持在目标项目根目录。

常见执行形式：

```powershell
python C:/Users/<你的用户名>/.codex/skills/test-init/scripts/check_summary.py
python C:/Users/<你的用户名>/.codex/skills/test-init/scripts/inspect_project.py
```

### 典型用法

给一个项目初始化 test-entry：

```text
$test-init 给这个项目补 test-entry
```

或者扩展已有契约：

```text
$test-init 把 backpack 页面正式加进 test-entry-summary
```

## 推荐工作流

对于 SPA 风格网页游戏 demo，推荐按这个顺序使用：

1. 先用 `test-init` 建立或扩展 test-entry 契约。
2. 再用 `test-start` 启动项目并返回一个经过校验的链接。
3. 后续截图、页面验证、视觉检查等 skill 都建立在这个返回链接之上。

## 备注

- 这些 skill 主要面向 SPA 风格网页游戏 demo。
- `test-start` 是契约消费者。
- `test-init` 是契约生产者。
- 如果项目实现和契约不一致，应优先回到 `test-init` 修正，而不是继续编造临时 URL。
