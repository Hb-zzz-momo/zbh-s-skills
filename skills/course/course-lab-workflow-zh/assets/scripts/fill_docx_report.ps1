# 用课程母版生成实验报告的骨架脚本（含本次踩过的坑，按需改写占位内容即可）
# 用法：pwsh -File fill_docx_report.ps1 -Template "实验报告1.doc" -BodyFile "body.txt" `
#        -ImageDir "evidence" -OutDocx "报告.docx" -ExportPdf
#
# body.txt 约定：
#   - 普通行 = 一个正文段落
#   - [[IMG1]] = 在此处插入图片（图片名在 -ImageMap 里映射，或按 image-1.png 顺序匹配）
#   - [[TABLE1]] = 在此处插入 -TableFile 指定的表格（TSV：第一行表头）
#   - 行首 § 的段落 = 代码行，最后统一改成等宽字体并去掉 §
#
# 关键坑（已在脚本中处理）：
#   1) 图片只设 Width 会被 Word 横向拉伸 → 用原图像素比例同时算 Height
#   2) 封面“班 级：”等标签格很窄，值必须写进右侧空单元格，否则折行
#   3) 填写字段用 Find/Replace 按标签替换，不要按段落下标（插段落会导致下标漂移）
#   4) 正文框（模板自带的表格）常比版心还宽 → 关自动调整再按比例缩到版心
#   5) 行高按内容收尾，不要用“每行至少一页高”撑满，否则出现只有边框的空页
#   6) 保存前检查目标文件是否被 WPS/Word 占用（~$ 锁文件）
param(
    [Parameter(Mandatory = $true)][string]$Template,
    [Parameter(Mandatory = $true)][string]$BodyFile,
    [Parameter(Mandatory = $true)][string]$ImageDir,
    [Parameter(Mandatory = $true)][string]$OutDocx,
    [hashtable]$CoverCells = @{},          # 例：@{ '2,2'='24大数据2班'; '2,4'='赵奔昊'; '2,6'='24211870236'; '3,2'='5B322'; '3,4'='2026年9月18日' }
    [hashtable]$Labels = @{},              # 例：@{ '学    号：'='24211870236' }（按标签替换时用）
    [string[]]$Images = @(),               # 按 [[IMG1]] [[IMG2]] 顺序对应的图片文件名
    [string]$TableFile = '',
    [double]$ImageWidthCm = 5,
    [switch]$ExportPdf
)

Add-Type -AssemblyName System.Drawing

$lock = Join-Path (Split-Path $OutDocx -Parent) ('~$' + [IO.Path]::GetFileName($OutDocx))
if (Test-Path $OutDocx) {
    try { [IO.File]::OpenWrite($OutDocx).Close() }
    catch { throw "目标文件被占用（可能有 $lock），请先关闭 WPS/Word 再运行" }
}

function To-WordText($raw) { (($raw -replace "`r?`n", "`r").Trim("`r")) + "`r" }

$word = New-Object -ComObject Word.Application
$word.Visible = $false; $word.DisplayAlerts = 0
$doc = $word.Documents.Open($Template)

function Replace-Label($doc, $label, $value) {
    $range = $doc.Content
    $range.Find.ClearFormatting(); $range.Find.Replacement.ClearFormatting(); $range.Find.MatchWildcards = $false
    return $range.Find.Execute($label, $false, $false, $false, $false, $false, $true, 1, $false, "$label$value", 2)
}

function Insert-Image($doc, $marker, $path, $widthCm) {
    $range = $doc.Content
    $range.Find.ClearFormatting(); $range.Find.MatchWildcards = $false
    if (-not $range.Find.Execute($marker)) { return $false }
    $range.Text = ''
    $shape = $doc.InlineShapes.AddPicture($path, $false, $true, $range)
    $img = [Drawing.Image]::FromFile($path)          # 坑 1：按像素比例同时算高
    $shape.Width = $widthCm * 28.3465
    $shape.Height = $shape.Width * ($img.Height / $img.Width)
    $img.Dispose()
    $shape.Range.ParagraphFormat.Alignment = 1
    return $true
}

