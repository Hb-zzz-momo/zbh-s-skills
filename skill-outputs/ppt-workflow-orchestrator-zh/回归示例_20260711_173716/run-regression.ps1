$ErrorActionPreference = 'Stop'
$utf8 = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = $utf8
$OutputEncoding = $utf8
$env:PYTHONUTF8 = '1'
function Assert-Native([string]$Step) { if ($LASTEXITCODE -ne 0) { throw "$Step failed with exit code $LASTEXITCODE" } }
$example = $PSScriptRoot
$repo = (Resolve-Path (Join-Path $example '..\..\..')).Path
$builder = Join-Path $repo 'skills\presentation\pptx-builder-zh'
$qa = Join-Path $repo 'skills\presentation\ppt-render-qa-zh\scripts'

Push-Location $builder
try {
    npm install
    Assert-Native 'npm install'
    npm exec tsx scripts/init-deck.ts -- --spec (Join-Path $example 'slide-spec-pass1.json') --theme (Join-Path $example 'theme.json') --output (Join-Path $example 'pass1\presentation-pass1.pptx') --manifest (Join-Path $example 'pass1\build-manifest.json')
    Assert-Native 'pass1 build'
    npm exec tsx scripts/check-bounds.ts -- --spec (Join-Path $example 'slide-spec-pass1.json') --manifest (Join-Path $example 'pass1\build-manifest.json') --output (Join-Path $example 'pass1\build-check.json')
    Assert-Native 'pass1 contract check'
    npm exec tsx scripts/init-deck.ts -- --spec (Join-Path $example 'slide-spec.json') --theme (Join-Path $example 'theme.json') --output (Join-Path $example 'presentation.pptx') --manifest (Join-Path $example 'qa\pass2\build-manifest.json')
    Assert-Native 'pass2 build'
    npm exec tsx scripts/check-bounds.ts -- --spec (Join-Path $example 'slide-spec.json') --manifest (Join-Path $example 'qa\pass2\build-manifest.json') --output (Join-Path $example 'qa\pass2\build-check.json')
    Assert-Native 'pass2 contract check'
}
finally { Pop-Location }

python (Join-Path $qa 'render_slides.py') (Join-Path $example 'pass1\presentation-pass1.pptx') (Join-Path $example 'qa\pass1\render') --backend auto
Assert-Native 'pass1 render'
python (Join-Path $qa 'make_montage.py') (Join-Path $example 'qa\pass1\render\slides') (Join-Path $example 'qa\pass1\montage.png')
Assert-Native 'pass1 montage'
python (Join-Path $qa 'render_slides.py') (Join-Path $example 'presentation.pptx') (Join-Path $example 'qa\pass2\render') --backend auto
Assert-Native 'pass2 render'
python (Join-Path $qa 'make_montage.py') (Join-Path $example 'qa\pass2\render\slides') (Join-Path $example 'qa\pass2\montage.png')
Assert-Native 'pass2 montage'
python (Join-Path $qa 'extract_text.py') (Join-Path $example 'presentation.pptx') --markdown (Join-Path $example 'qa\pass2\text.md') --json (Join-Path $example 'qa\pass2\text.json')
Assert-Native 'text extraction'
python (Join-Path $qa 'check_geometry.py') (Join-Path $example 'presentation.pptx') --output (Join-Path $example 'qa\pass2\geometry.json')
Assert-Native 'geometry check'
python (Join-Path $qa 'check_image_resolution.py') (Join-Path $example 'presentation.pptx') --output (Join-Path $example 'qa\pass2\images.json')
Assert-Native 'image resolution check'
python (Join-Path $qa 'build_qa_report.py') --render (Join-Path $example 'qa\pass2\render\render-manifest.json') --text (Join-Path $example 'qa\pass2\text.json') --geometry (Join-Path $example 'qa\pass2\geometry.json') --images (Join-Path $example 'qa\pass2\images.json') --contract (Join-Path $example 'qa\pass2\build-check.json') --previous (Join-Path $example 'pass1\build-check.json') --output (Join-Path $example 'qa\qa-report.md') --fix-log (Join-Path $example 'qa\fix-log.md')
Assert-Native 'QA report build'
