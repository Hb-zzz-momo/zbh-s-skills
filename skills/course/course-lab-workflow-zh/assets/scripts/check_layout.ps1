# 报告版式自检：量页数、图片缩放比例、表格宽度、正文文字边界、逐页墨迹与内容底边
# 用法：pwsh -File check_layout.ps1 -Docx "报告.docx" [-Pdf "报告.pdf"] [-ImageWidthCm 5]
# 需要：Windows + Word（读 docx 属性）、poppler 的 pdftoppm/pdftotext/pdfinfo（量 PDF）
param(
    [Parameter(Mandatory = $true)][string]$Docx,
    [string]$Pdf = '',                  # 留空表示由脚本从 docx 现导一份 PDF 再量，避免量到旧 PDF
    [double]$ImageWidthCm = 0,          # 传 0 表示不检查图片宽度是否达标
    [double]$MinInkRatio = 0.03,        # 单页墨迹低于此值提示“偏空”
    [int]$Dpi = 60
)

Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.IO.Compression.FileSystem

$tmp = Join-Path $env:TEMP ("layout-check-" + [Guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Force -Path $tmp | Out-Null

$result = [ordered]@{}

# ---------- 1. Word 侧属性：页数、图、表、图片比例 ----------
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$doc = $word.Documents.Open($Docx, [ref]$false, [ref]$true)

# 现导一份 PDF，保证页面数据与当前 docx 同版本
if (-not $Pdf) {
    $Pdf = Join-Path $tmp 'layout-check.pdf'
    $doc.ExportAsFixedFormat($Pdf, 17)
}
$result['docx'] = $Docx
$result['pages'] = $doc.ComputeStatistics(2)
$result['paragraphs'] = $doc.Paragraphs.Count
$result['tables'] = $doc.Tables.Count

$textWidthCm = ($doc.PageSetup.PageWidth - $doc.PageSetup.LeftMargin - $doc.PageSetup.RightMargin) / 28.3465
$result['text_width_cm'] = [math]::Round($textWidthCm, 2)

$tableInfo = @()
for ($k = 1; $k -le $doc.Tables.Count; $k++) {
    $t = $doc.Tables.Item($k)
    $tableInfo += [pscustomobject]@{
        table  = $k
        rows   = $t.Rows.Count
        cols   = $t.Columns.Count
        width  = [math]::Round($t.Rows.Item(1).Cells.Item(1).Width / 28.3465, 2)
        ok     = ($t.Rows.Item(1).Cells.Item(1).Width / 28.3465) -le ($textWidthCm + 0.2)
    }
}
$result['tables_detail'] = $tableInfo

$imgInfo = @()
$mediaRatios = @()
try {
    $zipCopy = Join-Path $tmp 'doc.zip'
    Copy-Item $Docx $zipCopy -Force
    $zip = [IO.Compression.ZipFile]::OpenRead($zipCopy)
    $media = $zip.Entries | Where-Object { $_.FullName -match '^word/media/.*\.(png|jpg|jpeg)$' } | Sort-Object FullName
    foreach ($m in $media) {
        $stream = $m.Open()
        $img = [Drawing.Image]::FromStream($stream)
        $mediaRatios += [math]::Round($img.Width / $img.Height, 3)
        $img.Dispose(); $stream.Close()
    }
    $zip.Dispose()
} catch { }

for ($k = 1; $k -le $doc.InlineShapes.Count; $k++) {
    $s = $doc.InlineShapes.Item($k)
    $w = $s.Width / 28.3465
    $h = $s.Height / 28.3465
    $ratio = if ($h -gt 0) { [math]::Round($w / $h, 3) } else { 0 }
    # 原图比例：优先按 docx 内嵌的 word/media 顺序取，其次尝试链接源文件
    $fileRatio = if ($mediaRatios.Count -eq $doc.InlineShapes.Count) { $mediaRatios[$k - 1] } else { $null }
    if ($null -eq $fileRatio) {
        try {
            $src = $s.LinkFormat.SourceFullName
            if ($src -and (Test-Path $src)) {
                $img = [Drawing.Image]::FromFile($src)
                $fileRatio = [math]::Round($img.Width / $img.Height, 3)
                $img.Dispose()
            }
        } catch { }
    }
    $imgInfo += [pscustomobject]@{
        index      = $k
        width_cm   = [math]::Round($w, 2)
        height_cm  = [math]::Round($h, 2)
        ratio      = $ratio
        file_ratio = $fileRatio
        not_distorted = ($null -eq $fileRatio) -or ([math]::Abs($ratio - $fileRatio) -le 0.02)
        width_ok   = ($ImageWidthCm -le 0) -or ([math]::Abs($w - $ImageWidthCm) -le 0.3)
        centered   = ($s.Range.ParagraphFormat.Alignment -eq 1)
    }
}
$result['images'] = $doc.InlineShapes.Count
$result['images_detail'] = $imgInfo
$result['media_ratio_source'] = if ($mediaRatios.Count -eq $doc.InlineShapes.Count) { 'word/media 顺序比对' } else { '内嵌图数量与插图数不一致，未做比例比对' }

$text = $doc.Content.Text
$result['figure_captions'] = ([regex]::Matches($text, '图 \d+')).Count
$result['table_captions'] = ([regex]::Matches($text, '表 \d+')).Count
$result['leftover_markers'] = ([regex]::Matches($text, '\[\[IMG\d+\]\]|\[\[TABLE\d\]\]|§')).Count
$doc.Close([ref]$false)
$word.Quit()

# ---------- 2. PDF 侧属性：文字边界、逐页墨迹与内容底边 ----------
if (Test-Path $Pdf) {
    pdftotext -bbox-layout $Pdf (Join-Path $tmp 'bbox.xml') 2>$null
    $minx = $null; $maxx = $null
    if (Test-Path (Join-Path $tmp 'bbox.xml')) {
        [xml]$bx = Get-Content (Join-Path $tmp 'bbox.xml') -Raw -Encoding UTF8
        foreach ($wd in $bx.GetElementsByTagName('word')) {
            $a = [double]$wd.GetAttribute('xMin'); $b = [double]$wd.GetAttribute('xMax')
            if ($null -eq $minx -or $a -lt $minx) { $minx = $a }
            if ($null -eq $maxx -or $b -gt $maxx) { $maxx = $b }
        }
    }
    $result['text_x_min_pt'] = if ($null -ne $minx) { [math]::Round($minx, 1) } else { $null }
    $result['text_x_max_pt'] = if ($null -ne $maxx) { [math]::Round($maxx, 1) } else { $null }

    pdftoppm -r $Dpi -png $Pdf (Join-Path $tmp 'p') 2>$null
    $pages = @()
    Get-ChildItem (Join-Path $tmp 'p-*.png') | Sort-Object Name | ForEach-Object {
        $bmp = [Drawing.Bitmap]::FromFile($_.FullName)
        $ink = 0; $tot = 0; $bottom = 0; $left = $bmp.Width; $right = 0
        for ($y = 0; $y -lt $bmp.Height; $y += 3) {
            for ($x = 0; $x -lt $bmp.Width; $x += 3) {
                $tot++
                $c = $bmp.GetPixel($x, $y)
                if (($c.R + $c.G + $c.B) -lt 700) {
                    $ink++
                    if ($y -gt $bottom) { $bottom = $y }
                    if ($x -lt $left) { $left = $x }
                    if ($x -gt $right) { $right = $x }
                }
            }
        }
        $ratio = if ($tot -gt 0) { $ink / $tot } else { 0 }
        $pages += [pscustomobject]@{
            page      = $_.BaseName
            ink       = [math]::Round($ratio, 4)
            too_empty = ($ratio -lt $MinInkRatio)
            bottom_px = $bottom
            page_h_px = $bmp.Height
            x_range   = "$left-$right"
        }
        $bmp.Dispose()
    }
    $result['pdf'] = $Pdf
    $result['pages_detail'] = $pages
}

Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
$result | ConvertTo-Json -Depth 6
