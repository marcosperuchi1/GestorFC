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
Run-Python '.github/scripts/clean_rankings_18320.py'
Run-Python '.github/scripts/test_rankings_clean_18320.py'
Run-Python '.github/scripts/fix_rankings_ui_18321.py'
Run-Python '.github/scripts/test_rankings_ui_18321.py'
Run-Python '.github/scripts/feature_champions_retirement_18322.py'
Run-Python '.github/scripts/test_champions_retirement_18322.py'
Run-Python '.github/scripts/optimize_unemployed_turbo_18327.py'
Run-Python '.github/scripts/test_unemployed_turbo_18327.py'
Run-Python '.github/scripts/fix_device_sessions_18329.py'
Run-Python '.github/scripts/test_device_sessions_18329.py'
Run-Python '.github/scripts/optimize_scout_18331.py'
Run-Python '.github/scripts/test_scout_18331.py'
Run-Python '.github/scripts/fix_unemployed_resume_18334.py'
Run-Python '.github/scripts/test_unemployed_resume_18334.py'
Run-Python '.github/scripts/optimize_long_career_saves_18338.py'
Run-Python '.github/scripts/test_long_career_saves_18338.py'
Run-Python '.github/scripts/optimize_season_saves_18343.py'
Run-Python '.github/scripts/test_season_saves_18343.py'
Run-Python '.github/scripts/fix_player_career_timeline_18339.py'
Run-Python '.github/scripts/test_player_career_timeline_18339.py'
Run-Python '.github/scripts/enable_desktop_updater_18339.py'
Run-Python '.github/scripts/test_desktop_updater_18339.py'
Run-Python '.github/scripts/fix_scorers_submit_18340.py'
Run-Python '.github/scripts/test_scorers_submit_18340.py'
Run-Python '.github/scripts/set_desktop_version_18340.py'
Run-Python '.github/scripts/set_desktop_version_18341.py'
Run-Python '.github/scripts/fix_welcome_national_preview_18342.py'
Run-Python '.github/scripts/test_welcome_national_preview_18342.py'
Run-Python '.github/scripts/set_desktop_version_18342.py'
Run-Python '.github/scripts/set_desktop_version_18343.py'
Run-Python '.github/scripts/fix_career_isolation_18344.py'
Run-Python '.github/scripts/test_career_isolation_18344.py'
Run-Python '.github/scripts/set_desktop_version_18344.py'
Run-Python '.github/scripts/fix_seriec_champion_18345.py'
Run-Python '.github/scripts/test_seriec_champion_18345.py'
Run-Python '.github/scripts/set_desktop_version_18345.py'
Run-Python '.github/scripts/fix_retirement_vacation_18346.py'
Run-Python '.github/scripts/test_retirement_vacation_18346.py'
Run-Python '.github/scripts/set_desktop_version_18346.py'
Run-Python '.github/scripts/feature_calendar_list_18347.py'
Run-Python '.github/scripts/test_calendar_list_18347.py'
Run-Python '.github/scripts/set_desktop_version_18347.py'
Run-Python '.github/scripts/set_desktop_version_18348.py'
Run-Python '.github/scripts/fix_calendar_nav_version_18348.py'
Run-Python '.github/scripts/test_calendar_nav_version_18348.py'
Run-Python '.github/scripts/set_desktop_version_18349.py'
Run-Python '.github/scripts/optimize_incremental_saves_calendar_18349.py'
Run-Python '.github/scripts/test_incremental_saves_calendar_18349.py'
Run-Python '.github/scripts/test_season_sync_18310.py'
Run-Python '.github/scripts/test_new_season_vacation_18311.py'
Run-Python '.github/scripts/test_history_incremental_18310.py'
"@.Trim()
$source = $source.Replace($syncAnchor, $syncSteps)
$initialAnchor = "Run-Python '.github/scripts/externalize_player_base.py'"
if (-not $source.Contains($initialAnchor)) { throw 'Base inicial 18.340: etapa de externalizacao ausente.' }
$source = $source.Replace($initialAnchor, "$initialAnchor`nRun-Python '.github/scripts/fix_initial_nationalities_18340.py'")
$initialTestAnchor = "Run-Python '.github/scripts/test_initial_database.py'"
if (-not $source.Contains($initialTestAnchor)) { throw 'Base inicial 18.340: teste do consolidador ausente.' }
$source = $source.Replace($initialTestAnchor, "$initialTestAnchor`nRun-Python '.github/scripts/test_initial_nationalities_18340.py'")
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
  Copy-Item 'ranking-clean-18320-install.json' 'artifacts/ranking-clean-18320-install.json'
  Copy-Item 'ranking-clean-18320-tests.json' 'artifacts/ranking-clean-18320-tests.json'
  Copy-Item 'ranking-ui-18321-install.json' 'artifacts/ranking-ui-18321-install.json'
  Copy-Item 'ranking-ui-18321-tests.json' 'artifacts/ranking-ui-18321-tests.json'
  Copy-Item 'champions-retirement-18322-install.json' 'artifacts/champions-retirement-18322-install.json'
  Copy-Item 'champions-retirement-18322-tests.json' 'artifacts/champions-retirement-18322-tests.json'
  Copy-Item 'unemployed-turbo-18327-install.json' 'artifacts/unemployed-turbo-18327-install.json'
  Copy-Item 'unemployed-turbo-18327-tests.json' 'artifacts/unemployed-turbo-18327-tests.json'
  Copy-Item 'device-sessions-18329-install.json' 'artifacts/device-sessions-18329-install.json'
  Copy-Item 'device-sessions-18329-tests.json' 'artifacts/device-sessions-18329-tests.json'
  Copy-Item 'history-incremental-18310-tests.json' 'artifacts/history-incremental-18310-tests.json'
  Copy-Item 'scout-18331-install.json' 'artifacts/scout-18331-install.json'
  Copy-Item 'scout-18331-tests.json' 'artifacts/scout-18331-tests.json'
  Copy-Item 'unemployed-resume-18334-install.json' 'artifacts/unemployed-resume-18334-install.json'
  Copy-Item 'unemployed-resume-18334-tests.json' 'artifacts/unemployed-resume-18334-tests.json'
  Copy-Item 'long-career-saves-18338-install.json' 'artifacts/long-career-saves-18338-install.json'
  Copy-Item 'long-career-saves-18338-tests.json' 'artifacts/long-career-saves-18338-tests.json'
  Copy-Item 'season-save-18343-install.json' 'artifacts/season-save-18343-install.json'
  Copy-Item 'season-save-18343-tests.json' 'artifacts/season-save-18343-tests.json'
  Copy-Item 'desktop-updater-18339-install.json' 'artifacts/desktop-updater-18339-install.json'
  Copy-Item 'career-timeline-18339-install.json' 'artifacts/career-timeline-18339-install.json'
  Copy-Item 'career-timeline-18339-tests.json' 'artifacts/career-timeline-18339-tests.json'
   Copy-Item 'initial-nationalities-18340-install.json' 'artifacts/initial-nationalities-18340-install.json'
   Copy-Item 'initial-nationalities-18340-tests.json' 'artifacts/initial-nationalities-18340-tests.json'
   Copy-Item 'scorers-submit-18340-install.json' 'artifacts/scorers-submit-18340-install.json'
   Copy-Item 'scorers-submit-18340-tests.json' 'artifacts/scorers-submit-18340-tests.json'
   Copy-Item 'desktop-version-18340-install.json' 'artifacts/desktop-version-18340-install.json'
   Copy-Item 'desktop-version-18341-install.json' 'artifacts/desktop-version-18341-install.json'
   Copy-Item 'welcome-national-preview-18342-install.json' 'artifacts/welcome-national-preview-18342-install.json'
   Copy-Item 'welcome-national-preview-18342-tests.json' 'artifacts/welcome-national-preview-18342-tests.json'
   Copy-Item 'desktop-version-18342-install.json' 'artifacts/desktop-version-18342-install.json'
  Copy-Item 'desktop-version-18343-install.json' 'artifacts/desktop-version-18343-install.json'
  Copy-Item 'career-isolation-18344-install.json' 'artifacts/career-isolation-18344-install.json'
  Copy-Item 'career-isolation-18344-tests.json' 'artifacts/career-isolation-18344-tests.json'
  Copy-Item 'desktop-version-18344-install.json' 'artifacts/desktop-version-18344-install.json'
  Copy-Item 'serie-c-champion-18345-install.json' 'artifacts/serie-c-champion-18345-install.json'
  Copy-Item 'serie-c-champion-18345-tests.json' 'artifacts/serie-c-champion-18345-tests.json'
  Copy-Item 'desktop-version-18345-install.json' 'artifacts/desktop-version-18345-install.json'
  Copy-Item 'retirement-vacation-18346-install.json' 'artifacts/retirement-vacation-18346-install.json'
  Copy-Item 'retirement-vacation-18346-tests.json' 'artifacts/retirement-vacation-18346-tests.json'
  Copy-Item 'desktop-version-18346-install.json' 'artifacts/desktop-version-18346-install.json'
  Copy-Item 'calendar-list-18347-install.json' 'artifacts/calendar-list-18347-install.json'
  Copy-Item 'calendar-list-18347-tests.json' 'artifacts/calendar-list-18347-tests.json'
  Copy-Item 'desktop-version-18347-install.json' 'artifacts/desktop-version-18347-install.json'
  Copy-Item 'desktop-version-18348-install.json' 'artifacts/desktop-version-18348-install.json'
  Copy-Item 'calendar-nav-version-18348-install.json' 'artifacts/calendar-nav-version-18348-install.json'
  Copy-Item 'calendar-nav-version-18348-tests.json' 'artifacts/calendar-nav-version-18348-tests.json'
  Copy-Item 'desktop-version-18349-install.json' 'artifacts/desktop-version-18349-install.json'
  Copy-Item 'incremental-saves-calendar-18349-install.json' 'artifacts/incremental-saves-calendar-18349-install.json'
  Copy-Item 'incremental-saves-calendar-18349-tests.json' 'artifacts/incremental-saves-calendar-18349-tests.json'
