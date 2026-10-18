# 小白工作流：先开门，再搭通道，最后让应用走通道

> 公开版本：服务器与出口IP已替换为文档示例地址（203.0.113.0/24），不能原样用于连接；执行前替换为实际值。

目录：场景与比喻；五个关卡；冲突对照；日常使用；撤销；Skill 用法。

## 先看懂三件事

把服务器想成外地办公室，把你的电脑想成家里，把家里代理想成能寄国际快递的窗口。

| 真实对象 | 小白比喻 | 职责 |
| --- | --- | --- |
| SSH 登录账户与密码 / 密钥 | 办公室门禁 | 决定能不能进入服务器 |
| SSH 反向隧道 | 办公室到家里的专线 | 把远程10801收到的连接送回电脑7890 |
| http_proxy / https_proxy | 写给应用的寄件地址 | 告诉应用去哪个窗口，不负责建设专线 |

**127.0.0.1 的意思是“我自己”。** 服务器上的127.0.0.1是服务器；电脑上的127.0.0.1是电脑。同一个数字不代表同一台机器。

本教程使用 server111 = 203.0.113.88、本地7890、远程10801。实际登录账户尚未确认；下面配置中的 ACTUAL_USER 必须替换。root 和 ubuntu 是不同账户，同一台服务器上不能混用它们的密码与 authorized_keys。SSH22也须核对。

第一台服务器曾得到 HTTP=200、curl_exit=0，这是成功案例。整理时 server111 的登录失败尚未定位；实际使用时以新日志判断从哪一关开始。若已有 Authenticated to 等认证通过证据，就直接检查后续转发或会话，不要重新猜密码。

## 第一关：只检查能不能进服务器

**在哪里：你的电脑，Windows PowerShell。**

```powershell
ssh -G server111 | Select-String '^(hostname|user|port|identityfile) '
ssh -vv -o ClearAllForwardings=yes server111
```

第一条像检查“寄件单”：确认 hostname 为203.0.113.88、user为真实账户、port为真实SSH端口。第二条表示“这次先只开门，暂时不搭通道”。

如果已有可用的服务器终端，在那里执行 whoami 确认登录名。若完全不能登录，从云控制台核实账户。密码输入时不显示星号很正常。

**成功信号：** 出现远程命令提示符，在里面执行 whoami 得到预期账户。日志中的 Authenticated to 证明认证阶段通过；之后仍可能遇到会话或转发问题。

**失败就停在这里：** Permission denied 查账户与认证；timeout/refused 查地址、端口、网络和SSH服务；Enter passphrase for key 问的是私钥口令。不要先改代理，也不要连续反复输入密码。

**举例：** 门禁卡属于 ubuntu，却尝试进 root 的门，卡本身正确也无法开门。当前问题必须用日志确认，不能直接认定就是这个原因。

## 第二关：按需要配置密钥登录（可选）

已经能用密码正常登录时，可以保留密码方式并直接进入第三关。免密用于减少日常输入，不是建立代理隧道的前提。

**比喻：** 公钥是放在办公室门上的锁，私钥是留在电脑里的钥匙。`.pub` 是公钥，客户端的 IdentityFile 要选无 `.pub` 的私钥。

**在哪里：电脑 PowerShell。** 文件不存在才生成，避免覆盖旧钥匙：

```powershell
New-Item -ItemType Directory -Path "$env:USERPROFILE\.ssh" -Force | Out-Null
$keyPath = "$env:USERPROFILE\.ssh\id_ed25519_111"
if (-not (Test-Path -LiteralPath $keyPath)) {
    ssh-keygen -t ed25519 -f $keyPath -C 'server111'
}
Get-Content -LiteralPath "${keyPath}.pub"
```

若公钥文件不存在而私钥已存在，先停止，不要覆盖；由助手协助导出公钥。保留第一关的可用会话。

**在哪里：服务器终端，真实登录账户下。** 将最后一行占位文本替换成完整公钥再执行：

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
touch ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
printf '\n%s\n' '替换为完整的 ssh-ed25519 公钥一行' >> ~/.ssh/authorized_keys
```

**在哪里：电脑的 `$env:USERPROFILE\.ssh\config` 文件。** 编辑前保存备份；保留其他主机。合并为下面两个别名，替换 ACTUAL_USER 和实际SSH端口。不要保留同一目标旧的重复 RemoteForward。

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

**成功信号：** 在电脑执行下面命令，得到真实用户名：

```powershell
ssh -o ClearAllForwardings=yes server111 'whoami'
```

私钥如果加了口令，可能仍询问这个口令；它和服务器密码是两回事。加密钥匙由 ssh-agent 解锁管理后才可能完全不提示。若报 bad permissions，参照操作参考只修复真实私钥，不要改整个文件夹。

## 第三关：把服务器10801接回电脑7890

**比喻：** 在办公室放一个10801号收件箱，专线把箱里的请求送到家里的7890号快递窗口。

**在哪里：电脑。** 先打开代理软件，确认7890是 HTTP 或 mixed 端口。在 PowerShell 单独开一个窗口执行：

```powershell
ssh -NT server111-proxy
```

窗口没有输出且一直停在那里通常正常，先保持开启。电脑代理软件也要一直运行。`-N` 表示不执行远程命令，`-T` 表示不申请终端。

**在哪里：另一个普通服务器终端。** 可以通过 `ssh server111` 进入，再执行：

```bash
ss -lntp 'sport = :10801'
command curl -q -v -S --noproxy '' --proxy http://127.0.0.1:10801 --connect-timeout 5 --max-time 20 --write-out '\nHTTP=%{http_code}\n' https://api.ipify.org
echo "curl_exit=$?"
```

**成功信号：** 看到一个外网IP、HTTP=200、curl_exit=0。IP不必每次相同，不要求和过去的203.0.113.211一致。该结果只证明这次请求成功。

**失败分支：** remote port forwarding failed 查是否已有隧道占用10801或服务端限制；先确认占用者，不要杀全部sshd。LISTEN存在但curl失败时，检查本地7890和隧道窗口。两台服务器分别用10801不冲突；同一服务器重复绑定才可能冲突。

## 第四关：把代理地址写进配置，省掉重复 export

**比喻：** 专线已经建好，把收件箱地址贴在办公室墙上，让之后进来的应用看得到。

**在哪里：服务器 Bash 终端。** 先检查是否已有旧的代理 export/source。已有设置应合并，避免不同值互相覆盖。下面方案在新文件中集中保存，并给 bashrc 加一个有标记的加载区块：

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

**每行什么意思：** http_proxy给HTTP应用指定代理；https_proxy给HTTPS请求指定代理；大写变量兼容其他程序；`$http_proxy`表示复用上面值；no_proxy让本机访问绕过代理。`http://`表示代理本身使用HTTP，访问HTTPS时可以用CONNECT隧道，所以这样写没问题。

