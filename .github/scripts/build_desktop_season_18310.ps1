$ErrorActionPreference = 'Stop'

# Reuse the entire validated 18.301 build pipeline. No binary/source is fetched
# from untrusted pull requests and no existing distribution branch is replaced.
$rootPath = Join-Path $PSScriptRoot 'build_desktop_root.ps1'
$text = Get-Content $rootPath -Raw
$extra = @'
$syncAnchor = "Run-Python '.github/scripts/stabilize_incremental_ranking_18300.py'"
if (-not $source.Contains($syncAnchor)) { throw 'Ancora 18.301 ausente.' }
$syncSteps = @"
Run-Python '.github/scripts/stabilize_incremental_ranking_18300.py'
Run-Python '.github/scripts/optimize_season_sync_18310.py'
Run-Python '.github/scripts/test_season_sync_18310.py'
Run-Python '.github/scripts/test_history_incremental_18310.py'
"@.Trim()
$source = $source.Replace($syncAnchor, $syncSteps)
$reportAnchor = "Copy-Item 'architecture-validation.json' 'artifacts/architecture-validation.json'"
if (-not $source.Contains($reportAnchor)) { throw 'Ancora de relatorios ausente.' }
$reportSteps = @"
Copy-Item 'architecture-validation.json' 'artifacts/architecture-validation.json'
  Copy-Item 'season-sync-18310-install.json' 'artifacts/season-sync-18310-install.json'
  Copy-Item 'season-sync-18310-tests.json' 'artifacts/season-sync-18310-tests.json'
  Copy-Item 'history-incremental-18310-tests.json' 'artifacts/history-incremental-18310-tests.json'
"@.Trim()
$source = $source.Replace($reportAnchor, $reportSteps)
if (-not $source.Contains("Run-Python '.github/scripts/optimize_season_sync_18310.py'")) { throw 'Otimizacao de ferias ausente.' }
'@
$marker = '$tempScript = Join-Path $env:RUNNER_TEMP'
if (($text.Split($marker).Length - 1) -ne 1) { throw 'Pipeline original mudou; revisar integracao.' }
$text = $text.Replace($marker, $extra + "`n" + $marker)
$generated = Join-Path $PSScriptRoot 'build_desktop_season_18310_generated.ps1'
Set-Content $generated $text -Encoding utf8
& $generated
if ($LASTEXITCODE -ne 0) { throw 'Falha no build 18.310.' }
