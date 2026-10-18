param(
    [string]$WorkDir,
    [string]$LaunchCommand,
    [string]$StatusCommand,
    [string]$LogPath,
    [int]$WaitSeconds = 300,
    [int]$StallMinutes = 120,
    [int]$MaxLoops = 0
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $WorkDir)) {
    throw "WorkDir not found: $WorkDir"
}

function Get-FileWriteTimeSafe([string]$Path) {
    if (Test-Path -LiteralPath $Path) {
        return (Get-Item -LiteralPath $Path).LastWriteTime
    }
    return $null
}

$loop = 0
$lastLogTime = Get-FileWriteTimeSafe $LogPath
$lastHealthyTime = Get-Date

while ($true) {
    $loop++
    Push-Location $WorkDir
    try {
        Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] status check #$loop"
        Invoke-Expression $StatusCommand

        $currentLogTime = Get-FileWriteTimeSafe $LogPath
        if ($currentLogTime -and ($null -eq $lastLogTime -or $currentLogTime -gt $lastLogTime)) {
            $lastLogTime = $currentLogTime
            $lastHealthyTime = Get-Date
            Write-Host "log updated: $lastLogTime"
        }

        $stalledFor = (New-TimeSpan -Start $lastHealthyTime -End (Get-Date)).TotalMinutes
        if ($stalledFor -ge $StallMinutes) {
            Write-Host "stalled for $([math]::Round($stalledFor, 1)) minutes, relaunch worker"
            Invoke-Expression $LaunchCommand
            $lastHealthyTime = Get-Date
        }
    }
    finally {
        Pop-Location
    }

    if ($MaxLoops -gt 0 -and $loop -ge $MaxLoops) {
        break
    }

    Start-Sleep -Seconds $WaitSeconds
}
