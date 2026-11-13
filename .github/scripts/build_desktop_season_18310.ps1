$ErrorActionPreference = 'Stop'

# Reuse the validated 18.301 build pipeline without replacing any release branch.
$rootPath = Join-Path $PSScriptRoot 'build_desktop_root.ps1'
$text = Get-Content $rootPath -Raw
$extra = @'
$syncAnchor = "Run-Python '.github/scripts/stabilize_incremental_ranking_18300.py'"
if (-not $source.Contains($syncAnchor)) { throw 'Ancora 18.301 ausente.' }
$syncSteps = @"
Run-Python '.github/scripts/stabilize_incremental_ranking_18300.py'
Run-Python '.github/scripts/optimize_season_sync_18310.py'
Run-Python '.github/scripts/fix_new_season_vacation_18311.py'
Run-Python '.github/scripts/optimize_rankings_finals_18312.py'
Run-Python '.github/scripts/test_rankings_finals_18312.py'
Run-Python '.github/scripts/optimize_career_runtime_18313.py'
Run-Python '.github/scripts/test_runtime_18313.py'
Run-Python '.github/scripts/fix_rank_details_18314.py'
Run-Python '.github/scripts/test_rank_details_18314.py'
Run-Python '.github/scripts/fix_rank_titles_sparse_18315.py'
Run-Python '.github/scripts/test_rank_titles_sparse_18315.py'
Run-Python '.github/scripts/fix_rank_rollover_18316.py'
Run-Python '.github/scripts/test_rank_rollover_18316.py'
Run-Python '.github/scripts/fix_rank_titles_18317.py'
Run-Python '.github/scripts/test_rank_titles_18317.py'
Run-Python '.github/scripts/rebuild_rankings_18318.py'
Run-Python '.github/scripts/test_rankings_18318.py'
Run-Python '.github/scripts/clean_rankings_18319.py'
Run-Python '.github/scripts/test_rankings_clean_18319.py'
Run-Python '.github/scripts/test_season_sync_18310.py'
Run-Python '.github/scripts/test_new_season_vacation_18311.py'
Run-Python '.github/scripts/test_history_incremental_18310.py'
"@.Trim()
$source = $source.Replace($syncAnchor, $syncSteps)
$reportAnchor = "Copy-Item 'architecture-validation.json' 'artifacts/architecture-validation.json'"
if (-not $source.Contains($reportAnchor)) { throw 'Ancora de relatorios ausente.' }
$reportSteps = @"
Copy-Item 'architecture-validation.json' 'artifacts/architecture-validation.json'
  Copy-Item 'season-sync-18310-install.json' 'artifacts/season-sync-18310-install.json'
  Copy-Item 'season-sync-18310-tests.json' 'artifacts/season-sync-18310-tests.json'
  Copy-Item 'new-season-vacation-18311-install.json' 'artifacts/new-season-vacation-18311-install.json'
  Copy-Item 'new-season-vacation-18311-tests.json' 'artifacts/new-season-vacation-18311-tests.json'
  Copy-Item 'rankings-finals-18312-install.json' 'artifacts/rankings-finals-18312-install.json'
  Copy-Item 'rankings-finals-18312-tests.json' 'artifacts/rankings-finals-18312-tests.json'
  Copy-Item 'runtime-18313-install.json' 'artifacts/runtime-18313-install.json'
  Copy-Item 'runtime-18313-tests.json' 'artifacts/runtime-18313-tests.json'
  Copy-Item 'ranking-cache-18314-install.json' 'artifacts/ranking-cache-18314-install.json'
  Copy-Item 'ranking-cache-18314-tests.json' 'artifacts/ranking-cache-18314-tests.json'
  Copy-Item 'sparse-titles-18315-install.json' 'artifacts/sparse-titles-18315-install.json'
  Copy-Item 'sparse-titles-18315-tests.json' 'artifacts/sparse-titles-18315-tests.json'
  Copy-Item 'rank-rollover-18316-install.json' 'artifacts/rank-rollover-18316-install.json'
  Copy-Item 'rank-rollover-18316-tests.json' 'artifacts/rank-rollover-18316-tests.json'
  Copy-Item 'title-engine-18317-install.json' 'artifacts/title-engine-18317-install.json'
  Copy-Item 'title-engine-18317-tests.json' 'artifacts/title-engine-18317-tests.json'
  Copy-Item 'ranking-rebuild-18318-install.json' 'artifacts/ranking-rebuild-18318-install.json'
  Copy-Item 'ranking-rebuild-18318-tests.json' 'artifacts/ranking-rebuild-18318-tests.json'
  Copy-Item 'ranking-clean-18319-install.json' 'artifacts/ranking-clean-18319-install.json'
  Copy-Item 'ranking-clean-18319-tests.json' 'artifacts/ranking-clean-18319-tests.json'
  Copy-Item 'history-incremental-18310-tests.json' 'artifacts/history-incremental-18310-tests.json'
"@.Trim()
$source = $source.Replace($reportAnchor, $reportSteps)
if (-not $source.Contains("Run-Python '.github/scripts/optimize_season_sync_18310.py'")) { throw 'Otimizacao de ferias ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/fix_new_season_vacation_18311.py'")) { throw 'Hotfix 18.311 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/optimize_rankings_finals_18312.py'")) { throw 'Arquitetura 18.312 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/optimize_career_runtime_18313.py'")) { throw 'Runtime 18.313 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/fix_rank_details_18314.py'")) { throw 'Hotfix 18.314 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/fix_rank_titles_sparse_18315.py'")) { throw 'Arquitetura 18.315 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/fix_rank_rollover_18316.py'")) { throw 'Handoff 18.316 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/clean_rankings_18319.py'")) { throw 'Motor limpo 18.319 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/fix_rank_titles_18317.py'")) { throw 'Motor de titulos 18.317 ausente.' }
'@
$marker = '$tempScript = Join-Path $env:RUNNER_TEMP'
if ([regex]::Matches($text, [regex]::Escape($marker)).Count -ne 1) { throw 'Pipeline original mudou; revisar integracao.' }
$text = $text.Replace($marker, $extra + "`n" + $marker)
$generated = Join-Path $PSScriptRoot 'build_desktop_season_18310_generated.ps1'
Set-Content $generated $text -Encoding utf8
& $generated
if ($LASTEXITCODE -ne 0) { throw 'Falha no build 18.310.' }
