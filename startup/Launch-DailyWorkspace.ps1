param(
    [switch]$DryRun
)

$ErrorActionPreference = 'Continue'

$logDir = Join-Path $env:LOCALAPPDATA 'StartupAppLauncher'
$null = New-Item -ItemType Directory -Force -Path $logDir
$logPath = Join-Path $logDir 'Launch-DailyWorkspace.log'

function Write-Log {
    param([string]$Message)

    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    Add-Content -LiteralPath $logPath -Value "[$timestamp] $Message" -Encoding UTF8
}

function Get-RegistryDefaultValue {
    param([string]$KeyPath)

    try {
        if (Test-Path -LiteralPath $KeyPath) {
            return (Get-Item -LiteralPath $KeyPath).GetValue('')
        }
    }
    catch {
        Write-Log "Registry lookup failed: $KeyPath :: $($_.Exception.Message)"
    }

    return $null
}

function Get-CommandSource {
    param([string]$CommandName)

    try {
        $command = Get-Command $CommandName -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($command) {
            return $command.Source
        }
    }
    catch {
        Write-Log "Command lookup failed: $CommandName :: $($_.Exception.Message)"
    }

    return $null
}

function Get-FirstExistingPath {
    param([string[]]$Candidates)

    foreach ($candidate in $Candidates) {
        if ([string]::IsNullOrWhiteSpace($candidate)) {
            continue
        }

        $expanded = [Environment]::ExpandEnvironmentVariables($candidate)
        if (Test-Path -LiteralPath $expanded) {
            return $expanded
        }
    }

    return $null
}

function Quote-Argument {
    param([string]$Value)

    if ($null -eq $Value) {
        return '""'
    }

    return '"' + ($Value -replace '"', '\"') + '"'
}

function Start-CheckedProcess {
    param(
        [string]$Label,
        [string]$FilePath,
        [string[]]$Arguments = @()
    )

    if ([string]::IsNullOrWhiteSpace($FilePath)) {
        Write-Log "SKIP $Label : executable path is empty"
        return
    }

    if (-not (Test-Path -LiteralPath $FilePath)) {
        Write-Log "SKIP $Label : executable not found: $FilePath"
        return
    }

    $argText = if ($Arguments.Count -gt 0) { $Arguments -join ' ' } else { '' }
    Write-Log "START $Label : $FilePath $argText"

    if ($DryRun) {
        return
    }

    try {
        if ($Arguments.Count -gt 0) {
            Start-Process -FilePath $FilePath -ArgumentList $Arguments -ErrorAction Stop
        }
        else {
            Start-Process -FilePath $FilePath -ErrorAction Stop
        }
    }
    catch {
        Write-Log "ERROR $Label : $($_.Exception.Message)"
    }
}

function Start-StoreAppByName {
    param(
        [string]$Label,
        [string]$NamePattern
    )

    try {
        $app = Get-StartApps |
            Where-Object { $_.Name -match $NamePattern } |
            Select-Object -First 1

        if (-not $app) {
            Write-Log "SKIP $Label : Start menu app not found by pattern $NamePattern"
            return $false
        }

        Write-Log "START $Label : shell:AppsFolder\$($app.AppID)"

        if (-not $DryRun) {
            Start-Process -FilePath 'explorer.exe' -ArgumentList ("shell:AppsFolder\$($app.AppID)") -ErrorAction Stop
        }

        return $true
    }
    catch {
        Write-Log "ERROR $Label : $($_.Exception.Message)"
        return $false
    }
}

Write-Log '===== Startup launch begin ====='

$typoraExe = Get-FirstExistingPath @(
    (Get-RegistryDefaultValue 'HKLM:\Software\Microsoft\Windows\CurrentVersion\App Paths\Typora.exe'),
    (Get-RegistryDefaultValue 'HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths\Typora.exe'),
    (Get-CommandSource 'Typora.exe'),
    'D:\using app\Typora\Typora.exe',
    'C:\Program Files\Typora\Typora.exe',
    'C:\Program Files (x86)\Typora\Typora.exe',
    '%LOCALAPPDATA%\Programs\Typora\Typora.exe'
)

$chromeExe = Get-FirstExistingPath @(
    (Get-CommandSource 'chrome.exe'),
    'C:\Program Files\Google\Chrome\Application\chrome.exe',
    'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
    '%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe'
)

$edgeExe = Get-FirstExistingPath @(
    (Get-CommandSource 'msedge.exe'),
    'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
    '%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe'
)

$codeExe = Get-FirstExistingPath @(
    (Get-CommandSource 'code.exe'),
    'D:\newapp\Microsoft VS Code\Code.exe',
    '%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe',
    'C:\Program Files\Microsoft VS Code\Code.exe',
    (Get-CommandSource 'code.cmd')
)

# Build Chinese paths without non-ASCII script text so Windows PowerShell reads this file reliably.
$cloudName = 'WPS' + [string][char]0x4E91 + [string][char]0x76D8
$wpsRoot = Join-Path 'D:\wps\1286397831' $cloudName
$answerFolder = [string][char]0x7B54 + [string][char]0x7591
$toolsFolder = [string][char]0x5DE5 + [string][char]0x5177

$typoraFolders = @(
    (Join-Path $wpsRoot 'ai'),
    (Join-Path $wpsRoot $answerFolder),
    (Join-Path $wpsRoot $toolsFolder)
)

foreach ($folder in $typoraFolders) {
    if (Test-Path -LiteralPath $folder) {
        Start-CheckedProcess -Label "Typora folder: $folder" -FilePath $typoraExe -Arguments @((Quote-Argument $folder))
        Start-Sleep -Seconds 2
    }
    else {
        Write-Log "SKIP Typora folder : folder not found: $folder"
    }
}

$chatGptUrl = 'https://chatgpt.com/'

$startedNativeChatGpt = Start-StoreAppByName -Label 'Microsoft ChatGPT app' -NamePattern '^ChatGPT$'
if (-not $startedNativeChatGpt) {
    Start-CheckedProcess -Label 'Microsoft Edge ChatGPT' -FilePath $edgeExe -Arguments @('--app=https://chatgpt.com/')
}

Start-CheckedProcess -Label 'Google Chrome ChatGPT profile 1' -FilePath $chromeExe -Arguments @(
    '--profile-directory=Default',
    '--app=https://chatgpt.com/'
)

Start-CheckedProcess -Label 'Google Chrome ChatGPT profile 2' -FilePath $chromeExe -Arguments @(
    '--profile-directory="Profile 2"',
    '--app=https://chatgpt.com/'
)

Start-CheckedProcess -Label 'Visual Studio Code' -FilePath $codeExe

Write-Log '===== Startup launch end ====='
