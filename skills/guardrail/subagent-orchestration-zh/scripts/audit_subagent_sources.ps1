param(
    [string[]]$ZipPath = @(
        "C:\Users\zbh\.agents\awesome-codex-subagents-main.zip",
        "C:\Users\zbh\.agents\Codex-Subagent-Orchestrator-main.zip"
    ),
    [string[]]$AgentDir = @(
        (Join-Path $env:USERPROFILE ".codex\agents"),
        (Join-Path (Get-Location) ".codex\agents")
    ),
    [string]$SkillsRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
)

Set-StrictMode -Version Latest
Add-Type -AssemblyName System.IO.Compression.FileSystem

function Read-ZipEntryText {
    param(
        [Parameter(Mandatory=$true)]$Zip,
        [Parameter(Mandatory=$true)]$Entry
    )
    $stream = $Entry.Open()
    try {
        $reader = [System.IO.StreamReader]::new($stream, [System.Text.Encoding]::UTF8)
        try {
            return $reader.ReadToEnd()
        }
        finally {
            $reader.Dispose()
        }
    }
    finally {
        $stream.Dispose()
    }
}

function Get-TomlName {
    param([string]$Text)
    if ($Text -match '(?m)^\s*name\s*=\s*"([^"]+)"') {
        return $Matches[1]
    }
    return $null
}

function Get-SkillName {
    param([string]$Text)
    if ($Text -match '(?m)^name:\s*(.+)$') {
        return ($Matches[1].Trim().Trim('"').Trim("'"))
    }
    return $null
}

function Get-InstalledAgentNames {
    param([string[]]$Dirs)
    $names = New-Object System.Collections.Generic.List[string]
    foreach ($dir in $Dirs) {
        if (-not (Test-Path $dir)) { continue }
        Get-ChildItem -Path $dir -Filter "*.toml" -File -ErrorAction SilentlyContinue | ForEach-Object {
            $text = [System.IO.File]::ReadAllText($_.FullName, [System.Text.Encoding]::UTF8)
            $name = Get-TomlName -Text $text
            if ($name) { $names.Add($name) }
        }
    }
    return @($names | Sort-Object -Unique)
}

function Get-LocalSkillNames {
    param([string]$Root)
    if (-not (Test-Path $Root)) { return @() }
    $names = New-Object System.Collections.Generic.List[string]
    Get-ChildItem -Path $Root -Recurse -Filter "SKILL.md" -File | Where-Object {
        $_.FullName -notmatch '[\\/]scripts[\\/]' -and $_.FullName -notmatch '[\\/]references[\\/]'
    } | ForEach-Object {
        $text = [System.IO.File]::ReadAllText($_.FullName, [System.Text.Encoding]::UTF8)
        $name = Get-SkillName -Text $text
        if ($name) { $names.Add($name) }
    }
    return @($names | Sort-Object -Unique)
}

$installedAgentNames = Get-InstalledAgentNames -Dirs $AgentDir
$localSkillNames = Get-LocalSkillNames -Root $SkillsRoot
$results = New-Object System.Collections.Generic.List[object]

foreach ($zipItem in $ZipPath) {
    $resolvedZip = $zipItem
    if (Test-Path $zipItem) {
        $resolvedZip = (Resolve-Path $zipItem).Path
    }

    if (-not (Test-Path $resolvedZip)) {
        $results.Add([PSCustomObject]@{
            ZipPath = $zipItem
            Found = $false
            Entries = 0
            TomlCount = 0
            SkillMdCount = 0
            LicenseEntries = @()
            TomlNameSample = @()
            SkillNames = @()
            InstalledAgentNameConflicts = @()
            LocalSkillNameConflicts = @()
            Notes = "zip not found"
        })
        continue
    }

    $zip = [System.IO.Compression.ZipFile]::OpenRead($resolvedZip)
    try {
        $entries = @($zip.Entries)
        $tomlEntries = @($entries | Where-Object { $_.FullName -like "*.toml" })
        $skillEntries = @($entries | Where-Object { $_.FullName -match '(^|/)SKILL\.md$' })
        $licenseEntries = @($entries | Where-Object { $_.FullName -match '(^|/)(LICENSE|UPSTREAM\.md)$' } | Select-Object -ExpandProperty FullName)

        $tomlNames = New-Object System.Collections.Generic.List[string]
        foreach ($entry in $tomlEntries) {
            $text = Read-ZipEntryText -Zip $zip -Entry $entry
            $name = Get-TomlName -Text $text
            if ($name) { $tomlNames.Add($name) }
        }
        $tomlNamesUnique = @($tomlNames | Sort-Object -Unique)

        $skillNames = New-Object System.Collections.Generic.List[string]
        foreach ($entry in $skillEntries) {
            $text = Read-ZipEntryText -Zip $zip -Entry $entry
            $name = Get-SkillName -Text $text
            if ($name) { $skillNames.Add($name) }
        }
        $skillNamesUnique = @($skillNames | Sort-Object -Unique)

        $agentConflicts = @($tomlNamesUnique | Where-Object { $installedAgentNames -contains $_ })
        $skillConflicts = @($skillNamesUnique | Where-Object { $localSkillNames -contains $_ })

        $notes = New-Object System.Collections.Generic.List[string]
        if ($tomlEntries.Count -gt 0) { $notes.Add("toml-role-library") }
        if ($skillEntries.Count -gt 0) { $notes.Add("skill-package") }
        if ($licenseEntries.Count -eq 0) { $notes.Add("no-license-entry-detected") }
        if ($agentConflicts.Count -gt 0) { $notes.Add("installed-agent-name-conflict") }
        if ($skillConflicts.Count -gt 0) { $notes.Add("local-skill-name-conflict") }

        $results.Add([PSCustomObject]@{
            ZipPath = $resolvedZip
            Found = $true
            Entries = $entries.Count
            TomlCount = $tomlEntries.Count
            SkillMdCount = $skillEntries.Count
            LicenseEntries = $licenseEntries
            TomlNameSample = @($tomlNamesUnique | Select-Object -First 20)
            SkillNames = $skillNamesUnique
            InstalledAgentNameConflicts = $agentConflicts
            LocalSkillNameConflicts = $skillConflicts
            Notes = @($notes)
        })
    }
    finally {
        $zip.Dispose()
    }
}

$results
