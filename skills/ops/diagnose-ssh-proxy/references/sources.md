# 官方来源与核对点

> 公开版本：服务器与出口IP已替换为文档示例地址（203.0.113.0/24），不能原样用于连接；执行前替换为实际值。

整理日期：2026-10-18。以下内容需要随目标软件版本核对；文档访问日期不代表用户已经升级。

| 官方来源 | 核对点 |
| --- | --- |
| [OpenSSH ssh_config](https://man.openbsd.org/ssh_config) | Host 匹配、配置优先级、IdentityFile、ClearAllForwardings、RemoteForward、ExitOnForwardFailure |
| [OpenSSH ssh](https://man.openbsd.org/ssh) | -R 的监听方向与本地目标，-N/-T/-G/-v 选项 |
| [OpenSSH sshd_config](https://man.openbsd.org/sshd_config) | 转发策略、监听限制、账户认证策略；在有效配置与日志支持后才修改 |
| [VS Code SSH 排错](https://code.visualstudio.com/docs/remote/troubleshooting) | 密钥、Windows 权限、Remote SSH 问题定位 |
| [VS Code 1.98 Remote 更新](https://github.com/microsoft/vscode-docs/blob/main/remote-release-notes/v1_98.md) | Remote SSH 0.118.0 引入 remote.SSH.httpProxy/httpsProxy；支持别名映射或字符串，为远程 Server 安装及启动导出变量 |
| [VS Code WSL 远程扩展代理](https://code.visualstudio.com/docs/remote/wsl) | 远程扩展复用本地代理的背景，http.useLocalProxyConfiguration 与远程设置；用于同类运行位置问题时应核对实际版本 |
| [VS Code Remote SSH](https://code.visualstudio.com/docs/remote/ssh) | Ports 面板与本地端口映射、远程设置 |
| [curl 手册](https://curl.se/docs/manpage.html) | --proxy、--noproxy、-q、write-out、超时及退出码、代理环境变量 |
| [GNU Bash 启动文件](https://www.gnu.org/software/bash/manual/html_node/Bash-Startup-Files.html) | 交互 Shell、登录 Shell、bashrc 和 profile 的不同加载条件 |
| [Codex CLI](https://developers.openai.com/codex/cli) | 官方独立安装器及安装后的验证；访问时跳转至 ChatGPT Learn |
| [Codex 认证](https://developers.openai.com/codex/auth) | headless 场景设备码登录、账户或工作区开关、认证缓存保护；访问时跳转至 ChatGPT Learn |

讲解时用自己的话概括。只引用支持当前结论的来源；本次机器的状态以用户日志或实际执行结果为准，不能由官方文档推断。
