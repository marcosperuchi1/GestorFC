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
Run-Python '.github/scripts/set_desktop_version_18350.py'
Run-Python '.github/scripts/fix_calendar_match_retirement_18350.py'
Run-Python '.github/scripts/test_calendar_match_retirement_18350.py'
Run-Python '.github/scripts/set_desktop_version_18351.py'
Run-Python '.github/scripts/fix_seriec_phases_history_18351.py'
Run-Python '.github/scripts/test_seriec_phases_history_18351.py'
Run-Python '.github/scripts/set_desktop_version_18352.py'
Run-Python '.github/scripts/optimize_oomsafe_saves_18352.py'
Run-Python '.github/scripts/test_oomsafe_saves_18352.py'
Run-Python '.github/scripts/set_desktop_version_18353.py'
Run-Python '.github/scripts/fix_seriec_full_history_18353.py'
Run-Python '.github/scripts/test_seriec_full_history_18353.py'
Run-Python '.github/scripts/set_desktop_version_18354.py'
Run-Python '.github/scripts/harden_native_save_mirror_18354.py'
Run-Python '.github/scripts/shard_remaining_archives_18354.py'
Run-Python '.github/scripts/test_native_save_mirror_18354.py'
Run-Python '.github/scripts/test_archive_root_shards_18354.py'
Run-Python '.github/scripts/set_desktop_version_18355.py'
Run-Python '.github/scripts/fix_job_saveexit_18355.py'
Run-Python '.github/scripts/test_job_saveexit_18355.py'
Run-Python '.github/scripts/set_desktop_version_18356.py'
Run-Python '.github/scripts/fix_jobwait_18356.py'
Run-Python '.github/scripts/test_jobwait_18356.py'
Run-Python '.github/scripts/set_desktop_version_18357.py'
Run-Python '.github/scripts/fix_dismissal_handoff_18357.py'
Run-Python '.github/scripts/test_dismissal_handoff_18357.py'
Run-Python '.github/scripts/set_desktop_version_18358.py'
Run-Python '.github/scripts/fix_dismissal_button_18358.py'
Run-Python '.github/scripts/test_dismissal_button_18358.py'
Run-Python '.github/scripts/set_desktop_version_18359.py'
Run-Python '.github/scripts/fix_dismissal_control_18359.py'
Run-Python '.github/scripts/test_dismissal_control_18359.py'
Run-Python '.github/scripts/set_desktop_version_18360.py'
Run-Python '.github/scripts/optimize_vacation_finalize_18360.py'
Run-Python '.github/scripts/test_vacation_finalize_18360.py'
Run-Python '.github/scripts/set_desktop_version_18361.py'
Run-Python '.github/scripts/fix_fast_updater_18361.py'
Run-Python '.github/scripts/test_fast_updater_18361.py'
Run-Python '.github/scripts/set_desktop_version_18362.py'
Run-Python '.github/scripts/fix_core_transitions_18362.py'
Run-Python '.github/scripts/test_core_transitions_18362.py'
Run-Python '.github/scripts/set_desktop_version_18363.py'
Run-Python '.github/scripts/fix_jobwait_state_18363.py'
Run-Python '.github/scripts/test_jobwait_state_18363.py'
Run-Python '.github/scripts/set_desktop_version_18364.py'
Run-Python '.github/scripts/fix_vacation_job_handoff_18364.py'
Run-Python '.github/scripts/test_vacation_job_handoff_18364.py'
Run-Python '.github/scripts/set_desktop_version_18365.py'
Run-Python '.github/scripts/fix_dismissal_source_18365.py'
Run-Python '.github/scripts/test_dismissal_source_18365.py'
Run-Python '.github/scripts/set_desktop_version_18366.py'
Run-Python '.github/scripts/fix_unemployed_scope_18366.py'
Run-Python '.github/scripts/test_unemployed_scope_18366.py'
Run-Python '.github/scripts/set_desktop_version_18367.py'
Run-Python '.github/scripts/fix_jobwait_real_progress_18367.py'
Run-Python '.github/scripts/test_jobwait_real_progress_18367.py'
Run-Python '.github/scripts/set_desktop_version_18368.py'
Run-Python '.github/scripts/fix_unemployed_real_worker_18368.py'
Run-Python '.github/scripts/test_unemployed_real_worker_18368.py'
Run-Python '.github/scripts/test_unemployed_real_browser_18368.py'
Run-Python '.github/scripts/set_desktop_version_18369.py'
Run-Python '.github/scripts/fix_vacation_resume_18369.py'
Run-Python '.github/scripts/test_vacation_resume_18369.py'
Run-Python '.github/scripts/test_vacation_queue_18369.py'
Run-Python '.github/scripts/test_vacation_lifecycle_scope_18369.py'
# Recheck unemployed real-Worker advancement on the final vacation queue implementation.
Run-Python '.github/scripts/test_unemployed_real_browser_18368.py'
Run-Python '.github/scripts/test_vacation_resume_browser_18369.py'
Run-Python '.github/scripts/test_vacation_dismissal_browser_18369.py'
Run-Python '.github/scripts/set_desktop_version_18370.py'
Run-Python '.github/scripts/fix_bounded_jobwait_18370.py'
Run-Python '.github/scripts/test_bounded_jobwait_18370.py'
Run-Python '.github/scripts/test_jobwait_memory_browser_18370.py'
Run-Python '.github/scripts/set_desktop_version_18371.py'
Run-Python '.github/scripts/fix_contract_preferences_18371.py'
Run-Python '.github/scripts/fix_repeated_dismissal_18371.py'
Run-Python '.github/scripts/test_contract_preferences_18371.py'
Run-Python '.github/scripts/test_repeated_dismissal_18371.py'
Run-Python '.github/scripts/test_career_transitions_browser_18371.py'
Run-Python '.github/scripts/set_desktop_version_18372.py'
Run-Python '.github/scripts/fix_native_confirmations_18372.py'
Run-Python '.github/scripts/fix_career_promotion_offers_18372.py'
Run-Python '.github/scripts/test_native_confirmations_18372.py'
Run-Python '.github/scripts/test_career_promotion_offers_18372.py'
Run-Python '.github/scripts/test_contract_preferences_18371.py'
Run-Python '.github/scripts/test_repeated_dismissal_18371.py'
# Recheck employed vacation return on the final 18.372 lifecycle.
Run-Python '.github/scripts/test_vacation_resume_browser_18369.py'
Run-Python '.github/scripts/test_season_sync_18310.py'
Run-Python '.github/scripts/test_new_season_vacation_18311.py'
Run-Python '.github/scripts/test_history_incremental_18310.py'
# Apply the inherited ranking-scope repair before the source is finalized.
# Its legacy regression also invokes the patch; that later call must be a no-op.
Run-Python '.github/scripts/fix_incremental_competition_scope.py'
# 18.373 runs after the preserved baseline regression stage.
Run-Python '.github/scripts/set_desktop_version_18373.py'
Run-Python '.github/scripts/fix_vacation_checkpoint_18373.py'
Run-Python '.github/scripts/fix_save_memory_runtime_18373.py'
Run-Python '.github/scripts/fix_jobwait_memory_transfer_18373.py'
Run-Python '.github/scripts/fix_vacation_memory_boot_18373.py'
Run-Python '.github/scripts/fix_player_checkpoint_reuse_18373.py'
Run-Python '.github/scripts/finalize_long_career_memory_18373.py'
Run-Python '.github/scripts/set_desktop_version_18374.py'
Run-Python '.github/scripts/prepare_career_club_season_18374.py'
Run-Python '.github/scripts/test_vacation_checkpoint_18373.py'
Run-Python '.github/scripts/test_save_memory_runtime_18373.py'
Run-Python '.github/scripts/test_jobwait_memory_transfer_18373.py'
Run-Python '.github/scripts/test_vacation_memory_boot_18373.py'
Run-Python '.github/scripts/test_player_checkpoint_reuse_18373.py'
Run-Python '.github/scripts/test_promotion_confirmations_browser_18372.py'
Run-Python '.github/scripts/test_long_career_memory_browser_18373.py'
Run-Python '.github/scripts/test_season_job_offers_18374.py'
Run-Python '.github/scripts/test_club_management_18374.py'
Run-Python '.github/scripts/test_season_rollover_18374.py'
Run-Python '.github/scripts/test_season_job_offers_browser_18374.py'
Run-Python '.github/scripts/test_club_management_browser_18374.py'
Run-Python '.github/scripts/test_season_rollover_browser_18374.py'
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
  Copy-Item 'desktop-version-18350-install.json' 'artifacts/desktop-version-18350-install.json'
  Copy-Item 'calendar-retirement-18350-install.json' 'artifacts/calendar-retirement-18350-install.json'
  Copy-Item 'calendar-retirement-18350-tests.json' 'artifacts/calendar-retirement-18350-tests.json'
  Copy-Item 'desktop-version-18351-install.json' 'artifacts/desktop-version-18351-install.json'
  Copy-Item 'serie-c-phases-history-18351-install.json' 'artifacts/serie-c-phases-history-18351-install.json'
  Copy-Item 'serie-c-phases-history-18351-tests.json' 'artifacts/serie-c-phases-history-18351-tests.json'
  Copy-Item 'desktop-version-18352-install.json' 'artifacts/desktop-version-18352-install.json'
  Copy-Item 'oomsafe-save-18352-install.json' 'artifacts/oomsafe-save-18352-install.json'
  Copy-Item 'oomsafe-save-18352-tests.json' 'artifacts/oomsafe-save-18352-tests.json'
  Copy-Item 'desktop-version-18353-install.json' 'artifacts/desktop-version-18353-install.json'
  Copy-Item 'serie-c-full-history-18353-install.json' 'artifacts/serie-c-full-history-18353-install.json'
  Copy-Item 'serie-c-full-history-18353-tests.json' 'artifacts/serie-c-full-history-18353-tests.json'
  Copy-Item 'desktop-version-18354-install.json' 'artifacts/desktop-version-18354-install.json'
  Copy-Item 'native-save-mirror-18354-install.json' 'artifacts/native-save-mirror-18354-install.json'
  Copy-Item 'native-save-mirror-18354-tests.json' 'artifacts/native-save-mirror-18354-tests.json'
  Copy-Item 'archive-root-shards-18354-install.json' 'artifacts/archive-root-shards-18354-install.json'
  Copy-Item 'archive-root-shards-18354-tests.json' 'artifacts/archive-root-shards-18354-tests.json'
  Copy-Item 'desktop-version-18355-install.json' 'artifacts/desktop-version-18355-install.json'
  Copy-Item 'job-save-exit-18355-tests.json' 'artifacts/job-save-exit-18355-tests.json'
  Copy-Item 'desktop-version-18356-install.json' 'artifacts/desktop-version-18356-install.json'
  Copy-Item 'jobwait-season-18356-install.json' 'artifacts/jobwait-season-18356-install.json'
  Copy-Item 'jobwait-season-18356-tests.json' 'artifacts/jobwait-season-18356-tests.json'
  Copy-Item 'desktop-version-18357-install.json' 'artifacts/desktop-version-18357-install.json'
  Copy-Item 'dismissal-handoff-18357-install.json' 'artifacts/dismissal-handoff-18357-install.json'
  Copy-Item 'dismissal-handoff-18357-tests.json' 'artifacts/dismissal-handoff-18357-tests.json'
  Copy-Item 'desktop-version-18358-install.json' 'artifacts/desktop-version-18358-install.json'
  Copy-Item 'dismissal-button-18358-install.json' 'artifacts/dismissal-button-18358-install.json'
  Copy-Item 'dismissal-button-18358-tests.json' 'artifacts/dismissal-button-18358-tests.json'
  Copy-Item 'desktop-version-18359-install.json' 'artifacts/desktop-version-18359-install.json'
  Copy-Item 'dismissal-control-18359-install.json' 'artifacts/dismissal-control-18359-install.json'
  Copy-Item 'dismissal-control-18359-tests.json' 'artifacts/dismissal-control-18359-tests.json'
  Copy-Item 'desktop-version-18360-install.json' 'artifacts/desktop-version-18360-install.json'
  Copy-Item 'vacation-finalize-18360-install.json' 'artifacts/vacation-finalize-18360-install.json'
  Copy-Item 'vacation-finalize-18360-tests.json' 'artifacts/vacation-finalize-18360-tests.json'
  Copy-Item 'desktop-version-18361-install.json' 'artifacts/desktop-version-18361-install.json'
  Copy-Item 'fast-updater-18361-install.json' 'artifacts/fast-updater-18361-install.json'
  Copy-Item 'fast-updater-18361-tests.json' 'artifacts/fast-updater-18361-tests.json'
  Copy-Item 'desktop-version-18362-install.json' 'artifacts/desktop-version-18362-install.json'
  Copy-Item 'core-transitions-18362-install.json' 'artifacts/core-transitions-18362-install.json'
  Copy-Item 'core-transitions-18362-tests.json' 'artifacts/core-transitions-18362-tests.json'
  Copy-Item 'desktop-version-18363-install.json' 'artifacts/desktop-version-18363-install.json'
  Copy-Item 'jobwait-state-18363-install.json' 'artifacts/jobwait-state-18363-install.json'
  Copy-Item 'jobwait-state-18363-tests.json' 'artifacts/jobwait-state-18363-tests.json'
  Copy-Item 'desktop-version-18364-install.json' 'artifacts/desktop-version-18364-install.json'
  Copy-Item 'vacation-handoff-18364-install.json' 'artifacts/vacation-handoff-18364-install.json'
  Copy-Item 'vacation-handoff-18364-tests.json' 'artifacts/vacation-handoff-18364-tests.json'
  Copy-Item 'desktop-version-18365-install.json' 'artifacts/desktop-version-18365-install.json'
  Copy-Item 'dismissal-source-18365-install.json' 'artifacts/dismissal-source-18365-install.json'
  Copy-Item 'dismissal-source-18365-tests.json' 'artifacts/dismissal-source-18365-tests.json'
  Copy-Item 'desktop-version-18366-install.json' 'artifacts/desktop-version-18366-install.json'
  Copy-Item 'scope-repair-18366-install.json' 'artifacts/scope-repair-18366-install.json'
  Copy-Item 'scope-repair-18366-tests.json' 'artifacts/scope-repair-18366-tests.json'
   Copy-Item 'desktop-version-18367-install.json' 'artifacts/desktop-version-18367-install.json'
   Copy-Item 'job-progress-18367-install.json' 'artifacts/job-progress-18367-install.json'
   Copy-Item 'job-progress-18367-tests.json' 'artifacts/job-progress-18367-tests.json'
   Copy-Item 'desktop-version-18368-install.json' 'artifacts/desktop-version-18368-install.json'
   Copy-Item 'unemployed-worker-18368-install.json' 'artifacts/unemployed-worker-18368-install.json'
   Copy-Item 'unemployed-worker-18368-tests.json' 'artifacts/unemployed-worker-18368-tests.json'
   Copy-Item 'unemployed-browser-18368-tests.json' 'artifacts/unemployed-browser-18368-tests.json'
   Copy-Item 'desktop-version-18369-install.json' 'artifacts/desktop-version-18369-install.json'
   Copy-Item 'vacation-resume-18369-install.json' 'artifacts/vacation-resume-18369-install.json'
   Copy-Item 'vacation-resume-18369-tests.json' 'artifacts/vacation-resume-18369-tests.json'
   Copy-Item 'vacation-queue-18369-tests.json' 'artifacts/vacation-queue-18369-tests.json'
   Copy-Item 'root-gameplay-tests.json' 'artifacts/root-gameplay-tests.json'
   Copy-Item 'vacation-lifecycle-scope-18369-tests.json' 'artifacts/vacation-lifecycle-scope-18369-tests.json'
   Copy-Item 'vacation-resume-browser-18369-tests.json' 'artifacts/vacation-resume-browser-18369-tests.json'
   Copy-Item 'vacation-dismissal-browser-18369-tests.json' 'artifacts/vacation-dismissal-browser-18369-tests.json'
   Copy-Item 'desktop-version-18370-install.json' 'artifacts/desktop-version-18370-install.json'
   Copy-Item 'jobwait-memory-18370-install.json' 'artifacts/jobwait-memory-18370-install.json'
   Copy-Item 'jobwait-memory-18370-tests.json' 'artifacts/jobwait-memory-18370-tests.json'
   Copy-Item 'jobwait-memory-browser-18370-tests.json' 'artifacts/jobwait-memory-browser-18370-tests.json'
   Copy-Item 'desktop-version-18371-install.json' 'artifacts/desktop-version-18371-install.json'
   Copy-Item 'contract-preferences-18371-install.json' 'artifacts/contract-preferences-18371-install.json'
   Copy-Item 'contract-preferences-18371-tests.json' 'artifacts/contract-preferences-18371-tests.json'
   Copy-Item 'repeated-dismissal-18371-install.json' 'artifacts/repeated-dismissal-18371-install.json'
   Copy-Item 'repeated-dismissal-18371-tests.json' 'artifacts/repeated-dismissal-18371-tests.json'
   Copy-Item 'career-transitions-browser-18371-tests.json' 'artifacts/career-transitions-browser-18371-tests.json'
   Copy-Item 'desktop-version-18372-install.json' 'artifacts/desktop-version-18372-install.json'
   Copy-Item 'native-confirmations-18372-install.json' 'artifacts/native-confirmations-18372-install.json'
   Copy-Item 'native-confirmations-18372-tests.json' 'artifacts/native-confirmations-18372-tests.json'
   Copy-Item 'career-promotion-offers-18372-install.json' 'artifacts/career-promotion-offers-18372-install.json'
   Copy-Item 'career-promotion-offers-18372-tests.json' 'artifacts/career-promotion-offers-18372-tests.json'
   Copy-Item 'promotion-confirmations-browser-18372-tests.json' 'artifacts/promotion-confirmations-browser-18372-tests.json'
   Copy-Item 'desktop-version-18373-install.json' 'artifacts/desktop-version-18373-install.json'
   Copy-Item 'vacation-checkpoint-18373-install.json' 'artifacts/vacation-checkpoint-18373-install.json'
   Copy-Item 'vacation-checkpoint-18373-tests.json' 'artifacts/vacation-checkpoint-18373-tests.json'
   Copy-Item 'save-memory-runtime-18373-install.json' 'artifacts/save-memory-runtime-18373-install.json'
   Copy-Item 'save-memory-runtime-18373-tests.json' 'artifacts/save-memory-runtime-18373-tests.json'
   Copy-Item 'jobwait-memory-transfer-18373-install.json' 'artifacts/jobwait-memory-transfer-18373-install.json'
   Copy-Item 'jobwait-memory-transfer-18373-tests.json' 'artifacts/jobwait-memory-transfer-18373-tests.json'
   Copy-Item 'vacation-memory-boot-18373-install.json' 'artifacts/vacation-memory-boot-18373-install.json'
   Copy-Item 'vacation-memory-boot-18373-tests.json' 'artifacts/vacation-memory-boot-18373-tests.json'
   Copy-Item 'player-checkpoint-reuse-18373-install.json' 'artifacts/player-checkpoint-reuse-18373-install.json'
   Copy-Item 'player-checkpoint-reuse-18373-tests.json' 'artifacts/player-checkpoint-reuse-18373-tests.json'
   Copy-Item 'long-career-memory-18373-install.json' 'artifacts/long-career-memory-18373-install.json'
   Copy-Item 'long-career-memory-browser-18373-tests.json' 'artifacts/long-career-memory-browser-18373-tests.json'
   Copy-Item '*18374*.json' 'artifacts/'
