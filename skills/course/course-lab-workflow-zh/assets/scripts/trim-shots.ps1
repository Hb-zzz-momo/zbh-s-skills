# 裁掉截图右下角的空白（保留窗口标题栏与左侧内容），输出 *-trim.png，原图不动
# 用法：pwsh -File trim-shots.ps1 -EvidenceDir "evidence" [-Pad 26]
param(
    [Parameter(Mandatory = $true)][string]$EvidenceDir,
    [string]$Pattern = 'shot-*.png',
    [int]$Pad = 26
)

Add-Type -AssemblyName System.Drawing

Get-ChildItem (Join-Path $EvidenceDir $Pattern) | Where-Object { $_.Name -notlike '*-trim.png' } | ForEach-Object {
    $src = [Drawing.Bitmap]::FromFile($_.FullName)
    # 只在窗口内部找内容（跳过外框 12px 与标题栏 64px，以及底部 44px 的滚动条/状态栏）
    $x0 = 12; $y0 = 64
    $x1 = $src.Width - 30; $y1 = $src.Height - 44
    $maxX = $x0; $maxY = $y0
    for ($y = $y0; $y -lt $y1; $y += 2) {
        for ($x = $x0; $x -lt $x1; $x += 2) {
            $c = $src.GetPixel($x, $y)
            if (($c.R + $c.G + $c.B) -lt 690) {
                if ($x -gt $maxX) { $maxX = $x }
                if ($y -gt $maxY) { $maxY = $y }
            }
        }
    }
    $w = [Math]::Min($src.Width, $maxX + $Pad)
    $h = [Math]::Min($src.Height, $maxY + $Pad)
    if ($w -lt 200) { $w = $src.Width }
    if ($h -lt 200) { $h = $src.Height }

    $dst = New-Object Drawing.Bitmap $w, $h
    $g = [Drawing.Graphics]::FromImage($dst)
    $rect = New-Object Drawing.Rectangle 0, 0, $w, $h
    $g.DrawImage($src, $rect, $rect, [Drawing.GraphicsUnit]::Pixel)
    $g.Dispose()
    $out = Join-Path $EvidenceDir ($_.BaseName + '-trim.png')
    $dst.Save($out, [Drawing.Imaging.ImageFormat]::Png)
    $dst.Dispose(); $src.Dispose()
    "{0} -> {1}  ({2}x{3})" -f $_.Name, [IO.Path]::GetFileName($out), $w, $h
}
