from __future__ import annotations
import base64, hashlib, json, re, sys
from pathlib import Path

VERSION='18.373.0'
INSTALLER='FutBR-Manager-18.373-Windows.exe'
FEED='https://download.futbrmanager.com.br/updates/latest.json'

def public_id(wrapped):
    source=base64.b64decode(wrapped.strip(),validate=True).decode('utf-8')
    lines=[line.strip() for line in source.splitlines() if re.fullmatch(r'RW[A-Za-z0-9+/=]+',line.strip())]
    if len(lines)!=1:raise RuntimeError('Updater configuration does not contain exactly one minisign public key')
    decoded=base64.b64decode(lines[0],validate=True)
    if len(decoded)!=42:raise RuntimeError('Malformed updater public key')
    return decoded[2:10]

def signed_id(signature):
    source=signature.strip()
    try:source=base64.b64decode(source,validate=True).decode('utf-8')
    except (ValueError,UnicodeDecodeError):pass
    for line in source.splitlines():
        try:decoded=base64.b64decode(line.strip(),validate=True)
        except ValueError:continue
        if len(decoded)>=74 and decoded[:2] in (b'ED',b'Ed'):
            return decoded[2:10]
    raise RuntimeError('Malformed or missing minisign installer signature')

# 18.373 reports are generated on the final source, after preserved 18.372 gates.
MEMORY_REQUIREMENTS = {
    'vacation-checkpoint-18373-tests.json': ('ok', 'originalStreamAndReaderExecuted', 'originalSimulationFinalizerExecuted', 'manualPauseWithoutPromotionSaved', 'dismissalWithoutPromotionSaved', 'nationalVacationSaved', 'ordinaryAndSeasonEndSaved', 'checkpointPlayerChunksReused', 'bounded2029ChunkTransactions', 'fullPlayerFieldsPreserved', 'freshRootHistoryWins', 'previousManifestPreserved', 'noAdditionalWorldSave', 'commitBeforeSyncEndAndFinished', 'rolloverArchivesFromCurrentWorld', 'initialArchivesWithoutManifestPreserved', 'atomicFailurePreservesSave', 'partialChunkFailurePreservesSave', 'failedCommitNeverClaimsSaved', 'identitySaveIdAndDateGuards', 'transportOnlyDoesNotPublish'),
    'save-memory-runtime-18373-tests.json': ('ok', 'sameGameScope', 'noFullWorldSaveRPC', 'boundedPackedHistory', 'boundedScorerHistory', 'boundedCompetitionStats', 'fullRoundtrip', 'legacyYearIdHistoryReadable', 'sparseNamesAndUnknownFieldsPreserved', 'threeYearsPackedHistory', 'changedHistoryWritten', 'failedWriteKeepsCurrentAndPrevious', 'partialUIBlocked', 'ownerRecoveryFromAdvancedCheckpoint', 'crossCareerRecoveryRejected', 'deferredWorkerSaveSettledBeforeRelease', 'activeAndMutatingWorkersProtected', 'missingShardRejected', 'actualWorkerPackedHistoryRoundtrip', 'actualWorkerScorerHistoryRoundtrip', 'runtimeTestHookNotShipped'),
    'jobwait-memory-transfer-18373-tests.json': ('ok',),
    'long-career-memory-browser-18373-tests.json': ('ok', 'fullOriginalWorldIn2029', 'threeHistoricalSeasonsPreserved', 'twoRealDismissalsAndOffers', 'immediateJobSearchAfterDismissal', 'zeroFullWorldJobWaitTransfers', 'zeroFullWorldSaveTransfers', 'zeroRpcWholeWorldReloads', 'workerSoleWorldOwnerDuringSearch', 'completeWorldReturnedWithoutRecovery', 'manualVacationStopThenRealSaveExit', 'cleanAndDirtySaveExitPaths', 'actualNamedReloadPreservesCollections', 'boardRenewalsPreservedAcrossClubs', 'testHooksNotShipped', 'withinMeasuredMemoryBudget'),
}

