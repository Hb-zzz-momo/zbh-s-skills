# 把 docx 渲染成 PDF，供版式门禁检查。
# 容器/服务器上装了 LibreOffice 时用 documents 技能的 render_docx.py；Windows 桌面用本脚本走 Word COM。
# 用法: powershell -NoProfile -File render_docx.ps1 -In <in.docx> -Out <out.pdf> [-Engine Word|WPS]
param(
  [Parameter(Mandatory=$true)][string]$In,
  [Parameter(Mandatory=$true)][string]$Out,
  [ValidateSet('Word','WPS')][string]$Engine = 'Word'
)
$ErrorActionPreference = 'Stop'
$progId = if ($Engine -eq 'Word') { 'Word.Application' } else { 'KWps.Application' }
$app = New-Object -ComObject $progId
try {
  try { $app.Visible = $false } catch {}
  $doc = $app.Documents.Open($In, $false, $true)   # ConfirmConversions=$false, ReadOnly=$true
  $doc.ExportAsFixedFormat($Out, 17)               # 17 = wdExportFormatPDF
  $doc.Close(0)
} finally {
  if ($Engine -eq 'Word') { try { $app.Quit() } catch {} }
}
Write-Output "rendered: $Out"
