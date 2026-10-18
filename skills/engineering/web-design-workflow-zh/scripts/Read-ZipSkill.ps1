[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ZipPath,

    [string]$EntryPath,

    [switch]$List,

    [string]$Pattern = '(?i)SKILL\.md$'
)

$resolvedZip = (Resolve-Path -LiteralPath $ZipPath -ErrorAction Stop).Path

Add-Type -AssemblyName System.IO.Compression.FileSystem

$archive = $null
try {
    $archive = [System.IO.Compression.ZipFile]::OpenRead($resolvedZip)

    if ($List) {
        $archive.Entries |
            Where-Object { $_.FullName -match $Pattern } |
            Select-Object -ExpandProperty FullName
        return
    }

    if ([string]::IsNullOrWhiteSpace($EntryPath)) {
        throw 'EntryPath is required unless -List is used.'
    }

    $normalizedEntry = $EntryPath.Replace('\', '/')
    $entry = $archive.GetEntry($normalizedEntry)
    if ($null -eq $entry) {
        throw "Entry not found: $normalizedEntry"
    }

    $reader = [System.IO.StreamReader]::new(
        $entry.Open(),
        [System.Text.Encoding]::UTF8,
        $true
    )
    try {
        $reader.ReadToEnd()
    }
    finally {
        $reader.Dispose()
    }
}
finally {
    if ($null -ne $archive) {
        $archive.Dispose()
    }
}