"@.Trim()
$source = $source.Replace($reportAnchor, $reportSteps)
$preBuildAnchor = "Run-Python '.github/scripts/validate_desktop_architecture.py'"
if ([regex]::Matches($source, [regex]::Escape($preBuildAnchor)).Count -ne 1) { throw '18.374: final architecture validation anchor is missing or duplicated.' }
$source = $source.Replace($preBuildAnchor, "$preBuildAnchor`nRun-Python '.github/scripts/validate_career_club_season_release_18374.py'`nRun-Python '.github/scripts/fix_calendar_translations_18375.py'`nRun-Python '.github/scripts/fix_transfer_realism_18375.py'`nRun-Python '.github/scripts/improve_support_ui_18375.py'`nRun-Python '.github/scripts/set_desktop_version_18375.py'`nRun-Python '.github/scripts/validate_support_release_18375.py'
Run-Python '.github/scripts/fix_font_settings_18376.py'
Run-Python '.github/scripts/test_font_settings_18376.py'
Run-Python '.github/scripts/set_desktop_version_18376.py'
Run-Python '.github/scripts/validate_font_settings_release_18376.py'
Run-Python '.github/scripts/fix_legacy_scorers_18377.py'
Run-Python '.github/scripts/fix_window_capture_18377.py'
Run-Python '.github/scripts/test_historical_scorers_18377.py'
Run-Python '.github/scripts/set_desktop_version_18377.py'
Run-Python '.github/scripts/validate_history_window_release_18377.py'
Run-Python '.github/scripts/fix_money_autoupdate_18378.py'
Run-Python '.github/scripts/set_desktop_version_18378.py'
Run-Python '.github/scripts/validate_money_autoupdate_release_18378.py'
Run-Python '.github/scripts/fix_scorer_identity_18379.py'
Run-Python '.github/scripts/test_scorer_identity_18379.py'
Run-Python '.github/scripts/set_desktop_version_18379.py'
Run-Python '.github/scripts/validate_scorer_identity_release_18379.py'
Run-Python '.github/scripts/fix_coach_honors_inline_scorers_18380.py'
Run-Python '.github/scripts/test_coach_honors_inline_scorers_18380.py'
Run-Python '.github/scripts/set_desktop_version_18380.py'
Run-Python '.github/scripts/validate_coach_honors_inline_release_18380.py'
Run-Python '.github/scripts/fix_national_history_competition_filter_18381.py'
Run-Python '.github/scripts/test_national_history_competition_filter_18381.py'
Run-Python '.github/scripts/set_desktop_version_18381.py'
Run-Python '.github/scripts/validate_national_history_filter_release_18381.py'
Run-Python '.github/scripts/optimize_career_sync_load_18382.py'
Run-Python '.github/scripts/test_career_sync_load_18382.py'
Run-Python '.github/scripts/set_desktop_version_18382.py'
Run-Python '.github/scripts/validate_career_sync_load_release_18382.py'
Run-Python '.github/scripts/apply_flags_coaches_stars_aging_18383.py'
Run-Python '.github/scripts/test_flags_coaches_stars_aging_18383.py'
Run-Python '.github/scripts/set_desktop_version_18383.py'
Run-Python '.github/scripts/validate_career_realism_release_18383.py'
Run-Python '.github/scripts/fix_season_scope_18384.py'
Run-Python '.github/scripts/balance_ai_rosters_18384.py'
Run-Python '.github/scripts/group_player_honors_18384.py'
Run-Python '.github/scripts/test_season_scope_18384.py'
Run-Python '.github/scripts/test_roster_balance_18384.py'
Run-Python '.github/scripts/test_player_honors_18384.py'
Run-Python '.github/scripts/set_desktop_version_18384.py'
Run-Python '.github/scripts/validate_season_roster_honors_release_18384.py'
Run-Python '.github/scripts/apply_fast_auth_18385.py'
Run-Python '.github/scripts/test_fast_auth_18385.py'
Run-Python '.github/scripts/set_desktop_version_18385.py'
Run-Python '.github/scripts/validate_fast_secure_login_release_18385.py'
Run-Python '.github/scripts/apply_nonblocking_startup_18386.py'
Run-Python '.github/scripts/test_nonblocking_startup_18386.py'
Run-Python '.github/scripts/set_desktop_version_18386.py'
Run-Python '.github/scripts/validate_nonblocking_startup_release_18386.py'")
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
if (-not $source.Contains("Run-Python '.github/scripts/test_calendar_match_retirement_18350.py'")) { throw 'Gerenciador de aposentadorias e alinhamento do calendario 18.350 ausentes.' }
if (-not $source.Contains("Run-Python '.github/scripts/test_seriec_phases_history_18351.py'")) { throw 'Testes das fases e campeoes da Serie C 18.351 ausentes.' }
if (-not $source.Contains("Run-Python '.github/scripts/test_oomsafe_saves_18352.py'")) { throw 'Teste de salvamento seguro para carreiras longas 18.352 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/test_seriec_full_history_18353.py'")) { throw 'Teste do vice e artilharia imediatos da Serie C 18.353 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/test_native_save_mirror_18354.py'")) { throw 'Teste de seguranca do espelhamento incremental 18.354 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/test_archive_root_shards_18354.py'")) { throw 'Teste dos arquivos historicos fragmentados 18.354 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/fix_job_saveexit_18355.py'")) { throw 'Oferta e salvamento 18.355 ausentes.' }
if (-not $source.Contains("Run-Python '.github/scripts/test_jobwait_18356.py'")) { throw 'Retomada segura das propostas 18.356 ausente.' }
if (-not $source.Contains("Run-Python '.github/scripts/test_dismissal_handoff_18357.py'")) { throw 'A demissao 18.357 requer regressao sem salvamento duplicado.' }
if (-not $source.Contains("Run-Python '.github/scripts/test_dismissal_button_18358.py'")) { throw 'Demissao durante as ferias 18.358 sem regressao da interface.' }
if (-not $source.Contains("Run-Python '.github/scripts/test_dismissal_control_18359.py'")) { throw '18.359 requer teste do evento real Worker e desbloqueio do botao.' }
if (-not $source.Contains("Run-Python '.github/scripts/test_vacation_finalize_18360.py'")) { throw '18.360 requer teste de salvamento atomico, memoria e fim de ferias leve.' }
if (-not $source.Contains("Run-Python '.github/scripts/test_fast_updater_18361.py'")) { throw '18.361 requer teste de progresso, assinatura, salvamento e CDN do atualizador.' }
if (-not $source.Contains("Run-Python '.github/scripts/test_core_transitions_18362.py'")) { throw '18.362 requer regressao real de demissao, sincronizacao e login.' }
if (-not $source.Contains("Run-Python '.github/scripts/test_jobwait_state_18363.py'")) { throw '18.363 exige teste real de retomada de proposta na jornada 42 de 2027.' }
if (-not $source.Contains("Run-Python '.github/scripts/test_vacation_job_handoff_18364.py'")) { throw '18.364 requires a real original Worker vacation-to-offer job handoff regression.' }
if (-not $source.Contains("Run-Python '.github/scripts/test_dismissal_source_18365.py'")) { throw '18.365 must test the native click dispatcher, actual dismissal Worker and career layout.' }
if (-not $source.Contains("Run-Python '.github/scripts/test_unemployed_scope_18366.py'")) { throw '18.366 must run real Chromium test within same lexical career scope; no detached scripts.' }
if (-not $source.Contains("Run-Python '.github/scripts/test_jobwait_real_progress_18367.py'")) { throw '18.367 requires three verified actual Worker dayfast journeys, not a cosmetic button click.' }
if (-not $source.Contains("Run-Python '.github/scripts/test_unemployed_real_worker_18368.py'")) { throw '18.368 requires original Worker transport and multi-round jobwait simulation, not mocked v53StartSimulation.' }
if (-not $source.Contains("Run-Python '.github/scripts/test_unemployed_real_browser_18368.py'")) { throw '18.368 requires real Chromium game Engine to advance two Worker dayfast rounds when unemployed.' }
if (-not $source.Contains("Run-Python '.github/scripts/test_vacation_resume_browser_18369.py'")) { throw '18.369 requires real Chromium test of vacation Worker stop then next match.' }
if (-not $source.Contains("Run-Python '.github/scripts/test_jobwait_memory_browser_18370.py'")) { throw '18.370 requires real Worker and durable final checkpoint.' }
if (-not $source.Contains("Run-Python '.github/scripts/set_desktop_version_18371.py'")) { throw '18.371 career transition gate is missing: set_desktop_version_18371.py' }
if (-not $source.Contains("Run-Python '.github/scripts/fix_contract_preferences_18371.py'")) { throw '18.371 career transition gate is missing: fix_contract_preferences_18371.py' }
if (-not $source.Contains("Run-Python '.github/scripts/fix_repeated_dismissal_18371.py'")) { throw '18.371 career transition gate is missing: fix_repeated_dismissal_18371.py' }
if (-not $source.Contains("Run-Python '.github/scripts/test_contract_preferences_18371.py'")) { throw '18.371 career transition gate is missing: test_contract_preferences_18371.py' }
if (-not $source.Contains("Run-Python '.github/scripts/test_repeated_dismissal_18371.py'")) { throw '18.371 career transition gate is missing: test_repeated_dismissal_18371.py' }
if (-not $source.Contains("Run-Python '.github/scripts/test_career_transitions_browser_18371.py'")) { throw '18.371 career transition gate is missing: test_career_transitions_browser_18371.py' }
if (-not $source.Contains("Run-Python '.github/scripts/set_desktop_version_18372.py'")) { throw '18.372 promotion and confirmation gate is missing: set_desktop_version_18372.py' }
if (-not $source.Contains("Run-Python '.github/scripts/fix_native_confirmations_18372.py'")) { throw '18.372 promotion and confirmation gate is missing: fix_native_confirmations_18372.py' }
if (-not $source.Contains("Run-Python '.github/scripts/fix_career_promotion_offers_18372.py'")) { throw '18.372 promotion and confirmation gate is missing: fix_career_promotion_offers_18372.py' }
if (-not $source.Contains("Run-Python '.github/scripts/test_native_confirmations_18372.py'")) { throw '18.372 promotion and confirmation gate is missing: test_native_confirmations_18372.py' }
if (-not $source.Contains("Run-Python '.github/scripts/test_career_promotion_offers_18372.py'")) { throw '18.372 promotion and confirmation gate is missing: test_career_promotion_offers_18372.py' }
if (-not $source.Contains("Run-Python '.github/scripts/test_promotion_confirmations_browser_18372.py'")) { throw '18.372 promotion and confirmation gate is missing: test_promotion_confirmations_browser_18372.py' }
if (-not $source.Contains("Run-Python '.github/scripts/set_desktop_version_18373.py'")) { throw '18.373 memory gate is missing: set_desktop_version_18373.py' }
if (-not $source.Contains("Run-Python '.github/scripts/fix_vacation_checkpoint_18373.py'")) { throw '18.373 memory gate is missing: fix_vacation_checkpoint_18373.py' }
if (-not $source.Contains("Run-Python '.github/scripts/fix_save_memory_runtime_18373.py'")) { throw '18.373 memory gate is missing: fix_save_memory_runtime_18373.py' }
if (-not $source.Contains("Run-Python '.github/scripts/fix_jobwait_memory_transfer_18373.py'")) { throw '18.373 memory gate is missing: fix_jobwait_memory_transfer_18373.py' }
if (-not $source.Contains("Run-Python '.github/scripts/fix_vacation_memory_boot_18373.py'")) { throw '18.373 memory gate is missing: fix_vacation_memory_boot_18373.py' }
if (-not $source.Contains("Run-Python '.github/scripts/fix_player_checkpoint_reuse_18373.py'")) { throw '18.373 memory gate is missing: fix_player_checkpoint_reuse_18373.py' }
if (-not $source.Contains("Run-Python '.github/scripts/finalize_long_career_memory_18373.py'")) { throw '18.373 memory gate is missing: finalize_long_career_memory_18373.py' }
if (-not $source.Contains("Run-Python '.github/scripts/test_vacation_checkpoint_18373.py'")) { throw '18.373 memory gate is missing: test_vacation_checkpoint_18373.py' }
if (-not $source.Contains("Run-Python '.github/scripts/test_save_memory_runtime_18373.py'")) { throw '18.373 memory gate is missing: test_save_memory_runtime_18373.py' }
if (-not $source.Contains("Run-Python '.github/scripts/test_jobwait_memory_transfer_18373.py'")) { throw '18.373 memory gate is missing: test_jobwait_memory_transfer_18373.py' }
if (-not $source.Contains("Run-Python '.github/scripts/test_vacation_memory_boot_18373.py'")) { throw '18.373 memory gate is missing: test_vacation_memory_boot_18373.py' }
if (-not $source.Contains("Run-Python '.github/scripts/test_player_checkpoint_reuse_18373.py'")) { throw '18.373 memory gate is missing: test_player_checkpoint_reuse_18373.py' }
if (-not $source.Contains("Run-Python '.github/scripts/test_long_career_memory_browser_18373.py'")) { throw '18.373 memory gate is missing: test_long_career_memory_browser_18373.py' }
if (-not $source.Contains("Run-Python '.github/scripts/set_desktop_version_18374.py'")) { throw '18.374 required gate missing: set_desktop_version_18374.py' }
if (-not $source.Contains("Run-Python '.github/scripts/prepare_career_club_season_18374.py'")) { throw '18.374 required gate missing: prepare_career_club_season_18374.py' }
if (-not $source.Contains("Run-Python '.github/scripts/test_season_job_offers_18374.py'")) { throw '18.374 required gate missing: test_season_job_offers_18374.py' }
if (-not $source.Contains("Run-Python '.github/scripts/test_club_management_18374.py'")) { throw '18.374 required gate missing: test_club_management_18374.py' }
if (-not $source.Contains("Run-Python '.github/scripts/test_season_rollover_18374.py'")) { throw '18.374 required gate missing: test_season_rollover_18374.py' }
if (-not $source.Contains("Run-Python '.github/scripts/test_season_job_offers_browser_18374.py'")) { throw '18.374 required gate missing: test_season_job_offers_browser_18374.py' }
if (-not $source.Contains("Run-Python '.github/scripts/test_club_management_browser_18374.py'")) { throw '18.374 required gate missing: test_club_management_browser_18374.py' }
if (-not $source.Contains("Run-Python '.github/scripts/test_season_rollover_browser_18374.py'")) { throw '18.374 required gate missing: test_season_rollover_browser_18374.py' }

'@
$marker = '$tempScript = Join-Path $env:RUNNER_TEMP'
if ([regex]::Matches($text, [regex]::Escape($marker)).Count -ne 1) { throw 'Pipeline original mudou; revisar integracao.' }
$text = $text.Replace($marker, $extra + "`n" + $marker)
$generated = Join-Path $PSScriptRoot 'build_desktop_support_18386_generated.ps1'
Set-Content $generated $text -Encoding utf8
& $generated
if ($LASTEXITCODE -ne 0) { throw 'Falha no build 18.386.' }

