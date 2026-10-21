$ErrorActionPreference = 'Stop'

function Expand-GzipBase64([string[]]$parts,[string]$dest) {
  $b64 = ($parts | Sort-Object | ForEach-Object { Get-Content $_ -Raw }) -join ''
  $bytes = [Convert]::FromBase64String($b64)
  $input = [IO.MemoryStream]::new($bytes)
  $gzip = [IO.Compression.GZipStream]::new($input,[IO.Compression.CompressionMode]::Decompress)
  $output = [IO.File]::Create($dest)
  try { $gzip.CopyTo($output) } finally { $output.Dispose(); $gzip.Dispose(); $input.Dispose() }
}

Write-Host 'Preparando scripts compactados...'
$parts = Get-ChildItem '.github/scripts/consolidate_initial_database.py.gz.b64.part*' | ForEach-Object FullName
if (-not $parts) { throw 'Partes do consolidador nao encontradas.' }
Expand-GzipBase64 $parts '.github/scripts/consolidate_initial_database.py'
Expand-GzipBase64 @('.github/scripts/test_initial_database.py.gz.b64') '.github/scripts/test_initial_database.py'

$pythonScripts = @(
  '.github/scripts/prepare_desktop_project.py',
  '.github/scripts/fix_root_gameplay.py',
  '.github/scripts/fix_gameplay_parity.py',
  '.github/scripts/fix_national_match_parity.py',
  '.github/scripts/externalize_crests.py',
  '.github/scripts/externalize_player_base.py',
  '.github/scripts/harden_save_storage.py',
  '.github/scripts/optimize_save_load.py',
  '.github/scripts/optimize_long_career_memory.py',
  '.github/scripts/optimize_player_storage.py',
  '.github/scripts/optimize_direct_load.py',
  '.github/scripts/add_relational_history_storage.py',
  '.github/scripts/diagnose_boot_performance.py',
  '.github/scripts/fix_mls_vacation.py',
  '.github/scripts/fix_mls_vacation_idempotency.py',
  '.github/scripts/fix_mls_vacation_ui.py',
  '.github/scripts/test_mls_vacation.py',
  '.github/scripts/test_player_storage.py',
  '.github/scripts/test_create_stream_integrity.py',
  '.github/scripts/test_direct_load.py',
  '.github/scripts/test_login_boot.py',
  '.github/scripts/test_runtime_boot.py',
  '.github/scripts/test_final_ui_integrity.py',
  '.github/scripts/finalize_prebuilt_boot.py',
  '.github/scripts/consolidate_initial_database.py',
  '.github/scripts/test_initial_database.py',
  '.github/scripts/test_create_performance.py',
  '.github/scripts/test_relational_history.py',
  '.github/scripts/test_root_gameplay.py',
  '.github/scripts/hide_how_to_play_ui.py',
  '.github/scripts/validate_desktop_architecture.py'
)
python -m py_compile @pythonScripts
if ($LASTEXITCODE -ne 0) { throw 'Falha na validacao de sintaxe Python.' }

