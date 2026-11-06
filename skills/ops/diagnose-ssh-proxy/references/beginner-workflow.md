# SSH与远程代理：五步小白工作流

公开示例地址203.0.113.88不能直接连接。先确认自己的服务器地址、SSH端口、实际账户；下文ACTUAL_USER与地址必须替换。本地代理示例7890、远端10801，实际软件端口不同就同时替换配置与测试。历史案例不证明当前机器正常。

## 日常路线

本机代理开启 → Windows保持唯一一个ssh -NT server111-proxy → 普通SSH/VS Code连接server111 → 从项目启动应用。

小白理解：普通连接负责进办公室；专用隧道负责把办公室的10801收件窗口接到家里代理7890。进办公室和寄快递是两件事；同一服务器不用为每个开发窗口重开收件窗口。

## 第1步：先只验证能登录正确账户

位置：Windows PowerShell。新机器尚无别名时直接登录：

~~~powershell
ssh -o ClearAllForwardings=yes -p 22 ACTUAL_USER@203.0.113.88
~~~

实际账户/端口替换后执行，首次指纹与可信控制台核对。已配置server111时可直接ssh -o ClearAllForwardings=yes server111。远端执行whoami确认账户。超时先查网络/端口；Permission denied查账户/认证，不先改代理。

**成功信号：** whoami是预期账户；保留此会话供后续配置。不能关主机校验、随意开启root密码登录或连续试密码。

小白理解：先确认办公室地址和门禁有效，再建设专线。

<details>
<summary>小白解析：账户、指纹和ClearAllForwardings各是什么</summary>
<p>地址像办公楼位置；User是进门身份，同一机器的root与ubuntu是不同身份。主机指纹用于确认不是走错楼；它不是账户密码。ClearAllForwardings=yes只让本次连接不申请端口转发，便于区分“没进门”和“进门后开窗口失败”，不会取消其他已运行隧道。</p>
<table>
<thead>
<tr>
<th>命令片段</th>
<th>意思</th>
<th>能否改变</th>
</tr>
</thead>
<tbody>
<tr>
<td>-o ClearAllForwardings=yes</td>
<td>此次不带转发</td>
<td>登录隔离测试保留</td>
</tr>
<tr>
<td>-p 22</td>
<td>SSH端口</td>
<td>换成实际值，不是代理端口</td>
</tr>
<tr>
<td>ACTUAL_USER@地址</td>
<td>登录哪个账户、哪台机器</td>
<td>两者都换成真实参数</td>
</tr>
<tr>
<td>whoami</td>
<td>显示远端当前账户</td>
<td>用结果核对，而非猜root</td>
</tr>
</tbody>
</table>
</details>

## 第2步：[可选] 建立密钥登录

位置：Windows文件管理器打开自己的.ssh目录。已有有效私钥就复用，不覆盖。确需新建且目标不存在时：

~~~powershell
ssh-keygen -t ed25519 -f "$env:USERPROFILE\.ssh\id_ed25519_111"
~~~

口令由用户输入。在Windows文件管理器中右键打开新生成的id_ed25519_111.pub，用文本编辑器复制完整一行；不要复制无.pub的私钥。用第1步密码连接进入VS Code远程窗口，在实际账户家目录打开.ssh/authorized_keys；没有.ssh目录或文件就从远程文件树新建。保留已有内容，仅将尚未存在的完整公钥另起一行粘贴并保存。

在**远端终端、该登录账户下**设置权限（文件已创建后执行）：

~~~bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
~~~

小白理解：700让只有本人能进入/读取/修改钥匙目录，600让只有本人能读写公钥登记文件；最后两个0表示不给其他组/用户权限，不是端口或密码。文件应属于实际登录账户，只改这两个对象，不对整个家目录递归改权限。启用新密钥时，第3步两个Host各加IdentityFile与IdentitiesOnly；保留密码方式则跳过本步直接做第3步。

**成功信号：** 第3步保存后，用普通别名登录返回正确whoami。私钥口令提示不等于服务器密码失败。

小白理解：公钥像放在办公室门上的锁，私钥是电脑里的钥匙；钥匙不交给服务器。

