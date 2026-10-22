$ErrorActionPreference = 'Stop'

$basePath = Join-Path $PSScriptRoot 'build_desktop_latest.ps1'
$source = Get-Content $basePath -Raw

# A compilacao continua usando exatamente a mesma cadeia de base externa,
# saves compactos, memoria, SQLite e carregamento direto. Apenas substitui as
# camadas de UI de Artilheiros por uma implementacao canonica, protege o ponto
# raiz em que o HTML e escrito, torna o estado seguro e executa os scripts no body.
$oldRuntime = "Run-Python '.github/scripts/finalize_prebuilt_boot.py'\r?\nRun-Python '.github/scripts/fix_scorers_navigation.py'\r?\nRun-Python '.github/scripts/fix_scorers_live_runtime.py'\r?\nRun-Python '.github/scripts/diagnose_boot_performance.py'"
$newRuntime = @"
Run-Python '.github/scripts/finalize_prebuilt_boot.py'
Run-Python '.github/scripts/fix_scorers_root.py'
Run-Python '.github/scripts/promote_scorers_page_factory.py'
Run-Python '.github/scripts/fix_scorers_render_root.py'
Run-Python '.github/scripts/fix_scorers_safe_state.py'
Run-Python '.github/scripts/relocate_scorers_scripts.py'
Run-Python '.github/scripts/annotate_scorers_root.py'
Run-Python '.github/scripts/diagnose_boot_performance.py'
"@.Trim()
$source = [regex]::Replace($source, $oldRuntime, $newRuntime, 1)

$source = [regex]::Replace($source, "(?m)^Run-Python '\.github/scripts/test_final_ui_integrity\.py'\r?\n", '')
$source = [regex]::Replace($source, "(?m)^Run-Python '\.github/scripts/test_scorers_navigation\.py'\r?\n", '')
$source = [regex]::Replace($source, "(?m)^Run-Python '\.github/scripts/test_scorers_live\.py'\r?\n", '')
$source = [regex]::Replace(
  $source,
  "Run-Python '\.github/scripts/test_runtime_boot\.py'",
  "Run-Python '.github/scripts/test_runtime_boot.py'`nRun-Python '.github/scripts/test_scorers_root.py'`nRun-Python '.github/scripts/test_scorers_render_root.py'`nRun-Python '.github/scripts/test_scorers_browser_runtime.py'",
  1
)

$source = [regex]::Replace($source, "(?m)^\s*Copy-Item 'scorers-navigation-tests\.json'.*\r?\n", '')
$source = [regex]::Replace($source, "(?m)^\s*Copy-Item 'scorers-live-tests\.json'.*\r?\n", '')
$source = [regex]::Replace(
  $source,
  "(?m)^(\s*)Copy-Item 'mls-vacation-tests\.json' 'artifacts/mls-vacation-tests\.json'\r?$",
  "`$1Copy-Item 'mls-vacation-tests.json' 'artifacts/mls-vacation-tests.json'`n`$1Copy-Item 'scorers-root-tests.json' 'artifacts/scorers-root-tests.json'`n`$1Copy-Item 'scorers-render-root-tests.json' 'artifacts/scorers-render-root-tests.json'`n`$1Copy-Item 'scorers-browser-runtime-tests.json' 'artifacts/scorers-browser-runtime-tests.json'",
  1
)

$required = @(
  "Run-Python '.github/scripts/fix_scorers_root.py'",
  "Run-Python '.github/scripts/promote_scorers_page_factory.py'",
  "Run-Python '.github/scripts/fix_scorers_render_root.py'",
  "Run-Python '.github/scripts/fix_scorers_safe_state.py'",
  "Run-Python '.github/scripts/relocate_scorers_scripts.py'",
  "Run-Python '.github/scripts/test_scorers_root.py'",
  "Run-Python '.github/scripts/test_scorers_render_root.py'",
  "Run-Python '.github/scripts/test_scorers_browser_runtime.py'",
  "Copy-Item 'scorers-root-tests.json' 'artifacts/scorers-root-tests.json'",
  "Copy-Item 'scorers-render-root-tests.json' 'artifacts/scorers-render-root-tests.json'",
  "Copy-Item 'scorers-browser-runtime-tests.json' 'artifacts/scorers-browser-runtime-tests.json'"
)
foreach ($marker in $required) {
  if (-not $source.Contains($marker)) { throw "Pipeline raiz incompleto: $marker" }
}
foreach ($forbidden in @(
  "Run-Python '.github/scripts/fix_scorers_navigation.py'",
  "Run-Python '.github/scripts/fix_scorers_live_runtime.py'",
  "Run-Python '.github/scripts/test_scorers_navigation.py'",
  "Run-Python '.github/scripts/test_scorers_live.py'",
  "Run-Python '.github/scripts/test_final_ui_integrity.py'"
)) {
  if ($source.Contains($forbidden)) { throw "Pipeline ainda executa camada antiga: $forbidden" }
}

python -m py_compile '.github/scripts/fix_scorers_root.py' '.github/scripts/promote_scorers_page_factory.py' '.github/scripts/fix_scorers_render_root.py' '.github/scripts/fix_scorers_safe_state.py' '.github/scripts/relocate_scorers_scripts.py' '.github/scripts/annotate_scorers_root.py' '.github/scripts/test_scorers_root.py' '.github/scripts/test_scorers_render_root.py' '.github/scripts/test_scorers_browser_runtime.py'
if ($LASTEXITCODE -ne 0) { throw 'Falha na sintaxe dos scripts raiz de Artilheiros.' }

$tempScript = Join-Path $env:RUNNER_TEMP 'build_desktop_root_generated.ps1'
Set-Content $tempScript $source -Encoding utf8
Write-Host 'Executando pipeline original com Artilheiros dentro do documento, estado seguro e validacao no Chrome real.'
& $tempScript
if ($LASTEXITCODE -ne 0) { throw 'Falha no pipeline raiz do desktop.' }