Write-Host 'Remontando pacote fonte...'
$zip = 'FutBR_Manager_Desktop_RC1_TAURI_SOURCE.zip'
if (-not (Test-Path $zip)) {
  $zipParts = Get-ChildItem -File 'FutBR_Manager_Desktop_RC1_TAURI_SOURCE.zip.part*' | Sort-Object Name
  if (-not $zipParts) { throw 'Partes do pacote fonte nao encontradas.' }
  $out = [System.IO.File]::Open($zip,[System.IO.FileMode]::Create,[System.IO.FileAccess]::Write)
  try {
    foreach ($part in $zipParts) {
      $stream = [System.IO.File]::OpenRead($part.FullName)
      try { $stream.CopyTo($out) } finally { $stream.Dispose() }
    }
  } finally { $out.Dispose() }
}
if (Test-Path 'FutBR_Manager_Desktop_RC1_TAURI_SOURCE.zip.sha256.txt') {
  $expected = ((Get-Content 'FutBR_Manager_Desktop_RC1_TAURI_SOURCE.zip.sha256.txt' -Raw).Trim() -split '\s+')[0].ToLowerInvariant()
  $actual = (Get-FileHash $zip -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($actual -ne $expected) { throw "SHA-256 invalido: $actual" }
}

$work = Join-Path $env:RUNNER_TEMP 'futbr-desktop-latest'
if (Test-Path $work) { Remove-Item $work -Recurse -Force }
New-Item -ItemType Directory -Force -Path $work | Out-Null
Expand-Archive -LiteralPath $zip -DestinationPath $work -Force
$project = Join-Path $work 'FutBR_Manager_Desktop_RC1'
if (-not (Test-Path (Join-Path $project 'src-tauri/tauri.conf.json'))) { throw 'Projeto Tauri invalido.' }
"FUTBR_PROJECT=$project" | Out-File -FilePath $env:GITHUB_ENV -Append -Encoding utf8

function Run-Python([string]$script) {
  Write-Host "Executando $script"
  python $script $project
  if ($LASTEXITCODE -ne 0) { throw "Falha em $script" }
}

Run-Python '.github/scripts/prepare_desktop_project.py'
Run-Python '.github/scripts/fix_root_gameplay.py'
Run-Python '.github/scripts/fix_gameplay_parity.py'
Run-Python '.github/scripts/fix_national_match_parity.py'
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
Run-Python '.github/scripts/diagnose_boot_performance.py'
Run-Python '.github/scripts/test_player_storage.py'
Run-Python '.github/scripts/test_create_stream_integrity.py'
Run-Python '.github/scripts/test_direct_load.py'
Run-Python '.github/scripts/test_login_boot.py'
Run-Python '.github/scripts/test_runtime_boot.py'
Run-Python '.github/scripts/test_final_ui_integrity.py'
Run-Python '.github/scripts/test_initial_database.py'
Run-Python '.github/scripts/test_create_performance.py'
Run-Python '.github/scripts/test_relational_history.py'
Run-Python '.github/scripts/test_root_gameplay.py'
Run-Python '.github/scripts/validate_desktop_architecture.py'

Write-Host 'Compilando Tauri...'
Push-Location $project
try {
  npm install
  if ($LASTEXITCODE -ne 0) { throw 'Falha no npm install.' }
  npm run tauri build -- --bundles nsis
  if ($LASTEXITCODE -ne 0) { throw 'Falha na compilacao Tauri.' }

  New-Item -ItemType Directory -Force -Path artifacts | Out-Null
  New-Item -ItemType Directory -Force -Path portable | Out-Null
  $exe = 'src-tauri/target/release/futbr-manager.exe'
  if (-not (Test-Path $exe)) { throw 'EXE final nao encontrado.' }
  Copy-Item $exe 'portable/FutBR Manager.exe'
  Copy-Item 'src/assets/data/rosters.v310.bin' 'portable/rosters.v310.bin'
  Set-Content 'portable/portable.flag' 'FutBR Manager portable mode' -Encoding ascii
  Set-Content 'portable/LEIA-ME.txt' @(
    'FUTBR MANAGER - DESKTOP RC1 PORTATIL',
    '',
    'Extraia a pasta inteira e execute FutBR Manager.exe.',
    'Nao apague portable.flag nem rosters.v310.bin.',
    'Os saves ficam em FutBR Manager Data\saves ao lado do EXE.',
    'F11 alterna tela cheia. Alt+F4 fecha o jogo.'
  ) -Encoding utf8
  Compress-Archive -Path 'portable/*' -DestinationPath 'artifacts/FutBR-Manager-Desktop-RC1-PORTATIL.zip' -Force
  $nsis = Get-ChildItem 'src-tauri/target/release/bundle/nsis' -Filter '*.exe' | Select-Object -First 1
  if (-not $nsis) { throw 'Instalador NSIS nao encontrado.' }
  Copy-Item $nsis.FullName 'artifacts/FutBR-Manager-Desktop-RC1-INSTALADOR.exe'
  Copy-Item 'mls-vacation-tests.json' 'artifacts/mls-vacation-tests.json'
  Copy-Item 'create-performance-tests.json' 'artifacts/create-performance-tests.json'
  Copy-Item 'architecture-validation.json' 'artifacts/architecture-validation.json'
  Get-ChildItem artifacts | Format-Table Name,Length
} finally {
  Pop-Location
}

Write-Host 'Build e testes concluidos.'
