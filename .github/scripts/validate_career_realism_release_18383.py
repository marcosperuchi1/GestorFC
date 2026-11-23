"""Release gate for 18.383: offline flags and evidence-based long-career simulation."""
from pathlib import Path
import hashlib,json,subprocess,sys
from validate_support_release_18375 import extract_executable_scripts
VERSION='18.383.0'
def verify_release_reports(project,artifacts=None):
 root=Path(project).resolve();source=(root/'src/index.html').read_text(encoding='utf-8')
 cfg=json.loads((root/'src-tauri/tauri.conf.json').read_text(encoding='utf-8'))
 acl=json.loads((root/'src-tauri/capabilities/default.json').read_text(encoding='utf-8'))
 if cfg.get('version')!=VERSION:raise RuntimeError('Desktop version is not 18.383')
 if acl.get('windows')!=['main']:raise RuntimeError('ACL window scope unexpectedly changed')
 for permission in ('core:default','core:window:allow-set-fullscreen','core:window:allow-is-fullscreen'):
  if permission not in acl.get('permissions',[]):raise RuntimeError('Missing Tauri window permission '+permission)
 for mark in ('FUTBR_SCORER_HISTORY_RECOVERY_18377','FUTBR_WINDOW_OBS_HELP_18377','FUTBR_MONEY_AUTOUPDATE_18378','FUTBR_SCORER_IDENTITY_18379','FUTBR_COACH_HONORS_INLINE_SCORERS_18380','FUTBR_NATIONAL_HISTORY_FILTER_DEDUP_18381','FUTBR_CAREER_SYNC_LOAD_BOUNDED_18382','FUTBR_LONG_CAREER_REALISM_18383','FUTBR_FONT_SETTINGS_18376',
             'FUTBR_SCORERS_IN_SCOPE_18220_START','FUTBR_TRANSFER_INTEREST_18375',
             'FUTBR_UNEMPLOYED_CALENDAR_18374','FUTBR_SAVE_MEMORY_RUNTIME_18373_BEGIN'):
  if mark not in source:raise RuntimeError('Mandatory career feature missing: '+mark)
 for bad in ('document.documentElement.style.zoom=','.v375-open','v375Open()'):
  if bad in source:raise RuntimeError('Broken global zoom or duplicate navigation')
 if "window.GestorFC.version='18.383.0';window.GestorFC.visualVersion='18.383.0';" not in source:
  raise RuntimeError('UI version must match signed package')
 if cfg.get('plugins',{}).get('updater',{}).get('endpoints')!=['https://download.futbrmanager.com.br/updates/latest.json']:
  raise RuntimeError('Updater endpoint changed')
 if cfg.get('bundle',{}).get('createUpdaterArtifacts') is not True:
  raise RuntimeError('Signed updater artifacts required')
 dirs=[Path(artifacts).resolve()] if artifacts else []
 dirs.append(root)
 required={
 'historical-scorers-18377-tests.json':('ok','recentArchivePreserved','legacyArchiveSupported','historicalClubsCorrect','noStateMutation','largeUnscoredPlayersExcluded'),
 'history-scorers-18377-install.json':('ok','archiveRingNotExpanded','readsOnlyOneYearAtATime','recoversOldGlobalLeagueAndCupTotals','doesNotModifySave'),
 'window-capture-18377-install.json':('ok','scopeOnlyMainWindow','previousAclPreserved','windowToggleNowAuthorized','settingsCardPaddingCompacted'),
 'font-settings-18376-tests.json':('ok','font120ScalesOnlyText','sidebarAndGridWidthsUnchanged','fullscreenAndWindowButtonsWork'),
 'money-autoupdate-18378-tests.json':('ok','monetaryGroupingPtBR','numericEngineValuesPreserved','signedUpdaterAutoTriggeredAtStartup','guardedCareerSaveBeforeInstall'),
 'scorer-identity-18379-install.json':('ok','viewOnlyChanges','historicClubIdsPreferred','uniqueTeamNameFallback','readOnlySavedStats','nationalityColumnPreserved'),
 'scorer-identity-18379-tests.json':('ok','realRankingsRendererExecuted','existingBadgeAndTeamButton','linkedOriginalAndHistoricalTeams','playerNameFlagsDeduplicated','nationalityColumnUnchanged','allTimeStatsUnmodified','historicalTotalsUnmodified'),
 'coach-honors-inline-18380-install.json':('ok','coachTitlesGroupedByCompetitionAndClub','distinctYearsAndCountsShown','differentClubsKeptSeparate','bonusPointsAggregated','originalCoachTitlesAndGameWorldUnchanged','scorerCrestAndClubNameHorizontal','savedCareersUnchanged'),
 'coach-honors-inline-18380-tests.json':('ok','originalCoachRendererWrapped','duplicatedTitlesDeduplicatedInViewOnly','fourCupTitlesOneCard','differentClubsSeparate','nationalTrophiesPreserved','yearsSortedAndVisible','bonusPointsSummed','noCareerMutation','realCssComputedInChromium','clubNameBesideCrest','existingTableActionPreserved'),
 'national-history-filter-18381-install.json':('ok','uniqueOptionsByNormalizedCompetitionName','allHistoricalEditionIdsRetained','singleOptionFiltersEveryEdition','oldSelectedEditionIdSupported','nationalHistoryAndGameSavesUnchanged'),
 'national-history-filter-18381-tests.json':('ok','uniqueOptionsPerDisplayName','normalizedAccentAndWhitespace','multipleEditionIdsSameOption','selectsEveryYearOfTournament','formerSelectedIdCompatible','confederationAndNationFiltersPreserved','gameStateUntouched','actualBrowserOneOptionPerCompetition','nativeSelectValueFunctional'),
 'career-sync-load-18382-install.json':('ok','fourChunkReadBound','fourChunkCopyBound','nativeBatchedSaveSwitch','independentArchivedSaveChunks','sourceManifestsUntouched','failureCleanupWaited','decodedOneChunkAtATime','workerAckAfterEntireBatch','packedPlayersAppliedWithoutPairArrays','coreSaveAndSeasonRolloverUnchanged'),
 'career-sync-load-18382-tests.json':('ok','independentSavesPreserved','legacyAndPackedSaveLoadLossless','missingChunkFailsWithoutOverwrite','playerWorldTransferredExactly','nativeCopyCallsReducedAtLeastFourfold','workerAckGuardPreserved','yearHistoriesPreserved'),
 'career-realism-18383-install.json':('ok','allFlagsLocalAndOffline','nationalCoachAnnualReview','humanManagedNationalSideProtected','nationalCoachHistoryPreserved','starReviewEverySeason','starPromotionOnlyByMajorEuropeanWorldPerformances','shortlistNoEntireWorldArray','agingByPositionInAnnualLoop','retirementChanceIncreasesAt35To40','manualRetirementPreserved','noAdditionalWorldCopyOrFullPlayerLoop'),
 'career-realism-18383-tests.json':('ok','countryFlagsEmbeddedOffline','allNineAttachedFlagsRenderedChromium','nationalCoachTenureGuarantee','nationalHistoryUntouched','majorEuropeAndWorldOnlyStars','twoYearStarPromotion','oneSeasonExceptionalWorldStar','weakLeagueExcluded','noFullWorldScan','declineStartsAt35','positionSpecificSkillDecline','retirementRealisticAge40Rare','allExistingSavesUntouched'),
 }
 for filename,fields in required.items():
  path=next((d/filename for d in dirs if (d/filename).is_file()),None)
  if path is None:raise RuntimeError('Missing required test report: '+filename)
  report=json.loads(path.read_text(encoding='utf-8'))
  for flag in fields:
   if report.get(flag) is not True:raise RuntimeError('Failed release check: '+filename+':'+flag)
 scripts,skipped=extract_executable_scripts(source)
 if len(scripts)<129:raise RuntimeError('Lost original JS scripts')
 check=subprocess.run(['node','-e',
  'const vm=require("vm"),fs=require("fs");JSON.parse(fs.readFileSync(0,"utf8")).forEach((s,i)=>new vm.Script(s,{filename:"script-"+i+".js"}));'],
  input=json.dumps(scripts),text=True,capture_output=True,timeout=120)
 if check.returncode:raise RuntimeError(check.stderr[-3500:])
 report={'ok':True,'version':VERSION,'recovered2026GlobalScorers':True,
 'keepsHistoricalArchiveMemoryBounded':True,'aclMainWindowPermissionAuthorized':True,
 'obsCaptureMethodExplainedNotHardwareVerified':True,'settings125LayoutCompacted':True,
 'savedCareerUntouched':True,'previous18376BehaviorsPreserved':True,
 'sameUpdaterIdentity':True,'executableScripts':len(scripts),
 'sourceSha256':hashlib.sha256(source.encode()).hexdigest()}
 (root/'career-realism-release-18383-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))
 return report
if __name__=='__main__':
 if len(sys.argv)!=2:raise SystemExit('usage: validate_career_realism_release_18383.py <root>')
 verify_release_reports(sys.argv[1])
