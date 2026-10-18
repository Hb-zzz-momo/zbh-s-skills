# 操作参考

> 公开版本：服务器与出口IP已替换为文档示例地址（203.0.113.0/24），不能原样用于连接；执行前替换为实际值。

目录：参数核对；登录；密钥；反向隧道；持久化；VS Code；Codex；恢复。

## 参数核对

示例别名为 server111，服务器为 203.0.113.88。实际账户尚未确认，必须先从已有连接中的 whoami 或云控制台确认。SSH 22 是示例值，须核对。新主机密钥指纹应与可信来源核对，不能通过关闭校验解决错误。

| 配置 | 文件位置 / 执行位置 |
| --- | --- |
| SSH 别名、IdentityFile、RemoteForward | 本地 $env:USERPROFILE\.ssh\config |
| 私钥与 .pub 公钥 | 本地 $env:USERPROFILE\.ssh |
| authorized_keys | 远程实际登录用户的 ~/.ssh |
| shell 代理 | 远程 ~/.config/proxy/ssh-local.sh、~/.bashrc |
| VS Code 本地设置 | Preferences: Open User Settings (JSON) |
| VS Code 远程设置 | 连接后 Preferences: Open Remote Settings (JSON) |

## 登录诊断：本地 PowerShell

```powershell
ssh -G server111 | Select-String '^(hostname|user|port|identityfile|remoteforward|exitonforwardfailure) '
ssh -vv -o ClearAllForwardings=yes server111
```

第一条检查合并后的配置；第二条排除端口转发干扰。需要单次测试密码且账户已确认时，可用：

```powershell
ssh -vv -o ClearAllForwardings=yes -o PubkeyAuthentication=no -o 'PreferredAuthentications=password,keyboard-interactive' server111
```

密码输入不显示字符是正常现象。不要连续重复尝试。若服务器未提供密码认证，客户端参数无法替服务器开启它。

从已有可用会话或云控制台检查远程情况：

```bash
whoami
cat /etc/os-release
```

若有管理员权限，按发行版和实际时间查看 journalctl -u sshd 或 -u ssh、/var/log/secure 或 /var/log/auth.log。先核对日志再决定是否检查账户锁定、PAM、AllowUsers、PermitRootLogin、PasswordAuthentication、Match 等有效策略。不要仅凭失败提示修改服务配置。

## 密钥：本地生成，远程安装公钥

本地 PowerShell，仅在文件不存在时生成：

```powershell
New-Item -ItemType Directory -Path "$env:USERPROFILE\.ssh" -Force | Out-Null
$keyPath = "$env:USERPROFILE\.ssh\id_ed25519_111"
if (-not (Test-Path -LiteralPath $keyPath)) {
    ssh-keygen -t ed25519 -f $keyPath -C 'server111'
}
if (Test-Path -LiteralPath "${keyPath}.pub") {
    Get-Content -LiteralPath "${keyPath}.pub"
}
```

如果只有私钥而没有公钥，不要覆盖私钥；可另行用 ssh-keygen -y 导出公钥。私钥口令由用户选择并本人输入。公钥不会解密或暴露私钥。

远程，在目标账户会话执行，将引号中的说明替换为本地输出的完整公钥一行：

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
touch ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
printf '\n%s\n' '替换为完整的 ssh-ed25519 公钥一行' >> ~/.ssh/authorized_keys
```

此命令必须替换公钥占位文本后执行；重复配置时先检查是否已有同一公钥。检查目录归属须匹配实际账户，不要随意 chmod 整个家目录或 chown 其他用户文件。

仅在真实私钥日志提示 bad permissions 时，本地 PowerShell 对这个私钥修复：

```powershell
$keyPath = "$env:USERPROFILE\.ssh\id_ed25519_111"
$keyUser = whoami
icacls $keyPath /grant:r "${keyUser}:(R)"
icacls $keyPath /inheritance:r
icacls $keyPath /remove:g '*S-1-1-0' '*S-1-5-11' '*S-1-5-32-545'
```

先授予当前账户读取，再移除继承和三类宽泛读取组。按实际 ACL 检查结果决定是否还需调整，保留管理员恢复能力。不要以 .pub 的权限报错为依据改整个 .ssh 目录。

## SSH 配置：两个别名，一条代理隧道

先备份现有 config，再合并下面区块；不要覆盖其他主机。将 ACTUAL_USER 替换为已经核实的登录名，将 22 替换为真实 SSH 端口。检查其他 Host * 或 Include 是否添加了 RemoteForward。

```sshconfig
Host server111 server111-proxy
    HostName 203.0.113.88
    User ACTUAL_USER
    Port 22
    IdentityFile ~/.ssh/id_ed25519_111
    IdentitiesOnly yes
    ServerAliveInterval 30
    ServerAliveCountMax 3

