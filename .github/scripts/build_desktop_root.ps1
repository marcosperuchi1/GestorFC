$ErrorActionPreference = 'Stop'

$basePath = Join-Path $PSScriptRoot 'build_desktop_latest.ps1'
$source = Get-Content $basePath -Raw

# Mantem a cadeia de performance ja consolidada: base externa, academias prontas,
# saves fragmentados, SQLite, memoria de carreira longa e carregamento direto.
# Somente a UI e o armazenamento incremental dos rankings sao alterados,
# dentro do mesmo escopo lexical do motor.
$oldRuntime = "Run-Python '.github/scripts/finalize_prebuilt_boot.py'\r?\nRun-Python '.github/scripts/fix_scorers_navigation.py'\r?\nRun-Python '.github/scripts/fix_scorers_live_runtime.py'\r?\nRun-Python '.github/scripts/diagnose_boot_performance.py'"
$newRuntime = @"
Run-Python '.github/scripts/finalize_prebuilt_boot.py'
Run-Python '.github/scripts/fix_scorers_in_scope.py'
Run-Python '.github/scripts/optimize_rankings_in_scope.py'
Run-Python '.github/scripts/diagnose_boot_performance.py'
"@.Trim()
$source = [regex]::Replace($source, $oldRuntime, $newRuntime, 1)

foreach ($obsolete in @(
  '.github/scripts/test_final_ui_integrity.py',
  '.github/scripts/test_scorers_navigation.py',
  '.github/scripts/test_scorers_live.py'
)) {
  $escaped = [regex]::Escape($obsolete)
  $source = [regex]::Replace($source, "(?m)^Run-Python '$escaped'\r?\n", '')
}

$source = [regex]::Replace(
  $source,
  "Run-Python '\.github/scripts/test_runtime_boot\.py'",
  "Run-Python '.github/scripts/test_runtime_boot.py'`nRun-Python '.github/scripts/test_scorers_in_scope.py'",
  1
)

$source = [regex]::Replace(
  $source,
  "Run-Python '\.github/scripts/test_scorers_in_scope\.py'",
  "Run-Python '.github/scripts/test_scorers_in_scope.py'`nRun-Python '.github/scripts/finalize_rankings_18230.py'`nRun-Python '.github/scripts/stabilize_rankings_18230.py'`nRun-Python '.github/scripts/fix_incremental_club_ranking.py'`nRun-Python '.github/scripts/stabilize_incremental_ranking_18300.py'`nRun-Python '.github/scripts/test_runtime_boot.py'`nRun-Python '.github/scripts/test_rankings_18230.py'`nRun-Python '.github/scripts/test_incremental_ranking_18300.py'",
  1
)

$source = [regex]::Replace($source, "(?m)^\s*Copy-Item 'scorers-navigation-tests\.json'.*\r?\n", '')
$source = [regex]::Replace($source, "(?m)^\s*Copy-Item 'scorers-live-tests\.json'.*\r?\n", '')
$source = [regex]::Replace(
  $source,
  "(?m)^(\s*)Copy-Item 'mls-vacation-tests\.json' 'artifacts/mls-vacation-tests\.json'\r?$",
  "`$1Copy-Item 'mls-vacation-tests.json' 'artifacts/mls-vacation-tests.json'`n`$1Copy-Item 'scorers-in-scope-tests.json' 'artifacts/scorers-in-scope-tests.json'`n`$1Copy-Item 'rankings-18230-install.json' 'artifacts/rankings-18230-install.json'`n`$1Copy-Item 'rankings-18230-stability.json' 'artifacts/rankings-18230-stability.json'`n`$1Copy-Item 'rankings-18230-tests.json' 'artifacts/rankings-18230-tests.json'`n`$1Copy-Item 'incremental-ranking-18300-install.json' 'artifacts/incremental-ranking-18300-install.json'`n`$1Copy-Item 'incremental-ranking-18301-install.json' 'artifacts/incremental-ranking-18301-install.json'`n`$1Copy-Item 'incremental-ranking-18300-tests.json' 'artifacts/incremental-ranking-18300-tests.json'",
  1
)

$required = @(
  "Run-Python '.github/scripts/fix_scorers_in_scope.py'",
  "Run-Python '.github/scripts/optimize_rankings_in_scope.py'",
  "Run-Python '.github/scripts/test_scorers_in_scope.py'",
  "Run-Python '.github/scripts/finalize_rankings_18230.py'",
  "Run-Python '.github/scripts/stabilize_rankings_18230.py'",
  "Run-Python '.github/scripts/fix_incremental_club_ranking.py'",
  "Run-Python '.github/scripts/stabilize_incremental_ranking_18300.py'",
  "Run-Python '.github/scripts/test_rankings_18230.py'",
  "Run-Python '.github/scripts/test_incremental_ranking_18300.py'",
  "Copy-Item 'scorers-in-scope-tests.json' 'artifacts/scorers-in-scope-tests.json'",
  "Copy-Item 'rankings-18230-tests.json' 'artifacts/rankings-18230-tests.json'",
  "Copy-Item 'incremental-ranking-18300-tests.json' 'artifacts/incremental-ranking-18300-tests.json'"
)
foreach ($marker in $required) {
  if (-not $source.Contains($marker)) { throw "Pipeline incremental incompleto: $marker" }
}
foreach ($forbidden in @(
  "Run-Python '.github/scripts/fix_scorers_navigation.py'",
  "Run-Python '.github/scripts/fix_scorers_live_runtime.py'",
  "Run-Python '.github/scripts/fix_scorers_root.py'",
  "Run-Python '.github/scripts/promote_scorers_page_factory.py'",
  "Run-Python '.github/scripts/fix_scorers_render_root.py'",
  "Run-Python '.github/scripts/fix_scorers_safe_state.py'",
  "Run-Python '.github/scripts/relocate_scorers_scripts.py'",
  "Run-Python '.github/scripts/bootstrap_rankings_api.py'",
  "Run-Python '.github/scripts/test_scorers_navigation.py'",
  "Run-Python '.github/scripts/test_scorers_live.py'",
  "Run-Python '.github/scripts/test_final_ui_integrity.py'",
  "Run-Python '.github/scripts/test_scorers_root.py'",
  "Run-Python '.github/scripts/test_scorers_render_root.py'",
  "Run-Python '.github/scripts/test_scorers_browser_runtime.py'"
)) {
  if ($source.Contains($forbidden)) { throw "Pipeline ainda executa camada antiga: $forbidden" }
}

python -m py_compile '.github/scripts/fix_scorers_in_scope.py' '.github/scripts/optimize_rankings_in_scope.py' '.github/scripts/test_scorers_in_scope.py' '.github/scripts/finalize_rankings_18230.py' '.github/scripts/stabilize_rankings_18230.py' '.github/scripts/test_rankings_18230.py' '.github/scripts/fix_incremental_club_ranking.py' '.github/scripts/stabilize_incremental_ranking_18300.py' '.github/scripts/test_incremental_ranking_18300.py'
if ($LASTEXITCODE -ne 0) { throw 'Falha na sintaxe dos scripts incrementais de rankings.' }

$tempScript = Join-Path $env:RUNNER_TEMP 'build_desktop_root_generated.ps1'
Set-Content $tempScript $source -Encoding utf8
Write-Host 'Executando pipeline original com Artilheiros compacto e Ranking de Clubes persistente, incremental e sem reconstrucao sazonal.'
& $tempScript
if ($LASTEXITCODE -ne 0) { throw 'Falha no pipeline incremental do desktop.' }