<details>
<summary>小白解析：.pub与私钥为什么不能用反</summary>
<p>.pub只含公钥，可以安装到自己的服务器；无.pub文件是私钥，客户端IdentityFile选它。-t ed25519选密钥算法，-f后是保存位置；命令不会代你确认已有文件，先查再生成。ssh-agent可以管理已经解锁的钥匙，但本步不要求配置它。只有私钥权限日志明确报错才修那个私钥，不改整个.ssh目录。BatchMode失败也可能是带口令钥匙未解锁，不能单凭它断言公钥没装好。</p>
</details>

## 第3步：保存两个SSH入口，再开唯一代理隧道

位置：Windows用编辑器打开 ~/.ssh/config，备份后合并，保留其他主机；这一步密码和密钥路线都要做。VS Code可以在本机命令面板选择Remote-SSH: Open SSH Configuration File。不要编辑远端的同名文件。

~~~sshconfig
Host server111
    HostName 203.0.113.88
    User ACTUAL_USER
    Port 22
    ServerAliveInterval 30
    ServerAliveCountMax 3

Host server111-proxy
    HostName 203.0.113.88
    User ACTUAL_USER
    Port 22
    RemoteForward 127.0.0.1:10801 127.0.0.1:7890
    ServerAliveInterval 30
    ServerAliveCountMax 3
    ExitOnForwardFailure yes
~~~

仅启用第2步密钥时，在两个Host里各合并IdentityFile ~/.ssh/id_ed25519_111与IdentitiesOnly yes。前者指定无.pub的私钥文件，后者只尝试明确配置的身份，避免拿其他钥匙试门；密码路线不加。保存后先ssh server111验证登录；本机代理开启并确认实际HTTP/mixed端口，再运行：

~~~powershell
ssh -NT server111-proxy
~~~

已有健康隧道就复用，不重复开。窗口无输出通常正常，仍须从另一个普通远端会话测试：

~~~bash
curl -q -sS --noproxy '' --proxy http://127.0.0.1:10801 --connect-timeout 5 --max-time 20 -w '\nHTTP=%{http_code}\n' https://api.ipify.org
echo "curl_exit=$?"
~~~

**成功信号：** 外网IP、HTTP200、curl_exit=0。只证明本次请求；出现remote port forwarding failed先查10801归属及转发策略，不杀sshd。远端10801无需开放公网。

小白理解：保存通讯录不会自动拨号；ssh -NT才建立办公室到家的专线。

<details>
<summary>小白解析：配置字段、两个回环地址与命令参数</summary>
<table>
<thead>
<tr>
<th>片段</th>
<th>白话意思</th>
<th>本步边界</th>
</tr>
</thead>
<tbody>
<tr>
<td>Host / HostName / User</td>
<td>通讯录名字 / 实际地址 / 门禁身份</td>
<td>两别名指同一机器与账户</td>
</tr>
<tr>
<td>RemoteForward 远端 本机</td>
<td>办公室开入口，把请求送回家</td>
<td>第一个127.0.0.1属于服务器，第二个属于Windows</td>
</tr>
<tr>
<td>ServerAliveInterval / CountMax</td>
<td>隔多久探测、容忍几次无回应</td>
<td>发现掉线，不自动重连</td>
</tr>
<tr>
<td>ExitOnForwardFailure yes</td>
<td>本次专线开不了就报错退出</td>
<td>不检查本机代理最终健康</td>
</tr>
<tr>
<td>ssh -N / -T</td>
<td>不跑远端命令 / 不分配终端</td>
<td>只维持隧道</td>
</tr>
<tr>
<td>curl -q / -sS</td>
<td>不读curl配置 / 安静但显示错误</td>
<td>便于隔离实际路径</td>
</tr>
<tr>
<td>--noproxy '' / --proxy</td>
<td>测试不绕代理 / 指明远端10801</td>
<td>这里空字符串是Bash写法</td>
</tr>
<tr>
<td>--connect-timeout / --max-time</td>
<td>连接/总请求超时秒数</td>
<td>避免无限等待</td>
</tr>
<tr>
<td>-w / echo $?</td>
<td>显示HTTP状态 / 上条退出码</td>
<td>必须紧接被测命令核对</td>
</tr>
</tbody>
</table>
<p>LISTEN或SSH进程存在不等于代理业务正常。多个程序可以共用一条健康隧道；同一服务器、同一地址的10801不能重复申请。VS Code Ports普通转发方向不同，不能代替-R。</p>
</details>

