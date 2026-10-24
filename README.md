# Codex OneDrive Project Memory

通过 OneDrive 在多台 Windows 电脑之间共享 Codex 的项目经验、工作流、决定和进度。每台电脑独立运行；通过 **Skill + Hooks + 不可变 Markdown 笔记** 接续项目。

这是一套用户自建工具，不是 OpenAI 官方同步服务。它不会同步 Codex 原始聊天、侧栏任务、登录信息或内部数据库，也不会修改模型参数。自动提炼由当前会话中的智能体完成，需 Hooks 成功运行并遵守 Skill。

## 你可以得到什么

- 项目分开存储，两台电脑用相同项目编号对应不同本地路径。
- 每台电脑生成独立设备编号；每轮记录独立文件，避免互相覆盖。
- 会话开始和提交新消息时读取项目笔记；结束前保存新增知识或跳过。
- 本地队列支持共享目录暂时不可用后的重试；同一轮重复保存幂等。
- Windows PowerShell 5.1 即可运行，无需额外 API Key 或 Python。Python 仅用于开发测试。

## 快速开始

前提：两台电脑已安装支持 `SessionStart`、`UserPromptSubmit`、`Stop` 和 `/hooks` 的 Codex；OneDrive 已登录同一共享位置。脚本不会安装 Codex 或配置 OneDrive 账号。

1. 下载或克隆本仓库，在仓库根目录打开 PowerShell，替换共享路径后运行：

   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Prepare-SharedFolder.ps1 -SharedRoot "D:\OneDrive\Codex-Shared-Memory"
   ```

2. 在共享目录的 `setup\v1.0.0` 中双击 `Install-This-PC.cmd`。看到安装结果后，双击 `Open-Codex.cmd`，在 Codex 内输入 `/hooks`，审阅并信任本工具的三项 Hooks，然后重新打开桌面会话。
3. 在另一台电脑等待 OneDrive 下载完成，在同步后的同一安装目录重复第 2 步。**每台独立安装，不复制第一台的本地配置。**
4. 两台都在安装包目录执行下面的命令；各自替换本地项目路径，保持项目编号相同：

   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Connect-Project.ps1 -ProjectPath "D:\Projects\example" -ProjectId "example-project"
   ```

5. 在已绑定目录打开 Codex 会话，记录一条明确标为测试的经验；等待 OneDrive 同步后，在另一台同项目会话要求读取，并核对来源文件和设备编号。

完整操作、验收、停用和故障排查见 **[安装与使用说明](package/使用与安装说明.md)**。

## 日常操作流程

```text
本机项目目录 → Hooks 识别项目编号 → 读取近期共享笔记
          → 正常处理任务 → Skill 保存经验或跳过
          → 本机 outbox → OneDrive 目录 → OneDrive 上传
          → 另一台下载 → 同项目下一条消息读取
```

换机前检查 OneDrive 已完成同步。另一台无需等待原电脑开机，但只能读取已经同步完成的记录。旧任务不会自动回填；需要在原任务中要求整理经核验的经验和下一步，或在新任务中提供必要材料后形成笔记。

## 目录

| 路径 | 用途 |
| --- | --- |
| `package/` | 可复制到 OneDrive 的完整安装包 |
| `package/onedrive-project-memory/SKILL.md` | 智能体的读取、提炼和保存规范 |
| `package/onedrive-project-memory/scripts/memory.ps1` | 项目绑定、Hooks、读写、队列、状态检查 |
| `scripts/Prepare-SharedFolder.ps1` | 在指定共享目录创建安装入口 |
| `tests/` | 隔离环境中的 Windows 集成测试 |
| [TESTING.md](TESTING.md) | 测试方法和已验证范围 |
| [SECURITY.md](SECURITY.md) | 数据范围、信任与维护注意事项 |

## 关键注意事项

- 不要用 OneDrive 同步整个 `.codex`；每台机器的身份、队列和信任状态应独立。
- 不要直接编辑历史笔记。更正时写新笔记并引用旧文件；校验失败的记录会被跳过。
- 文件写入本地 OneDrive 不代表上传成功；强制中断任务也可能来不及提炼最后一轮。
- 项目路径未绑定时会使用设备独立编号，避免混入同名项目；历史笔记不会随绑定自动搬迁。
- 密钥形态检查只是辅助。不要保存密码、令牌、完整会话或不必要的个人信息。
- 云端 Codex 任务不能通过此工具自动访问本地 OneDrive。

## 依据与兼容性

参考 OpenAI 的 [Hooks](https://learn.chatgpt.com/docs/hooks)、[Skills](https://learn.chatgpt.com/docs/build-skills) 和 [AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md) 文档。Codex 的 Hooks 能力和 CLI 参数可能随版本变化；以本机 `/hooks` 和 CLI 帮助为准。

初始版本为 `1.0.0`。本地测试验证的是脚本行为，不等于真实双机 OneDrive 网络链路已验收。
