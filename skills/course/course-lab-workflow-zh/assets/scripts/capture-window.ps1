# 证据截图：按窗口标题定位真实窗口并整窗截图（Chrome 页面 / 记事本日志）
# 截图成品不得包含 Computer Use 发光指针/控制浮层或鼠标指针：截图前隐藏指示层或把指针移出截图区域，
# 截图后逐张放大检查；发现即重截，不得涂改遮盖。SetCursorPos 只移开系统鼠标，不会隐藏 Computer Use 的发光叠加层。
# -ClickPlay：先在页面空白处点一下，再 Tab 两次到第一个音频控件并按空格播放，
#             随后校验访问日志新增了音频请求，只有日志出现记录才算“播放成功”
# 用法：
#   pwsh -File capture-window.ps1 -Exe chrome -Url http://localhost:8080/experiment1/music.html `
#        -Title "歌曲列表" -Out "evidence/shot-music.png" -ClickPlay -LogFile "...\localhost_access_log.txt" -LogPattern "audio/"
param(
    [Parameter(Mandatory = $true)][string]$Out,
    [Parameter(Mandatory = $true)][string]$Title,
    [string]$Exe = 'chrome',
    [string]$Url = '',
    [string]$File = '',
    [string]$ProfileDir = '',
    [int]$Width = 1320,
    [int]$Height = 880,
    [int]$WaitSeconds = 7,
    [switch]$ClickPlay,
    [string]$LogFile = '',
    [string]$LogPattern = 'audio/'
)

Add-Type -AssemblyName System.Drawing

if (-not ('WinShot' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;

public class WinShot {
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumWindowsProc cb, IntPtr lParam);
    [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
    [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr h, IntPtr after, int x, int y, int cx, int cy, uint flags);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
    [DllImport("user32.dll")] public static extern void mouse_event(uint f, uint dx, uint dy, uint d, IntPtr e);
    [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr h, uint msg, IntPtr w, IntPtr l);
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
    public static List<IntPtr> Windows() {
        List<IntPtr> l = new List<IntPtr>();
        EnumWindows(delegate(IntPtr h, IntPtr p) { if (IsWindowVisible(h)) { l.Add(h); } return true; }, IntPtr.Zero);
        return l;
    }
    public static string Title(IntPtr h) { StringBuilder sb = new StringBuilder(512); GetWindowText(h, sb, sb.Capacity); return sb.ToString(); }
}
'@
}

# 启动目标程序
switch -Wildcard ($Exe) {
    '*chrome*' {
        $chrome = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
        if (-not $ProfileDir) { $ProfileDir = Join-Path $env:TEMP 'codex-capture-profile' }
        Start-Process $chrome -ArgumentList "--user-data-dir=$ProfileDir", '--new-window', "--window-size=$Width,$Height", '--window-position=40,20', $Url | Out-Null
    }
    '*notepad*' { Start-Process notepad.exe -ArgumentList $File | Out-Null }
    default { Start-Process $Exe -ArgumentList $File | Out-Null }
}

Start-Sleep -Seconds $WaitSeconds

$handle = [IntPtr]::Zero
$deadline = (Get-Date).AddSeconds(25)
while ($handle -eq [IntPtr]::Zero -and (Get-Date) -lt $deadline) {
    foreach ($h in [WinShot]::Windows()) {
        if ([WinShot]::Title($h) -like "*$Title*") { $handle = $h; break }
    }
    if ($handle -eq [IntPtr]::Zero) { Start-Sleep -Milliseconds 700 }
}
if ($handle -eq [IntPtr]::Zero) { "未找到标题包含 $Title 的窗口"; exit 1 }

[WinShot]::SetWindowPos($handle, [IntPtr](-1), 40, 20, ($Width + 40), ($Height + 120), 0x40) | Out-Null
Start-Sleep -Milliseconds 800
[WinShot]::SetForegroundWindow($handle) | Out-Null
Start-Sleep -Milliseconds 600

if ($ClickPlay) {
    $before = 0
    if ($LogFile -and (Test-Path $LogFile)) { $before = (Select-String -Path $LogFile -Pattern $LogPattern -ErrorAction SilentlyContinue).Count }
    [WinShot]::SetCursorPos(720, 930) | Out-Null
    Start-Sleep -Milliseconds 300
    [WinShot]::mouse_event(0x0002, 0, 0, 0, [IntPtr]::Zero)
    [WinShot]::mouse_event(0x0004, 0, 0, 0, [IntPtr]::Zero)
    Start-Sleep -Milliseconds 600
    $shell = New-Object -ComObject WScript.Shell
    $shell.SendKeys('{TAB}'); Start-Sleep -Milliseconds 400
    $shell.SendKeys('{TAB}'); Start-Sleep -Milliseconds 400
    $shell.SendKeys(' '); Start-Sleep -Seconds 12
    if ($LogFile -and (Test-Path $LogFile)) {
        $after = (Select-String -Path $LogFile -Pattern $LogPattern -ErrorAction SilentlyContinue).Count
        "播放前后服务端日志条数：$before → $after" + $(if ($after -gt $before) { '（日志已新增请求，可作为播放证据）' } else { '（日志未新增，尚不能认定播放成功）' })
    }
}

$rect = New-Object WinShot+RECT
[WinShot]::GetWindowRect($handle, [ref]$rect) | Out-Null
$w = $rect.Right - $rect.Left
$h2 = $rect.Bottom - $rect.Top
$bmp = New-Object Drawing.Bitmap $w, $h2
$g = [Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($rect.Left, $rect.Top, 0, 0, $bmp.Size)
$g.Dispose()
$bmp.Save($Out, [Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()
[WinShot]::SetWindowPos($handle, [IntPtr](-2), 40, 20, ($Width + 40), ($Height + 120), 0x40) | Out-Null
[WinShot]::PostMessage($handle, 0x0010, [IntPtr]::Zero, [IntPtr]::Zero) | Out-Null
"$Out -> ${w}x${h2} | $([WinShot]::Title($handle))"