Host server111-proxy
    RemoteForward 127.0.0.1:10801 127.0.0.1:7890
    ExitOnForwardFailure yes
```

本地先验证普通账户登录和免密：

```powershell
ssh -o ClearAllForwardings=yes server111 'whoami'
ssh -o ClearAllForwardings=yes -o BatchMode=yes server111 'whoami'
```

第二条不弹交互输入；加密私钥未加载到 ssh-agent 时可能失败，不能因此断言公钥失效。

本地验证 HTTP 或 mixed 代理端口，再单独开一个 PowerShell 窗口维持隧道：

```powershell
curl.exe --% -q -v --noproxy "" --proxy http://127.0.0.1:7890 --connect-timeout 5 --max-time 20 --write-out "\nHTTP=%{http_code}\n" https://api.ipify.org
ssh -NT server111-proxy
```

上面 --% 是 Windows PowerShell 的停止解析标记，用于兼容旧版 PowerShell 传递空字符串参数；不要把这条 curl.exe 命令原样搬到 Bash。

保持本地代理和隧道窗口打开；无输出且不返回提示符通常表示连接正在维持，但还需做端到端验证。ServerAlive 检测断线，不会自动重新连接。

远程另一个普通会话执行：

```bash
ss -lntp 'sport = :10801'
command curl -q -v -S --noproxy '' --proxy http://127.0.0.1:10801 --connect-timeout 5 --max-time 20 --write-out '\nHTTP=%{http_code}\n' https://api.ipify.org
echo "curl_exit=$?"
```

ss 中 LISTEN 仅证明端口有人监听。HTTP=200、curl_exit=0 且返回外网 IP，才证明此请求完整成功。ExitOnForwardFailure 不检测最终 7890 服务健康。

| 现象 | 下一步 |
| --- | --- |
| remote port forwarding failed | 检查已有监听、另一条隧道、绑定地址、服务端转发策略 |
| curl 退出码 7 | 检查当前请求所连代理是否有监听 |
| curl 退出码 28 | 依据 verbose 阶段区分代理连接、CONNECT、TLS、目标响应超时 |
| 端口监听存在但 curl 失败 | 本地 7890 可能离线或协议不匹配；检查 SSH 窗口与代理日志 |
| 出现 IP 紧贴下一条提示符 | 接口可能不输出换行；使用 write-out 明确状态 |

同一服务器、同一地址的 10801 通常不能由两条 SSH 连接同时绑定。不同服务器可各有自己的 10801；本地一个 7890 可以服务多条连接。识别已有隧道后优先复用，或在确认归属后从其本地窗口 Ctrl+C 停止，不要盲目 kill sshd。

## 远程持久化：隧道成功后再写

适用 Bash 交互式终端。修改前备份已存在的 ~/.bashrc 和代理文件。若已有其他代理方案，先合并并移除冲突赋值；以下标记方案只负责自己创建的加载区块。

```bash
mkdir -p ~/.config/proxy
if [ -f ~/.bashrc ]; then cp -p ~/.bashrc ~/.bashrc.proxy-backup-$(date +%Y%m%d%H%M%S); fi
if [ -f ~/.config/proxy/ssh-local.sh ]; then cp -p ~/.config/proxy/ssh-local.sh ~/.config/proxy/ssh-local.sh.backup-$(date +%Y%m%d%H%M%S); fi
cat > ~/.config/proxy/ssh-local.sh <<'EOF'
export http_proxy="http://127.0.0.1:10801"
export https_proxy="http://127.0.0.1:10801"
export HTTP_PROXY="$http_proxy"
export HTTPS_PROXY="$https_proxy"
export no_proxy="localhost,127.0.0.1,::1"
export NO_PROXY="$no_proxy"
EOF
touch ~/.bashrc
if ! grep -qxF '# BEGIN ssh-local-proxy' ~/.bashrc; then
    cat >> ~/.bashrc <<'EOF'

