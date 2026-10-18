---
name: diagnose-ssh-proxy
description: "排查 Windows 到 Linux 的 SSH 登录失败、正确密码无法登录、私钥选择或权限错误、VS Code Remote SSH 连接异常、反向转发冲突，以及远程 Codex CLI 的代理和登录问题。用于远程 10801 经 SSH 接入本地 7890 的配置、修复、验证和小白工作流教学。 Use when: SSH登录失败、免密配置、远程10801转发本地7890、VS Code代理、Codex远程安装和小白排错教学。"
---

# SSH 登录与代理排错

按证据逐层定位故障，每次只调整当前失败的一层。用中文说明“在哪台机器执行、预期结果、失败后走哪条分支”。将操作限制在用户授权的主机、账户与配置文件内。

## 先读取相关材料

- 配置或修复时，读取 [操作参考](references/operations.md)。按当前层选择命令，避免一次执行整套修改。
- 解释原理或教学时，读取 [小白工作流](references/beginner-workflow.md)。使用五个关卡及生活例子。
- 延续本次问题时，读取 [本次案例记录](references/incident.md)。将“已验证、推断、未解决”分别对待。
- 涉及当前安装方式、软件设置或服务端策略时，核对 [官方来源](references/sources.md) 对应文档；不要把历史版本配置当作永远有效。

## 1. 确认目标与执行环境

建立参数表：服务器地址、SSH 端口、实际登录账户、连接别名、本地私钥路径、本地 HTTP 代理端口、远程代理端口。默认代理端口示例为本地 7890、远程 10801；不要默认登录账户为 root。

区分本地 Windows PowerShell 与远程 Linux Shell。说明两端的 127.0.0.1 各自指向本机。仅请求必要的日志，不索取服务器密码、私钥内容、验证码或 Codex 认证缓存。

若有执行能力，先只读检查已授权目标；若工具自身报 Permission denied 或 app-server 缺失，记录为执行环境限制，不能据此断定用户服务器认证失败，不能声称已修改配置。

## 2. 隔离并修复 SSH 登录

先检查实际生效配置，再关闭转发进行单独登录测试：

```powershell
ssh -G server111 | Select-String '^(hostname|user|port|identityfile|remoteforward|exitonforwardfailure) '
ssh -vv -o ClearAllForwardings=yes server111
```

把 server111 替换为实际别名。读取日志阶段，不依据“密码肯定正确”猜测故障。

| 证据 | 下一步 |
| --- | --- |
| 超时、拒绝连接、域名解析失败 | 检查目标、端口、网络和 SSH 服务；先不改密钥与代理 |
| Permission denied / authentication failed | 核对实际账户、认证方式、密钥或密码；有服务器控制台时再查看认证日志和有效策略 |
| Enter passphrase for key | 说明正在询问私钥口令；检查代理是否已加载密钥 |
| Authenticated to 后出现 remote port forwarding failed | 认证已通过；转入端口转发层 |
| shell prompt 或远程 whoami 成功 | 登录已通过；继续下一层 |

不要直接开放 root 密码登录、关闭认证保护、关闭主机密钥校验或清空 known_hosts。若登录后立即断开，检查远程命令、shell、会话策略和日志，不能只归为密码错误。

## 3. 配置并验证免密

先保留一个可用登录会话。生成新密钥前检查文件是否存在，禁止覆盖现有私钥。将公钥安装到实际登录账户的 authorized_keys；把无 .pub 后缀的私钥交给客户端。只有日志指向私钥权限不安全时才修复该私钥的 ACL。

验证时使用 ClearAllForwardings；区分服务器密码、私钥口令和 ssh-agent 缓存。BatchMode 失败可能是加密私钥未解锁，不能单凭该结果认定公钥未安装。

## 4. 建立唯一的反向代理通道

推荐将普通登录别名与代理别名分开：server111 负责交互连接，server111-proxy 独占 RemoteForward。先验证本地 7890 HTTP 代理，再开启一次反向隧道，最后从远程显式指定 10801 测试。

解释流量：远程应用访问远程 127.0.0.1:10801，经 SSH 隧道抵达本地 127.0.0.1:7890，再由本地代理访问外网。

遇到绑定失败，核对远程监听、已有隧道以及转发策略。不要盲目 kill sshd、重启 SSH 服务或删除 VS Code Ports 条目。两个 Host 区块不会自动启动两个进程；多个匹配区块可能累积转发，须以 ssh -G 和实际连接为准。

## 5. 持久化、接入应用并分层验收

隧道验证成功后，再写入远程 shell 代理环境文件，按标记加载到 bashrc，保留备份、避免重复行，并提供撤销方式。不要宣称 bashrc 覆盖所有服务或所有用户。环境变量声明代理地址，不会创建监听或隧道。

VS Code 本地 http.proxy 使用本地 7890；remote.SSH.httpProxy/httpsProxy 为远程 Server 安装与启动设置代理，应填远程 10801。远程扩展若错误复用本地代理，再设置远程 http.proxy 和 http.useLocalProxyConfiguration。根据应用实际运行位置和日志确定配置，不能保证每个扩展都遵从相同变量。

Codex CLI 使用官方安装方式，远程无浏览器时优先核对 device-auth 支持。不要使用 pip 安装 Codex；python 缺失与 SSH 认证是不同问题。独立验证 codex --version、登录状态和实际请求。

结束时报告：已改文件、测试结果、尚未完成的层、恢复方式。只有实际输出成功时才写“已解决”；HTTP=200 与 curl_exit=0 仅证明被测请求成功，不能推出所有 OpenAI 功能可用。

## 验收门槛

1. 不带转发能登录正确账户。
2. 公钥认证可用，或明确保留用户选定的认证方式。
3. 本地代理、远程监听及显式代理请求均通过。
4. 新 Shell 的环境代理请求通过；目标应用单独验证。
5. 给小白交付最多五个主步骤，每步附位置、命令、成功信号和错误分支。