def verify_memory_reports(artifacts):
    version = json.loads((artifacts / 'desktop-version-18373-install.json').read_text(encoding='utf-8'))
    if version.get('ok') is not True or version.get('version') != '18.373.0' or version.get('canAutoUpdateFrom18372') is not True:
        raise RuntimeError('18.373 desktop version and upgrade preparation were not verified')
    for name, required in MEMORY_REQUIREMENTS.items():
        report = json.loads((artifacts / name).read_text(encoding='utf-8'))
        if report.get('version') != '18.373.0' or any(report.get(key) is not True for key in required):
            raise RuntimeError('18.373 mandatory long-career memory checks missing: ' + name)
        if name == 'vacation-checkpoint-18373-tests.json':
            if report.get('identityGuardCases', 0) < 19 or len(report.get('scenarios', [])) != 5:
                raise RuntimeError('18.373 vacation checkpoint cases are incomplete')
        if name == 'long-career-memory-browser-18373-tests.json':
            memory = report.get('memory') or {}
            if any(memory.get(key) is not True for key in ('ok', 'withinRssBudget', 'oldSpaceArgumentVerified')):
                raise RuntimeError('18.373 constrained browser memory measurements are missing')
            limit = memory.get('requestedOldSpaceLimitMiB', 0)
            budget = memory.get('rssBudgetBytes', 0)
            peak = memory.get('peakRssBytes', 0)
            if not isinstance(limit, (int, float)) or not 0 < limit <= 1024:
                raise RuntimeError('18.373 browser must run with at most 1024 MiB V8 old space')
            if not isinstance(budget, (int, float)) or not 0 < peak <= budget <= 3 * 1024 ** 3:
                raise RuntimeError('18.373 measured Chromium process RSS exceeded the 3 GiB budget')
            if memory.get('forcedGarbageCollection') is not False or memory.get('rssSampleCount', 0) < 10 or len(memory.get('heapProbes', [])) < 2:
                raise RuntimeError('18.373 memory probe is incomplete or relies on forced garbage collection')
            if len(report.get('cycles', [])) != 2 or report.get('initial', {}).get('year') != 2029:
                raise RuntimeError('18.373 must validate two complete 2029 career cycles')
            if report.get('nativeDialogs') or report.get('crashes') or any(error.get('phase') != 'startup' for error in report.get('errors', [])):
                raise RuntimeError('18.373 real career flow had an exception, native dialog or crash')


