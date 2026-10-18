param([string]$Source,[Parameter(Mandatory=$true)][string]$Destination,[string]$Metadata,[switch]$Cleanup,[string]$StructureDocx,[string]$ParagraphMap)
$ErrorActionPreference = 'Stop'
$ownerPath = $Destination + '.owner.json'
if ($Cleanup) {
    if (Test-Path -LiteralPath $ownerPath) {
        $owner = Get-Content -LiteralPath $ownerPath -Raw | ConvertFrom-Json
        $ownedProcess = if ($owner.process_id -gt 0) { Get-Process -Id $owner.process_id -ErrorAction SilentlyContinue } else { $null }
        if ($owner.owned -and $null -ne $ownedProcess -and $ownedProcess.ProcessName -eq 'WINWORD' -and $ownedProcess.StartTime.ToUniversalTime().Ticks.ToString() -eq $owner.start_ticks) {
            Stop-Process -Id $ownedProcess.Id
        }
    }
    exit
}
$previousIds = @(Get-Process WINWORD -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id)
$word = $null
$doc = $null
# Read-only conversion avoids executing macros or changing the submitted file.
try {
    $word = New-Object -ComObject Word.Application
    $newProcesses = @(Get-Process WINWORD -ErrorAction SilentlyContinue | Where-Object { $_.Id -notin $previousIds })
    if ($newProcesses.Count -eq 1) {
        $ownedProcess = $newProcesses[0]
        @{process_id=$ownedProcess.Id;start_ticks=$ownedProcess.StartTime.ToUniversalTime().Ticks.ToString();owned=$true} | ConvertTo-Json | Set-Content -LiteralPath $ownerPath -Encoding UTF8
    }
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $word.AutomationSecurity = 3
    $word.Options.UpdateLinksAtOpen = $false
    $word.Options.SaveNormalPrompt = $false
    $doc = $word.Documents.Open($Source, $false, $true, $false, '__no_password__')
    # A new OOXML copy exposes structure/media of legacy DOC without saving it.
    if ($StructureDocx) {
        if ([IO.Path]::GetExtension($Source).ToLowerInvariant() -eq '.docx') {
            Copy-Item -LiteralPath $Source -Destination $StructureDocx
        } else {
            $doc.SaveAs2($StructureDocx, 16)
        }
    }
    $doc.Repaginate()
    $doc.ExportAsFixedFormat($Destination, 17, $false)
    if ($ParagraphMap) {
        # Headless Range.Information reported the final page for every range;
        # use actual page-start character offsets instead of that unreliable API.
        $pageOffsets = @()
        $pageCount = $doc.Content.Information(4)
        for ($pageNumber=1; $pageNumber -le $pageCount; $pageNumber++) {
            $pageRange = $doc.GoTo(1, 1, $pageNumber)
            $pageOffsets += [int]$pageRange.Start
            [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($pageRange)
        }
        $paragraphs = @()
        $index = 0
        foreach ($paragraph in $doc.Paragraphs) {
            $range = $paragraph.Range
            $start = [int]$range.Start
            $end = [int]$range.End
            $firstPage = 1
            $lastPage = 1
            for ($pageIndex=0; $pageIndex -lt $pageOffsets.Count; $pageIndex++) {
                if ($pageOffsets[$pageIndex] -le $start) { $firstPage=$pageIndex+1 }
                if ($pageOffsets[$pageIndex] -lt $end) { $lastPage=$pageIndex+1 }
            }
            $paragraphs += @{index=$index; text=$range.Text; start=$start; end=$end; page_start=$firstPage; page_end=$lastPage}
            $index++
            [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($range)
            [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($paragraph)
        }
        ConvertTo-Json -InputObject @($paragraphs) -Depth 5 | Set-Content -LiteralPath $ParagraphMap -Encoding UTF8
    }
    $doc.Repaginate()
    # Range.Information reflects rendered pagination; ComputeStatistics returned
    # 1 for a seven-page legacy .doc in this environment, so retain it only as diagnostic.
    $info = @{pages=$doc.Content.Information(4); statistics_pages=$doc.ComputeStatistics(2); inline_shapes=$doc.InlineShapes.Count; floating_shapes=$doc.Shapes.Count; converter='Microsoft Word'; version=$word.Version}
    $info | ConvertTo-Json | Set-Content -LiteralPath $Metadata -Encoding UTF8
} finally {
    $closeMode = 0
    try {
        if ($null -ne $doc) {
            try { $doc.Close([ref]$closeMode) }
            finally { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($doc) }
        }
    } finally {
        if ($null -ne $word) {
            try { $word.Quit([ref]$closeMode) }
            finally { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($word) }
        }
    }
}