**成功信号：** 新开一个普通SSH终端，在服务器执行：

```bash
printf 'https_proxy=%s\n' "$https_proxy"
curl -q -sS --connect-timeout 5 --max-time 20 --write-out '\nHTTP=%{http_code}\n' https://api.ipify.org
echo "curl_exit=$?"
```

应显示10801代理地址，且请求HTTP200、退出码0。还需确认no_proxy没有排除ipify，否则可能绕过代理。旧进程要重启才获得新环境。bashrc只影响相应Bash加载链，并不会自动配置系统服务、其他账户或容器；电脑断网或隧道关闭时，写好的地址不会自己重建专线。

## 第五关：让 VS Code 和 Codex 使用已验证的通道

**在哪里：电脑 VS Code。** 日常连接 server111；专用的 server111-proxy 留给隧道。F1打开 User Settings (JSON)，合并下列键，不要覆盖其他设置：

```json
{
  "http.proxy": "http://127.0.0.1:7890",
  "remote.SSH.httpProxy": {"server111": "http://127.0.0.1:10801"},
  "remote.SSH.httpsProxy": {"server111": "http://127.0.0.1:10801"}
}
```

http.proxy是电脑侧地址；两个remote.SSH设置为远程Server安装和启动配置HTTP/HTTPS代理，不是“本地一个、远程一个”。只写端口号不足以表达代理协议与地址。

若远程扩展复用了错误的本地代理，连接后打开 Remote Settings (JSON)，合并：

```json
{
  "http.proxy": "http://127.0.0.1:10801",
  "http.useLocalProxyConfiguration": false
}
```

重连并检查目标扩展日志。不是所有扩展都读取同一设置；以实际请求为准。

**在哪里：服务器。** 核对当前官方安装文档后，Linux可使用：

```bash
curl -fsSL https://chatgpt.com/codex/install.sh | sh
```

按安装提示处理PATH或重开终端，然后：

```bash
codex --version
codex login --device-auth
codex login status
```

在电脑浏览器由你本人打开生成链接、输入设备码；账号或工作区可能需要开启设备码登录。不要发送设备码或认证文件。最后从项目目录运行codex，验证实际请求。Codex不通过pip安装，所以不需要先解决python命令缺失才能使用上述独立安装器。

**成功信号：** 版本号可显示、登录状态正确、目标应用请求成功。curl成功只是第三关成功，不能替代第五关验收。

## 最容易混淆的冲突

| 说法 / 现象 | 原理与正确动作 |
| --- | --- |
| 密码对了却进不去 | 先核对账户与日志；认证通过后还可能因转发失败退出 |
| 两个Host一定启动两个SSH | Host是配置匹配，不是进程启动器；用ssh -G看实际配置 |
| 重复export会抢端口 | export只改变量；后赋值可能覆盖前值，不会占监听端口 |
| 电脑和服务器都写127.0.0.1 | 两端各自指自己，靠SSH隧道连接两边 |
| VS Code Ports里有10801就够了 | Ports普通转发与这里的反向隧道方向不同 |
| 每次登录都要export | 可放入配置文件；要确认新Shell确实加载，隧道仍须在线 |
| 全局配置只写10801 | 应写完整http://127.0.0.1:10801；全局的作用范围取决于配置位置 |

## 日常只记三件事

电脑代理软件开启7890；电脑维持一个 `ssh -NT server111-proxy` 窗口；VS Code或普通SSH连接server111。电脑重启后，持久环境配置还在，隧道需要重新开启。

临时取消当前服务器终端代理可执行 `unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY no_proxy NO_PROXY`。永久撤销时删除bashrc本方案BEGIN/END区块，并检查旧的source/export；仅撤销这次增加的设置，必要时比较备份恢复。不要清空整个配置文件。

## 下次如何调用这个 Skill

技能安装可用后，可以说：“使用 $diagnose-ssh-proxy，排查server111正确密码无法登录；先看实际账户与日志，不带转发测试，再逐层检查。”

文件上传成功不等于技能已注册。只有Skills同步或安装完成后，才可以把上面的名字作为已安装技能调用；本次安装状态以交付说明为准。未安装时，也可以将技能文件交给助手作为参考材料使用。