## 第4步：用文件保存远端代理设置

位置：VS Code连接普通server111，文件树/打开文件定位远端账户的 ~/.config/proxy/ssh-local.sh；目录没有就先创建。编辑器新建文件夹/文件即可，无需复制长串写文件脚本。备份已存在文件，粘贴：

~~~bash
export http_proxy="http://127.0.0.1:10801"
export https_proxy="$http_proxy"
export HTTP_PROXY="$http_proxy"
export HTTPS_PROXY="$http_proxy"
export all_proxy="$http_proxy"
export ALL_PROXY="$http_proxy"
export no_proxy="localhost,127.0.0.1,::1"
export NO_PROXY="$no_proxy"
~~~

打开远端 ~/.bashrc，合并一条加载语句，清理冲突旧赋值但不覆盖其他配置：

~~~bash
[ -f "$HOME/.config/proxy/ssh-local.sh" ] && . "$HOME/.config/proxy/ssh-local.sh"
~~~

交互Bash需能执行到该行；如果还要覆盖SSH单条非交互命令，放在其提前return之前。保存后开新终端，省略--proxy重测第3步请求。bashrc不配置所有服务/用户/容器；后台进程需核对自己的启动链并重新启动。

**成功信号：** 新终端https_proxy为10801，环境代理请求HTTP200/退出0。不要把永久配置简化成每次临时export。

小白理解：专线建好后，把寄件地址写在配置文件里；已经出发的旧员工不会自动换通知。

<details>
<summary>小白解析：为何大小写都设置，https_proxy为何写http</summary>
<p>不同程序读取的变量不同，统一HTTP(S)/ALL_PROXY可避免残留地址。http://描述代理本身的协议，HTTPS业务可经CONNECT传输，不意味着业务变成明文。NO_PROXY让本机通信不绕路；它不应排除正在验证的外部站点。source或点号加载只影响当前Shell和其后代，不能追溯修改后台。变量只是通知，不会创建监听或隧道；窗口关掉后，保存的地址也不能自行重建专线。</p>
</details>

## 第5步：让目标应用使用通道并单独验收

位置：先明确应用运行在Windows、远端终端还是远端后台。VS Code本地http.proxy填本机7890；remote.SSH.httpProxy/httpsProxy按server111映射远端10801。若远端扩展错误复用本机代理，再在Remote Settings设远端http.proxy和http.useLocalProxyConfiguration=false。合并字段并按实际应用需要重连，不能整份覆盖设置。

Codex已有正常版本就跳过安装；首次安装按[当前官方CLI文档](https://learn.chatgpt.com/docs/cli)。远端检查：

~~~bash
codex --version
codex login status
~~~

确实未登录时，核对codex login --help后选受支持设备授权，由用户本人完成浏览器授权。不要记录设备码或auth.json。最后从项目目录启动应用并完成真实请求；Codex不通过pip安装。CLI版本不等于常驻后台版本，后台启动环境需另外核对。

**成功信号：** 目标应用实际回复/任务完成。普通站点200、模型菜单可见或已登录都不能替代；失败按实际日志区分连接、认证、权限等。

小白理解：普通信件寄到，不代表登录、模型等每项业务都获准；最后要真的办成目标业务。

<details>
<summary>小白解析：本机设置、远端设置和后台为什么分开</summary>
<p>每个程序看到的127.0.0.1都是自己；远端填写电脑7890通常会找错窗口。环境沿启动关系传递，终端export不会改变已运行后台。按具体进程的启动配置和日志确认，而不是看到curl成功就认定全部应用成功。403是收到拒绝回执，不是“完全连不上”；原因以正文为准，不用重装Python或反复更新模型来替代排障。</p>
</details>

## 恢复与迁移

保留备份并先比较后续修改；只撤销自己添加的Host/加载块和代理文件，不清空整个配置。临时停止当前Shell代理可unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY no_proxy NO_PROXY；这不撤销持久文件。结束自己维持的隧道用Ctrl+C，保留普通SSH。

小白理解：恢复像撤销本次改的通讯录和通知，不是拆掉办公室全部门禁。换机器时重新核对账户、SSH端口、本机代理端口、远端监听与Shell，不照抄示例身份。上述为可复用教程，不代表示例服务器已配置成功。