def main():
    if len(sys.argv)!=2:raise SystemExit('usage: verify_desktop_updater_signature_18373.py <project-dir>')
    root=Path(sys.argv[1]).resolve()
    cfg=json.loads((root/'src-tauri/tauri.conf.json').read_text(encoding='utf-8'))
    artifacts=root/'artifacts'
    manifest=json.loads((artifacts/'latest.json').read_text(encoding='utf-8'))
    signature=(artifacts/(INSTALLER+'.sig')).read_text(encoding='utf-8').strip()
    manifest_signature=manifest['platforms']['windows-x86_64']['signature'].strip()
    if manifest.get('version')!=VERSION or cfg.get('version')!=VERSION:
        raise RuntimeError('Packaged Tauri version or manifest is not 18.373')
    if manifest_signature!=signature:raise RuntimeError('Published manifest does not use exactly the built signature')
    updater=cfg.get('plugins',{}).get('updater',{})
    if updater.get('endpoints')!=[FEED]:raise RuntimeError('Updater endpoint has changed')
    if public_id(updater.get('pubkey',''))!=signed_id(signature):
        raise RuntimeError('SECURITY BLOCK: embedded updater public key does not match NSIS installer private signing key')
    if root.joinpath('src-tauri','target','release','bundle','nsis').is_dir() is False:
        raise RuntimeError('Unsigned or missing NSIS build')
    if not manifest['platforms']['windows-x86_64']['url'].startswith('https://download.futbrmanager.com.br/updates/'):
        raise RuntimeError('Updater asset is not HTTPS')
    installer=artifacts/INSTALLER
    digest=hashlib.sha256(installer.read_bytes()).hexdigest()
    if digest!=(artifacts/'SHA256SUMS.txt').read_text(encoding='ascii').strip().split()[0]:
        raise RuntimeError('Installer SHA-256 does not match the checksum manifest')
    for name in ('initial-nationalities-18340-tests.json','scorers-submit-18340-tests.json','desktop-version-18369-install.json','welcome-national-preview-18342-tests.json','season-save-18343-tests.json','career-isolation-18344-tests.json','serie-c-champion-18345-tests.json','retirement-vacation-18346-tests.json','calendar-list-18347-tests.json','calendar-nav-version-18348-tests.json','incremental-saves-calendar-18349-tests.json','calendar-retirement-18350-tests.json','serie-c-phases-history-18351-tests.json','oomsafe-save-18352-tests.json','serie-c-full-history-18353-tests.json','job-save-exit-18355-tests.json','jobwait-season-18356-tests.json','dismissal-handoff-18357-tests.json','dismissal-button-18358-tests.json','dismissal-control-18359-tests.json','vacation-finalize-18360-tests.json','fast-updater-18361-tests.json','native-save-mirror-18354-tests.json','archive-root-shards-18354-tests.json','core-transitions-18362-tests.json','jobwait-state-18363-tests.json','vacation-handoff-18364-tests.json','dismissal-source-18365-tests.json','scope-repair-18366-tests.json','unemployed-worker-18368-tests.json','unemployed-browser-18368-tests.json','vacation-resume-18369-tests.json','vacation-queue-18369-tests.json','root-gameplay-tests.json','vacation-lifecycle-scope-18369-tests.json','vacation-resume-browser-18369-tests.json','vacation-dismissal-browser-18369-tests.json','desktop-version-18370-install.json','jobwait-memory-18370-tests.json','jobwait-memory-browser-18370-tests.json'):
        report=json.loads((artifacts/name).read_text(encoding='utf-8'))
        if not report.get('ok'):raise RuntimeError('Mandatory preserved game regression failed: '+name)
    fast=json.loads((artifacts/'fast-updater-18361-tests.json').read_text(encoding='utf-8'))
    if not all(fast.get(k) for k in ('ok','cachedOnlyTrustedMetadata','saveBeforeInstall','secondHTTPManifestCheckAvoided','liveDownloadPercentage','signedInstallerRemainsOnlyNativePath','noInstallerPrefetch','samePerUserInstaller','progressDoesNotBypassSave','directCDN')):
        raise RuntimeError('18.369 fast updater and career preservation verification missing')
    core=json.loads((artifacts/'core-transitions-18362-tests.json').read_text(encoding='utf-8'))
    if not all(core.get(k) for k in ('ok','outerPromiseRequired','noEarlyUnlock','firstUnemployedDayUsesLiveWorld')):raise RuntimeError('18.369 Worker completion regression failed')
    job=json.loads((artifacts/'jobwait-state-18363-tests.json').read_text(encoding='utf-8'))
    if not all(job.get(k) for k in ('ok','screenshot2027Day42Recovered','loadedUnemployedCareerRecovered',
        'realDayfastUsed','blocksActualWorkerAndSave','stopButtonAccessible')):
        raise RuntimeError('18.369 unemployed job-wait regression failed')
    handoff=json.loads((artifacts/'vacation-handoff-18364-tests.json').read_text(encoding='utf-8'))
    if not all(handoff.get(k) for k in ('ok','screenshot2026Day97Handoff','sendsOriginalWorkerPauseEnd','noSecondWorkerUntilOriginalPromise','automaticJobSearchAfterCheckpoint','failedVacationDoesNotStartWorker','wrongCareerCannotAutoSearch')):
        raise RuntimeError('18.369 actual dismissed-holiday Worker handoff regression failed')
    source=json.loads((artifacts/'dismissal-source-18365-tests.json').read_text(encoding='utf-8'))
    if not all(source.get(k) for k in ('ok','primaryNativeClickRouteTested','dismissedDay29VacationStillRunning',
      'firstClickRequestsOriginalWorkerEnd','secondClickDoesNotCancel','pendingVisibleInButton',
      'originalCheckpointRequired','automaticJobSearchAfterSync','autoStopOnActualDismissalEvent',
      'careerHistoryReadable','partialCareerShowsSyncPlaceholder','navigationDuringSyncAllowed')):
        raise RuntimeError('18.369 real native click and original vacation Worker regression failed')
    scope=json.loads((artifacts/'scope-repair-18366-tests.json').read_text(encoding='utf-8'))
    if not all(scope.get(k) for k in (
        'ok','scriptInOriginalLexicalScope','detachedControllersRemoved',
        'realChromiumBootAndScopeChecked','actualDOMClickSendsOriginalWorkerEnd',
        'secondDOMClickKeepsRequest','postCheckpointStartsJobOnce',
        'synchronizingCareerReadOnlyView','legacy18363And18364ScopeCallable'
    )) or scope.get('stateReferenceErrors')!=0:
        raise RuntimeError('18.369 browser ran disconnected private state or refused to start the real job handoff')
    progress=json.loads((artifacts/'job-progress-18367-tests.json').read_text(encoding='utf-8'))
    if not all(progress.get(k) for k in ('ok','threeRealDaysAdvanced','stopsAtOffer','dayfastWorker','phantomDaysRejected','failedWorkerLeavesSafeState','stopControlStillWorks')):
        raise RuntimeError('18.369 job-wait genuine three-day Worker advancement regression failed')
    real=json.loads((artifacts/'unemployed-worker-18368-tests.json').read_text(encoding='utf-8'))
    if not all(real.get(k) for k in (
      'ok','testedOriginalV53StartSimulation','testedOriginalV89RunJobWait',
      'realBaseWorkerPostMessage','threeSequentialDayfastMessages',
      'oneLiveWorldTransfer','noFullWorldPreSave','allLaterRoundsResident',
      'staleDiskReplayForbidden','jobOfferStops','phantomRoundFails',
      'stopActionWorks','sourceWorkerIdentityGuard','saveCodecUnchanged'
    )):
        raise RuntimeError('18.369 original Worker postMessage or unemployed live-state regression failed')
    browser=json.loads((artifacts/'unemployed-browser-18368-tests.json').read_text(encoding='utf-8'))
    if not all(browser.get(k) for k in (
      'ok','originalEngineRealBrowser','originalWorkerExecuted',
      'twoRealEngineJornadas','twoActualDaysAdvanced','careerIdentityPreserved',
      'unemployedStayedUnemployed','didNotLeaveJobWaitActive','testHookNotShipped'
    )):
        raise RuntimeError('18.369 real Chromium test failed: no two genuine unemployed game rounds')
    basic=json.loads((artifacts/'vacation-resume-18369-tests.json').read_text(encoding='utf-8'))
    realvac=json.loads((artifacts/'vacation-resume-browser-18369-tests.json').read_text(encoding='utf-8'))
    if not all(basic.get(k) for k in (
      'ok','realOriginalV53StartSimulation','nextMatchAfterVacationWorks',
      'normalDayAfterVacationWorks','noPreSaveBeforeResume','noStaleDiskReload',
      'careerIdentityGuard','noEarlySyncRelease',
      'previousSessionGuard','noStrongWorldRetention','dispatchConsumesToken','failedDispatchPreservesToken','newVacationConsumesOldToken'
    )):
        raise RuntimeError('18.369 normal-day or nextmatch Worker handoff regression failed')
    if not all(realvac.get(k) for k in (
      'ok','realOriginalEngine','realVacationWorkerAndStream',
      'realNextMatchAfterManualVacationEnd','realWorkersNotMocked',
      'originalManualEndCommandAccepted','terminalRepaintFailurePreservesOriginalPromise','originalLifecycleHasPrivateState','originalFinalHandlerUsesScopedLifecycle','testHookNotShipped'
    )):
        raise RuntimeError('18.369 Chrome real vacation stop followed by nextmatch failed')
    queue=json.loads((artifacts/'vacation-queue-18369-tests.json').read_text(encoding='utf-8'))
    if not all(queue.get(k) for k in ('ok', 'originalFinalDrainExecuted', 'vacLiveAckSurvivesPaintException', 'nextMatchSyncSurvivesPaintException', 'finishedPromiseSettlesOnce', 'errorToastCannotLoseRejection', 'appliedMessagesNeverReplayed', 'realDataFailureRejectsWithoutAck', 'dataFailureRoutesToOriginalRecovery', 'queueOwnershipAlwaysReleased', 'staleSessionIgnored', 'nationalJumpPaintFailureKeepsSyncAndSchedulers')):
        raise RuntimeError('18.369 Worker queue or acknowledgement recovery regression failed')
    national=json.loads((artifacts/'root-gameplay-tests.json').read_text(encoding='utf-8'))
    if not all(national.get(k) for k in ('ok', 'nationaljump_root', 'nationaljump_final_handler', 'nationaljump_rejects_missing_paint', 'nationaljump_rejects_missing_scheduler', 'nationaljump_rejects_inactive_handler')):
        raise RuntimeError('18.369 national-jump active-handler repaint or scheduler regression failed')
    lifecycle=json.loads((artifacts/'vacation-lifecycle-scope-18369-tests.json').read_text(encoding='utf-8'))
    if not all(lifecycle.get(k) for k in ('ok', 'originalLifecycleFunctionsExecuted', 'lifecycleInsideOriginalPrivateUI', 'employedFinishedCallbackHasPrivateState', 'dismissalUsesSamePrivateWorld', 'outerVacationPromiseSettlesBeforeHandoff', 'controllerWrapperOrderPreserved', 'storageCleanupUsesExplicitScalarBridge', 'careerStateNotExported', 'dismissalFinishedIdentityIsWeak')):
        raise RuntimeError('18.369 private lifecycle or dismissal settlement regression failed')
    dismissal=json.loads((artifacts/'vacation-dismissal-browser-18369-tests.json').read_text(encoding='utf-8'))
    if not all(dismissal.get(k) for k in ('ok', 'originalEngineAndWorker', 'testInputOnly', 'realDismissalWorkerEvent', 'originalLifecycleCompleted', 'twoRealJobSearchDaysAfterDismissal', 'realEmployedToUnemployedTransition', 'testHookNotShipped')):
        raise RuntimeError('18.369 real vacation dismissal or subsequent job-search advancement regression failed')
    bounded=json.loads((artifacts/'jobwait-memory-18370-tests.json').read_text(encoding='utf-8'))
    browser_memory=json.loads((artifacts/'jobwait-memory-browser-18370-tests.json').read_text(encoding='utf-8'))
    if not all(bounded.get(k) for k in ('ok','noUnboundedSaveChain','priorWorldReferenceRemoved','immediateOfferCheckpoint','rollbackOnFailure','allHistoricalFieldsStayInWorld','actualPostRoundLoopExecuted','originalWorkerCheckpointGuardExecuted')):
        raise RuntimeError('18.370 bounded checkpoint and history regression failed')
    if not all(browser_memory.get(k) for k in ('ok','actualEngine','actualWorker','realDayfastJornadas','diskCheckpointConfirmed','checkpointMatchesReturnedDay','noCheckpointFailures','noConcurrentCheckpoint','realBrowserSource')):
        raise RuntimeError('18.370 real browser could not persist its final dayfast journey')
    for name in ('desktop-version-18371-install.json', 'contract-preferences-18371-tests.json',
                 'repeated-dismissal-18371-tests.json', 'career-transitions-browser-18371-tests.json'):
        report=json.loads((artifacts/name).read_text(encoding='utf-8'))
        if not report.get('ok'):
            raise RuntimeError('18.371 career transition regression failed: '+name)
    current_version=json.loads((artifacts/'desktop-version-18371-install.json').read_text(encoding='utf-8'))
    if current_version.get('version')!='18.371.0':
        raise RuntimeError('18.371 desktop version preparation was not verified')
    # These checks execute the actual patched functions, including current
    # Worker ownership and settings persistence across three employment spells.
    transition_requirements = {
        'career-transitions-browser-18371-tests.json': ('realEngineAndWorkers', 'threeDismissalsSameCareer', 'threeSuccessfulSearches', 'boardPreferenceAcrossClubs', 'actualJobButtonEnabled', 'actualJobButtonClickHandled', 'manualPreferencePersistsAfterReload', 'statusRPCAtEachVacationBoundary', 'noOrphanedRPCsAfterThirdDismissal', 'threeDistinctClubs', 'testHookNotShipped'),
        'contract-preferences-18371-tests.json': ('sourceSimulationMessageExecuted', 'sourceFinalDrainExecuted', 'serializedReloadPreservesSettings', 'manualChoiceWins', 'otherCareerAndManagerRejected', 'authoritativeWorkerRenewsOnce', 'uiDoesNotMutateBeforeSavedWorldLoad', 'nationalJobDoesNotRenewOldClub', 'checkpointRootPreserved', 'noFullWorldCloneAdded'),
        'repeated-dismissal-18371-tests.json': ('originalFunctionsExecuted', 'oldWorkerRPCSettled', 'readOnlyCheckDoesNotBlock', 'retiredWorkerErrorIgnored', 'onlyRetiredOwnerCanceled', 'lateReplyIgnored', 'currentSaveProtected', 'activeSimulationStreamAndSaveProtected', 'currentHandoffSurvivesFormerClubCallback', 'duplicateStartKeepsCurrentOrigin', 'failedAcceptanceDoesNotReset'),
    }
    for name, required in transition_requirements.items():
        report = json.loads((artifacts / name).read_text(encoding='utf-8'))
        if any(report.get(key) is not True for key in required):
            raise RuntimeError('18.371 mandatory behavioral checks missing: ' + name)
        if name == 'repeated-dismissal-18371-tests.json':
            cycles = report.get('threeEmploymentDismissalCycles')
            if not isinstance(cycles, list) or len(cycles) != 3:
                raise RuntimeError('18.371 must validate three employment and dismissal cycles')
    for name in ('desktop-version-18372-install.json', 'native-confirmations-18372-tests.json',
                 'career-promotion-offers-18372-tests.json', 'promotion-confirmations-browser-18372-tests.json'):
        report=json.loads((artifacts/name).read_text(encoding='utf-8'))
        if report.get('ok') is not True:
            raise RuntimeError('18.372 promotion or confirmation regression failed: '+name)
    current_version=json.loads((artifacts/'desktop-version-18372-install.json').read_text(encoding='utf-8'))
    if current_version.get('version')!='18.372.0' or current_version.get('canAutoUpdateFrom18371') is not True:
        raise RuntimeError('18.372 desktop version preparation was not verified')
    release_requirements = {
        'career-promotion-offers-18372-tests.json': ('superiorClubBeyondLegacyCut', 'goodAndPoorFormControls', 'employmentAndNationalGuards', 'plausibleBoardInterestRequired', 'domesticDivisionAndForeignQuality', 'uiListsOnlyReceivedOffers', 'noEmploymentMutationBeforeAcceptance', 'oneOfferAndCooldown', 'sameOfferAndExpiryAfterReload', 'originalDeferHandlerPreservesExpiry', 'rejectionCooldownPreserved', 'seasonBoundaryCooldownUsesOriginalCalendar', 'compactWorkerDecisionOverlay', 'otherCareerClubAndDateRejected', 'originalTakeJobAcceptsCurrentOffer', 'historyAndPreferencesPreserved', 'expiredAndWrongCareerOffersRejected', 'actualAsyncRoundAndVacationFunctionsExecuted', 'vacationStopsAfterCompletedRound', 'uiDoesNotDuplicateWorkerOffer', 'confirmedUserMatchRequired', 'unemployedMarketPreserved', 'deterministicSelectivePulse', 'engineWorkerScopeVerified', 'overlayAfterCheckpointRestore', 'expiredOfferCannotFallBackToCandidates', 'legacyOffersBoundAndAccepted', 'legacyScopeAndExpiryPreserved', 'originalStreamAndReaderPersistPromotion', 'checkpointReusesPlayerChunks', 'freshRootHistoryWinsOverOldShards', 'previousManifestPreserved', 'promotionCheckpointIdentityGuard', 'atomicCheckpointFailurePreservesSave', 'durableCommitScopedToNewPromotion'),
        'promotion-confirmations-browser-18372-tests.json': ('realEngineAndWorkers', 'normalMatchGeneratesPromotion', 'vacationGeneratesPromotion', 'vacationPausesAtOffer', 'superiorClubRequired', 'offersShownAutomatically', 'deferAndRejectRealClicks', 'offerSurvivesRealSaveReload', 'promotionAcceptedThroughRealClick', 'careerAndPreferencesPreserved', 'inGameDeleteModalRealClicks', 'noNativeDialogs', 'testHookNotShipped'),
        'native-confirmations-18372-tests.json': ('inGameDeleteConfirmation', 'noNativeConfirm', 'cancelPreservesStorage', 'escapePreservesStorage', 'closePreservesStorage', 'explicitConfirmDeletesOnlySelected', 'activeDeletionPreservesOtherCareers', 'singleCommitOnDoubleClick', 'staleConfirmationRejected', 'focusManaged', 'accountChangeRevalidated', 'storageErrorDoesNotClaimSuccess', 'originalRouterUsed', 'escapedCareerName', 'isolatedFixturesOnly', 'testHookNotShipped'),
    }
    for name, required in release_requirements.items():
        report = json.loads((artifacts / name).read_text(encoding='utf-8'))
        if any(report.get(key) is not True for key in required):
            raise RuntimeError('18.372 mandatory behavioral checks missing: ' + name)
    verify_memory_reports(artifacts)
    result={'ok':True,'version':VERSION,'installedUpdaterTrustMatchesSignature':True,
            'installerSha256Verified':True,'manifestSignatureExact':True,'careerSavesPreserved':True,
            'oneTimeManualInstallRequiredForBroken18339And18340':True,
            'publicKeyDerivedFromConfiguredSigner':True}
    (artifacts/'updater-18373-signature-tests.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result))

if __name__=='__main__':main()

