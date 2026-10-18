param(
    [Parameter(Mandatory=$true)][string]$InputDocx,
    [Parameter(Mandatory=$true)][string]$OutputDirectory
)
$ErrorActionPreference = 'Stop'
# This fallback never opens or saves the author's live document.
$taskInput = (Resolve-Path -LiteralPath $InputDocx).Path
$taskOutput = [IO.Path]::GetFullPath($OutputDirectory)
if (Test-Path -LiteralPath $taskOutput) { throw 'Use a new, empty output directory for each render.' }
New-Item -ItemType Directory -Path $taskOutput | Out-Null
$taskCopy = Join-Path $taskOutput 'render-input.docx'
$taskPdf = Join-Path $taskOutput 'render.pdf'
Copy-Item -LiteralPath $taskInput -Destination $taskCopy
function Get-TaskHash([string]$Path) {
    $hash = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($hash.ComputeHash([IO.File]::ReadAllBytes($Path)))).Replace('-', '').ToLowerInvariant() }
    finally { $hash.Dispose() }
}
$taskBefore = Get-TaskHash $taskInput
$taskCopyHash = Get-TaskHash $taskCopy
if ($taskCopyHash -ne $taskBefore) { throw 'Input changed while copying.' }
$taskWord = $null
$taskDocument = $null
try {
    $taskWord = New-Object -ComObject Word.Application
    $taskWord.Visible = $false
    $taskWord.DisplayAlerts = 0
    $taskWord.AutomationSecurity = 3
    $taskWord.Options.UpdateLinksAtOpen = $false
    $taskVersion = $taskWord.Version
    $taskDocument = $taskWord.Documents.Open($taskCopy, $false, $true, $false)
    if (-not $taskDocument.ReadOnly) { throw 'Render copy was not opened read-only.' }
    $taskDocument.Repaginate()
    $taskPages = $taskDocument.ComputeStatistics(2)
    $taskDocument.ExportAsFixedFormat($taskPdf, 17)
    $receipt = @{
        docx = $taskInput; docx_sha256 = $taskBefore; copy_sha256 = $taskCopyHash
        pdf = $taskPdf; pdf_sha256 = (Get-TaskHash $taskPdf)
        read_only = $true; renderer = 'Microsoft Word'; renderer_version = $taskVersion
        page_count = $taskPages; exported_at_utc = [DateTime]::UtcNow.ToString('o')
    }
    $receipt | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskOutput 'word-export.json') -Encoding UTF8
    if ((Get-TaskHash $taskInput) -ne $taskBefore) { throw 'Original changed during export.' }
    Write-Output $taskPdf
}
finally {
    if ($taskDocument) {
        $taskDocument.Close(0)
        [Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskDocument) | Out-Null
    }
    if ($taskWord) {
        $taskWord.Quit(0)
        [Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskWord) | Out-Null
    }
}
