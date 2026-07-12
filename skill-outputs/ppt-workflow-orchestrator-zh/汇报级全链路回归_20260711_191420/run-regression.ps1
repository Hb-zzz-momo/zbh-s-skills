param([ValidateSet('powerpoint','wps','libreoffice','auto')][string]$Backend='auto')
$ErrorActionPreference='Stop'
$root=$PSScriptRoot
$builder=Join-Path $root 'src/builder'
$python='python'

Push-Location $builder
try {
  npm ci
  npm test
  & (Join-Path $builder 'node_modules/.bin/tsx.cmd') (Join-Path $builder 'scripts/init-deck.ts') --spec (Join-Path $root 'slide-spec.json') --design (Join-Path $root 'PRESENTATION_DESIGN.md') --assets-root $root --output (Join-Path $root 'presentation-rebuilt.pptx') --manifest (Join-Path $root 'qa/rebuilt-build-manifest.json')
} finally { Pop-Location }

& $python (Join-Path $root 'src/orchestrator/scripts/validate_contract.py') --spec (Join-Path $root 'slide-spec.json') --sources (Join-Path $root 'sources.json') --output (Join-Path $root 'qa/rebuilt-contract.json')
& $python (Join-Path $root 'src/qa/scripts/render_slides.py') (Join-Path $root 'presentation-rebuilt.pptx') (Join-Path $root 'qa/rebuilt-render') --backend $Backend
& $python (Join-Path $root 'src/qa/scripts/extract_text.py') (Join-Path $root 'presentation-rebuilt.pptx') --markdown (Join-Path $root 'qa/rebuilt-text.md') --json (Join-Path $root 'qa/rebuilt-text.json')
& $python (Join-Path $root 'src/qa/scripts/check_geometry.py') (Join-Path $root 'presentation-rebuilt.pptx') --output (Join-Path $root 'qa/rebuilt-geometry.json')
& $python (Join-Path $root 'src/qa/scripts/check_image_resolution.py') (Join-Path $root 'presentation-rebuilt.pptx') --output (Join-Path $root 'qa/rebuilt-images.json') --min-ppi 150
& $python (Join-Path $root 'src/qa/scripts/check_charts.py') (Join-Path $root 'presentation-rebuilt.pptx') --output (Join-Path $root 'qa/rebuilt-charts.json') --min-charts 1
& $python (Join-Path $root 'src/qa/scripts/check_contrast.py') (Join-Path $root 'presentation-rebuilt.pptx') --output (Join-Path $root 'qa/rebuilt-contrast.json') --background F7F4ED
if($env:OS -eq 'Windows_NT'){& $python (Join-Path $root 'src/qa/scripts/check_office_layout.py') (Join-Path $root 'presentation-rebuilt.pptx') --output (Join-Path $root 'qa/rebuilt-office-layout.json') --expected-font 'Microsoft YaHei'}
Write-Host "Regression rebuild complete: $root"
