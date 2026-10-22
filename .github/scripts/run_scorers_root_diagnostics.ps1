$ErrorActionPreference = 'Stop'

function Expand-GzipBase64([string[]]$parts,[string]$dest) {
  $b64 = ($parts | Sort-Object | ForEach-Object { Get-Content $_ -Raw }) -join ''
  $bytes = [Convert]::FromBase64String($b64)
  $input = [IO.MemoryStream]::new($bytes)
  $gzip = [IO.Compression.GZipStream]::new($input,[IO.Compression.CompressionMode]::Decompress)
  $output = [IO.File]::Create($dest)
  try { $gzip.CopyTo($output) } finally { $output.Dispose(); $gzip.Dispose(); $input.Dispose() }
}

$parts = Get-ChildItem '.github/scripts/consolidate_initial_database.py.gz.b64.part*' | ForEach-Object FullName
Expand-GzipBase64 $parts '.github/scripts/consolidate_initial_database.py'
Expand-GzipBase64 @('.github/scripts/test_initial_database.py.gz.b64') '.github/scripts/test_initial_database.py'

$zip = 'FutBR_Manager_Desktop_RC1_TAURI_SOURCE.zip'
if (-not (Test-Path $zip)) {
  $zipParts = Get-ChildItem -File 'FutBR_Manager_Desktop_RC1_TAURI_SOURCE.zip.part*' | Sort-Object Name
  $out = [System.IO.File]::Open($zip,[System.IO.FileMode]::Create,[System.IO.FileAccess]::Write)
  try {
    foreach ($part in $zipParts) {
      $stream = [System.IO.File]::OpenRead($part.FullName)
      try { $stream.CopyTo($out) } finally { $stream.Dispose() }
    }
  } finally { $out.Dispose() }
}
$expected = ((Get-Content 'FutBR_Manager_Desktop_RC1_TAURI_SOURCE.zip.sha256.txt' -Raw).Trim() -split '\s+')[0].ToLowerInvariant()
$actual = (Get-FileHash $zip -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actual -ne $expected) { throw "SHA-256 invalido: $actual" }

$work = Join-Path $env:RUNNER_TEMP 'futbr-scorers-root-diagnostic'
if (Test-Path $work) { Remove-Item $work -Recurse -Force }
Expand-Archive -LiteralPath $zip -DestinationPath $work -Force
$project = Join-Path $work 'FutBR_Manager_Desktop_RC1'
$dist = Join-Path $env:RUNNER_TEMP 'futbr-scorers-diagnostics'
if (Test-Path $dist) { Remove-Item $dist -Recurse -Force }
New-Item -ItemType Directory -Force -Path $dist | Out-Null
"FUTBR_SCORERS_DIAGNOSTICS=$dist" | Out-File -FilePath $env:GITHUB_ENV -Append -Encoding utf8

function Run-Python([string]$script) {
  Write-Host "Executando $script"
  python $script $project
  if ($LASTEXITCODE -ne 0) { throw "Falha em $script" }
}
function Save-Diagnostic([string]$prefix) {
  Run-Python '.github/scripts/diagnose_scorers_root.py'
  Copy-Item "$project/scorers-root-diagnostic.json" "$dist/$prefix.json" -Force
  Copy-Item "$project/scorers-root-diagnostic.txt" "$dist/$prefix.txt" -Force
}

Run-Python '.github/scripts/prepare_desktop_project.py'
Run-Python '.github/scripts/fix_root_gameplay.py'
Run-Python '.github/scripts/fix_gameplay_parity.py'
Run-Python '.github/scripts/fix_national_match_parity.py'
Save-Diagnostic '01-source-after-gameplay'

Run-Python '.github/scripts/hide_how_to_play_ui.py'
Run-Python '.github/scripts/externalize_crests.py'
Run-Python '.github/scripts/externalize_player_base.py'
Run-Python '.github/scripts/consolidate_initial_database.py'
Run-Python '.github/scripts/harden_save_storage.py'
Run-Python '.github/scripts/optimize_save_load.py'
Run-Python '.github/scripts/optimize_long_career_memory.py'
Run-Python '.github/scripts/optimize_player_storage.py'
Run-Python '.github/scripts/optimize_direct_load.py'
Run-Python '.github/scripts/add_relational_history_storage.py'
Run-Python '.github/scripts/finalize_prebuilt_boot.py'
Save-Diagnostic '02-after-performance-and-finalize'

Run-Python '.github/scripts/fix_scorers_navigation.py'
Run-Python '.github/scripts/fix_scorers_live_runtime.py'
Save-Diagnostic '03-current-final-html'

Set-Content "$dist/README.md" @(
  '# Diagnostico da causa raiz de Artilheiros',
  '',
  '- 01: fonte reconstruida apos correcoes de gameplay.',
  '- 02: apos todas as otimizacoes de performance e finalize_prebuilt_boot.',
  '- 03: HTML atual depois das camadas 18.202/18.203.'
) -Encoding utf8

Write-Host "Diagnosticos gravados em $dist"