# 1) 正文：把 body.txt 插到“四、实验结果与分析”之后
$anchor = $null
for ($i = 1; $i -le $doc.Paragraphs.Count; $i++) {
    if ($doc.Paragraphs.Item($i).Range.Text -match '^四、实验结果与分析') { $anchor = $i; break }
}
if (-not $anchor) { throw '未找到“四、实验结果与分析”段落，请按模板调整锚点' }
$body = To-WordText (Get-Content $BodyFile -Raw -Encoding UTF8)
$doc.Paragraphs.Item($anchor).Range.InsertAfter($body)

# 2) 封面：值写进标签右侧的空单元格（坑 2）
if ($doc.Tables.Count -ge 1 -and $CoverCells.Count -gt 0) {
    $cover = $doc.Tables.Item(1)
    foreach ($k in $CoverCells.Keys) {
        $rc = $k.Split(',')
        $cover.Cell([int]$rc[0], [int]$rc[1]).Range.Text = [string]$CoverCells[$k]
    }
}
# 3) 其余字段：按标签替换（坑 3）
foreach ($k in $Labels.Keys) { Replace-Label $doc $k $Labels[$k] | Out-Null }

# 4) 图片与表格
for ($n = 1; $n -le $Images.Count; $n++) {
    Insert-Image $doc "[[IMG$n]]" (Join-Path $ImageDir $Images[$n - 1]) $ImageWidthCm | Out-Null
}
if ($TableFile -and (Test-Path $TableFile)) {
    $rows = Get-Content $TableFile -Encoding UTF8 | Where-Object { $_ -ne '' } | ForEach-Object { , ($_ -split "`t") }
    $range = $doc.Content
    $range.Find.ClearFormatting(); $range.Find.MatchWildcards = $false
    if ($range.Find.Execute('[[TABLE1]]')) {
        $range.Text = ''
        $table = $doc.Tables.Add($range, $rows.Count, $rows[0].Count)
        for ($r = 0; $r -lt $rows.Count; $r++) {
            for ($c = 0; $c -lt $rows[0].Count; $c++) { $table.Cell($r + 1, $c + 1).Range.Text = [string]$rows[$r][$c] }
        }
        $table.Borders.InsideLineStyle = 1; $table.Borders.OutsideLineStyle = 1
    }
}

# 5) 代码行：去掉 § 前缀并改成等宽字体；图题/表题居中
foreach ($p in $doc.Paragraphs) {
    $t = $p.Range.Text
    if ($t.StartsWith('§')) {
        $p.Range.Text = ($t -replace '^§', '')
        $p.Range.Font.Name = 'Consolas'; $p.Range.Font.Size = 9
    } elseif ($t -match '^图 \d' -or $t -match '^表 \d') {
        $p.Range.ParagraphFormat.Alignment = 1; $p.Range.Font.Size = 10.5
    }
}

# 6) 正文框收进版心（坑 4），行高按内容收尾（坑 5）
$widthPt = ($doc.PageSetup.PageWidth - $doc.PageSetup.LeftMargin - $doc.PageSetup.RightMargin)
$body_table = $null; $maxW = 0
for ($k = 1; $k -le $doc.Tables.Count; $k++) {
    $w = $doc.Tables.Item($k).Rows.Item(1).Cells.Item(1).Width
    if ($w -gt $maxW) { $maxW = $w; $body_table = $doc.Tables.Item($k) }
}
if ($body_table) {
    $body_table.AllowAutoFit = $false
    $body_table.AutoFitBehavior(0)
    $body_table.PreferredWidthType = 3
    $body_table.PreferredWidth = $widthPt
    for ($r = 1; $r -le $body_table.Rows.Count; $r++) {
        $row = $body_table.Rows.Item($r)
        $row.AllowBreakAcrossPages = $true
        $row.HeightRule = 0
    }
}

$doc.SaveAs2($OutDocx, 16)
if ($ExportPdf) { $doc.ExportAsFixedFormat([IO.Path]::ChangeExtension($OutDocx, '.pdf'), 17) }
"生成 $OutDocx（页数 $($doc.ComputeStatistics(2))，图 $($doc.InlineShapes.Count)）"
$doc.Close(0); $word.Quit()
