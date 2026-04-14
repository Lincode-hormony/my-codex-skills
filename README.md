# my-codex-skills

这个仓库放的是我自己维护的 Codex skills，目前主要是 `test-init`、`test-start`、`test-screenshot` 这套 build + preview 测试链路。

## 目录

```text
skills/
  export/
  test-init/
  test-start/
  test-screenshot/
```

## 三个 test skill 分别做什么

### `test-init`

给项目接入正式的测试底座，产出和维护 `test-entry-summary`。

适合这些场景：

- 项目第一次接入测试体系
- 现有 `test-entry-summary` 缺失或失效
- 需要正式新增一个 screen、preset 或 ready contract

常见说法：

```text
$test-init 给这个项目补测试接入
$test-init 把 shop 页面正式加进测试协议
```

### `test-start`

消费已经存在的 `test-entry-summary`，执行 build + preview，并返回一个校验过的本地启动链接。

适合这些场景：

- 想拿一个可用的测试入口链接
- 想直接打开某个已支持的 screen
- 想确认当前项目的 build-preview 测试链路是否可用

常见说法：

```text
$test-start 给我一个启动链接
$test-start 打开 combat 页面
```

### `test-screenshot`

基于 `test-start` 或现成的测试链接，按 ready contract 截一张当前 screen 的图。

适合这些场景：

- 截某个已接入 screen 的最新画面
- 做页面检查或视觉确认
- 避免靠固定 sleep 猜页面什么时候稳定

常见说法：

```text
$test-screenshot 截一张 combat 页面
$test-screenshot 用这个链接截一张 shop 图
```

## 推荐使用顺序

1. 先用 `test-init` 建立或扩展项目测试协议。
2. 再用 `test-start` 启动 build + preview 并拿到链接。
3. 最后用 `test-screenshot` 按协议截图。

## 安装方式

把需要的 skill 目录复制到本机 Codex 的 skills 目录即可，常见路径：

```text
C:/Users/<你的用户名>/.codex/skills/
```

例如：

```powershell
Copy-Item -Recurse -Force .\skills\test-init C:\Users\<你的用户名>\.codex\skills\test-init
Copy-Item -Recurse -Force .\skills\test-start C:\Users\<你的用户名>\.codex\skills\test-start
Copy-Item -Recurse -Force .\skills\test-screenshot C:\Users\<你的用户名>\.codex\skills\test-screenshot
```

## 说明

- 这套 skill 主要面向前端项目的稳定测试接入和截图流程。
- `test-init` 是协议生产者。
- `test-start` 和 `test-screenshot` 是协议消费者。
- 如果下游 skill 发现项目不在协议里，应该回到 `test-init` 做正式接入，而不是临时猜路径。