# BEGIN ssh-local-proxy
source ~/.config/proxy/ssh-local.sh
# END ssh-local-proxy
EOF
fi
source ~/.bashrc
```

若用户之前已有不带标记的 source 行或旧 export，先识别再合并，避免后续值覆盖。bashrc 不自动配置所有用户、systemd、容器、定时任务；登录 Bash 是否读取它取决于 profile 的加载链。旧进程不会追溯继承新环境。隧道断开后，使用该代理的应用可能无法联网。

新终端验证环境和不带 --proxy 的请求：

```bash
printf 'https_proxy=%s\n' "$https_proxy"
curl -q -sS --connect-timeout 5 --max-time 20 --write-out '\nHTTP=%{http_code}\n' https://api.ipify.org
echo "curl_exit=$?"
```

同时确认 no_proxy 没有排除此测试域名，避免把绕过代理的成功当成环境代理成功。https_proxy 使用 http:// 表示连接 HTTP 代理，由 CONNECT 承载 HTTPS，属于正常配置。

## VS Code：按实际运行位置设置

本地 User Settings 合并键，保留其他设置，不要整文件覆盖。推荐按别名限制作用域：

```json
{
  "http.proxy": "http://127.0.0.1:7890",
  "remote.SSH.httpProxy": {
    "server111": "http://127.0.0.1:10801"
  },
  "remote.SSH.httpsProxy": {
    "server111": "http://127.0.0.1:10801"
  }
}
```

两个 remote.SSH 键分别用于 HTTP/HTTPS，不是本地与远程两个方向；它们为远程 Server 安装及启动导出环境。对象键应匹配实际连接别名。仅在用户确需所有 SSH 主机且各机已有10801通道时，改为单个字符串 "http://127.0.0.1:10801"，不能只填端口。

远程扩展错误复用本地代理时，在已连接的 Remote Settings 合并：

```json
{
  "http.proxy": "http://127.0.0.1:10801",
  "http.useLocalProxyConfiguration": false
}
```

重连以使相关设置生效；保持专用隧道运行。若需停止或重启远程 VS Code Server，先说明会话影响。VS Code Ports 面板通常将远程端口映射到本地，不能代替这里的 SSH -R。不要使用 SSH ProxyCommand 代替远程应用 HTTP 代理，两者控制的是不同连接。

## Codex CLI：独立检查安装与认证

先读取官方页面和 codex login --help，避免固定过时参数。核实用户目标系统架构与发行版，Linux 官方独立安装示例：

```bash
curl -fsSL https://chatgpt.com/codex/install.sh | sh
```

按安装器提示处理 PATH 或重开终端后：

```bash
codex --version
codex login --device-auth
codex login status
```

用户本人打开生成链接并输入一次性码；是否可用取决于账户安全设置或工作区权限。随后从项目目录启动 codex 并验证实际请求。不要将授权码或 auth.json 写进 skill、Git、教程或排错日志。

Codex 不通过 pip 安装。python、pip、py 命令不存在仅说明相应命令不可用；Python3 可能另有安装。只有用户另需 Python 时，再依据发行版选择包管理器，不要改系统 Python 链接。

## 恢复

先展示目标区块再编辑：删除 ~/.bashrc 中本方案的 BEGIN/END 标记区块；检查是否还存在以前教程的 source 行或 export 后逐条处理。用备份恢复文件时先比较差异，避免覆盖此后新增内容。代理文件若为本方案新建且无其他使用者，可删除；否则恢复备份。

当前远程 Shell 临时停用：

```bash
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY no_proxy NO_PROXY
```

这不会删除持久配置，下次 Shell 仍可能加载。结束自己维持的隧道窗口用 Ctrl+C；保留普通 SSH 会话。只撤销本次增加的 VS Code 键或主机映射，不清空其他设置。