"@.Trim()
$source = $source.Replace($reportAnchor, $reportSteps)
if (-not $source.Contains("Run-Python '.github/scripts/optimize_season_sync_18310.py'")) { throw 'Otimizacao de ferias ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/fix_new_season_vacation_18311.py'")) { throw 'Hotfix 18.311 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/optimize_rankings_finals_18312.py'")) { throw 'Arquitetura 18.312 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/optimize_career_runtime_18313.py'")) { throw 'Runtime 18.313 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/fix_rank_details_18314.py'")) { throw 'Hotfix 18.314 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/fix_rank_titles_sparse_18315.py'")) { throw 'Arquitetura 18.315 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/fix_rank_rollover_18316.py'")) { throw 'Handoff 18.316 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/clean_rankings_18320.py'")) { throw 'Motor limpo 18.320 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/fix_unemployed_resume_18334.py'")) { throw 'Recuperacao 18.334 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/test_unemployed_resume_18334.py'")) { throw 'Teste 18.334 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/optimize_long_career_saves_18338.py'")) { throw 'Otimizacao de saves 18.338 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/test_long_career_saves_18338.py'")) { throw 'Regressao de integridade de saves 18.338 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/enable_desktop_updater_18339.py'")) { throw 'Atualizador assinado 18.339 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/fix_rank_titles_18317.py'")) { throw 'Motor de titulos 18.317 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/fix_initial_nationalities_18340.py'")) { throw 'Correcao base inicial 18.340 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/test_initial_nationalities_18340.py'")) { throw 'Teste da base 18.340 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/fix_scorers_submit_18340.py'")) { throw 'Busca explicita de Artilheiros 18.340 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/set_desktop_version_18341.py'")) { throw 'Reparo de assinatura Windows 18.341 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/fix_welcome_national_preview_18342.py'")) { throw 'Hotfix de preview da Selecao 18.342 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/test_welcome_national_preview_18342.py'")) { throw 'Regressao de preview da Selecao 18.342 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/set_desktop_version_18342.py'")) { throw 'Versao Windows 18.342 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/optimize_season_saves_18343.py'")) { throw 'Otimização incremental de históricos da 18.343 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/test_season_saves_18343.py'")) { throw 'Teste de integridade de saves da 18.343 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/set_desktop_version_18343.py'")) { throw 'Versao Windows 18.343 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/fix_career_isolation_18344.py'")) { throw 'Hotfix 18.344 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/test_career_isolation_18344.py'")) { throw 'Regressao de isolamento 18.344 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/fix_seriec_champion_18345.py'")) { throw 'Campeao da Serie C 18.345 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/test_seriec_champion_18345.py'")) { throw 'Teste de final da Serie C 18.345 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/set_desktop_version_18345.py'")) { throw 'Versao assinada 18.345 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/fix_retirement_vacation_18346.py'")) { throw 'IA de aposentadorias 18.346 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/test_retirement_vacation_18346.py'")) { throw 'Teste de aposentadoria 18.346 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/set_desktop_version_18346.py'")) { throw 'Versao assinada 18.346 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/feature_calendar_list_18347.py'")) { throw 'Calendario em lista 18.347 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/test_calendar_list_18347.py'")) { throw 'Teste de calendario 18.347 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/set_desktop_version_18347.py'")) { throw 'Versao assinada 18.347 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/set_desktop_version_18348.py'")) { throw 'Versao assinada 18.348 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/fix_calendar_nav_version_18348.py'")) { throw 'Menu calendario e versao visual 18.348 ausentes.' }
if (-not $source.Contains("Run-Python '.github/scripts/test_calendar_nav_version_18348.py'")) { throw 'Teste da navegacao real 18.348 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/set_desktop_version_18349.py'")) { throw 'Versao assinada 18.349 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/optimize_incremental_saves_calendar_18349.py'")) { throw 'Salvamento incremental seguro e calendario rolavel 18.349 ausentes.' }
if (-not $source.Contains("Run-Python '.github/scripts/test_incremental_saves_calendar_18349.py'")) { throw 'Teste de integridade de salvamento 18.349 ausente.' }
'@
$marker = '$tempScript = Join-Path $env:RUNNER_TEMP'
if ([regex]::Matches($text, [regex]::Escape($marker)).Count -ne 1) { throw 'Pipeline original mudou; revisar integracao.' }
$text = $text.Replace($marker, $extra + "`n" + $marker)
$generated = Join-Path $PSScriptRoot 'build_desktop_season_18310_generated.ps1'
Set-Content $generated $text -Encoding utf8
& $generated
if ($LASTEXITCODE -ne 0) { throw 'Falha no build 18.310.' }
