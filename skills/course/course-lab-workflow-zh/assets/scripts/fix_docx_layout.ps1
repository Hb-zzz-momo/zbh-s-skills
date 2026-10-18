# 报告版式修正：把现有 docx 的图片改成等比缩放、表格收进版心、行高按内容收尾，并重新导出 PDF
# 用法：pwsh -File fix_docx_layout.ps1 -Docx "报告.docx" [-ImageWidthCm 5] [-OutDocx "输出.docx"] [-ExportPdf]
param(
    [Parameter(Mandatory = $true)][string]$Docx,
    [double]$ImageWidthCm = 5,
    [double]$ContentWidthCm = 0,        # 0 表示用页面边距算出的版心宽度
    [int]$BodyTableIndex = 0,           # 0 表示自动选“最宽的表”作为正文框
    [string]$OutDocx = '',
    [switch]$ExportPdf
)

Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.IO.Compression.FileSystem

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$doc = $word.Documents.Open($Docx)

# 先从 docx 里取出内嵌图片的真实像素比例：只改宽度会被 Word 横向拉伸，
# 而内嵌图拿不到 LinkFormat.SourceFullName，必须按 word/media 顺序比对
$tmp = Join-Path $env:TEMP ("fix-layout-" + [Guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
$mediaRatios = @()
try {
    $zipCopy = Join-Path $tmp 'doc.zip'
    Copy-Item $Docx $zipCopy -Force
    $zip = [IO.Compression.ZipFile]::OpenRead($zipCopy)
    foreach ($m in ($zip.Entries | Where-Object { $_.FullName -match '^word/media/.*\.(png|jpg|jpeg)$' } | Sort-Object FullName)) {
        $stream = $m.Open()
        $img = [Drawing.Image]::FromStream($stream)
        $mediaRatios += ($img.Height / $img.Width)
        $img.Dispose(); $stream.Close()
    }
    $zip.Dispose()
} catch { }

if ($ContentWidthCm -le 0) {
    $ContentWidthCm = ($doc.PageSetup.PageWidth - $doc.PageSetup.LeftMargin - $doc.PageSetup.RightMargin) / 28.3465
}
$widthPt = $ContentWidthCm * 28.3465

# 1) 图片：按原图像素比例同时算宽高，避免只改宽度被 Word 拉变形
$fixed = 0
for ($k = 1; $k -le $doc.InlineShapes.Count; $k++) {
    $s = $doc.InlineShapes.Item($k)
    $ratio = $null
    if ($mediaRatios.Count -eq $doc.InlineShapes.Count) { $ratio = $mediaRatios[$k - 1] }
    if ($null -eq $ratio) {
        try {
            $src = $s.LinkFormat.SourceFullName
            if ($src -and (Test-Path $src)) {
                $img = [Drawing.Image]::FromFile($src)
                $ratio = $img.Height / $img.Width
                $img.Dispose()
            }
        } catch { }
    }
    if ($null -eq $ratio) { $ratio = $s.Height / $s.Width }
    $s.Width = $ImageWidthCm * 28.3465
    $s.Height = $s.Width * $ratio
    $s.Range.ParagraphFormat.Alignment = 1
    $fixed++
}

# 2) 正文框：关自动调整 → 宽度收到版心 → 行高按内容收尾 → 允许跨页断行
$body = $null
if ($BodyTableIndex -gt 0) {
    $body = $doc.Tables.Item($BodyTableIndex)
} else {
    $maxW = 0
    for ($k = 1; $k -le $doc.Tables.Count; $k++) {
        $w = $doc.Tables.Item($k).Rows.Item(1).Cells.Item(1).Width
        if ($w -gt $maxW) { $maxW = $w; $body = $doc.Tables.Item($k) }
    }
}
if ($body) {
    $body.AllowAutoFit = $false
    $body.AutoFitBehavior(0)
    $body.PreferredWidthType = 3
    $body.PreferredWidth = $widthPt
    $body.Rows.LeftIndent = 0
    for ($r = 1; $r -le $body.Rows.Count; $r++) {
        $row = $body.Rows.Item($r)
        $row.AllowBreakAcrossPages = $true
        $row.HeightRule = 0                      # wdRowHeightAuto：避免整页只有边框的空页
        $cells = $row.Cells
        $old = @(); $total = 0
        for ($c = 1; $c -le $cells.Count; $c++) { $old += $cells.Item($c).Width; $total += $cells.Item($c).Width }
        for ($c = 1; $c -le $cells.Count; $c++) {
            $cells.Item($c).Width = [math]::Round($widthPt * $old[$c - 1] / $total, 1)
        }
    }
}

if ($OutDocx) {
    $doc.SaveAs2($OutDocx, 16)
} else {
    $doc.Save()
    $OutDocx = $Docx
}

if ($ExportPdf) {
    $pdf = [IO.Path]::ChangeExtension($OutDocx, '.pdf')
    if (Test-Path $pdf) { Remove-Item $pdf -Force }
    $doc.ExportAsFixedFormat($pdf, 17)
}

"修图 {0} 张（宽 {1}cm 等比）；正文框宽 {2:N2}cm；输出 {3}" -f $fixed, $ImageWidthCm, $ContentWidthCm, $OutDocx
$doc.Close(0)
$word.Quit()
