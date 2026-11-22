from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# This script is only called after the signed installer and all regression
# reports have been verified. The mutable latest.json is published LAST.
FILES = ("FutBR-Manager-18.382-Windows.exe", "FutBR-Manager-18.382-Windows.exe.sig")


# 18.373 reports are generated on the final source, after preserved 18.372 gates.
MEMORY_REQUIREMENTS = {
    'vacation-checkpoint-18373-tests.json': ('ok', 'originalStreamAndReaderExecuted', 'originalSimulationFinalizerExecuted', 'manualPauseWithoutPromotionSaved', 'dismissalWithoutPromotionSaved', 'nationalVacationSaved', 'ordinaryAndSeasonEndSaved', 'checkpointPlayerChunksReused', 'bounded2029ChunkTransactions', 'fullPlayerFieldsPreserved', 'freshRootHistoryWins', 'previousManifestPreserved', 'noAdditionalWorldSave', 'commitBeforeSyncEndAndFinished', 'rolloverArchivesFromCurrentWorld', 'initialArchivesWithoutManifestPreserved', 'atomicFailurePreservesSave', 'partialChunkFailurePreservesSave', 'failedCommitNeverClaimsSaved', 'identitySaveIdAndDateGuards', 'transportOnlyDoesNotPublish'),
    'save-memory-runtime-18373-tests.json': ('ok', 'sameGameScope', 'noFullWorldSaveRPC', 'boundedPackedHistory', 'boundedScorerHistory', 'boundedCompetitionStats', 'fullRoundtrip', 'legacyYearIdHistoryReadable', 'sparseNamesAndUnknownFieldsPreserved', 'threeYearsPackedHistory', 'changedHistoryWritten', 'failedWriteKeepsCurrentAndPrevious', 'partialUIBlocked', 'ownerRecoveryFromAdvancedCheckpoint', 'crossCareerRecoveryRejected', 'deferredWorkerSaveSettledBeforeRelease', 'activeAndMutatingWorkersProtected', 'missingShardRejected', 'actualWorkerPackedHistoryRoundtrip', 'actualWorkerScorerHistoryRoundtrip', 'runtimeTestHookNotShipped', 'ownerCannotBeReleasedWhilePartial', 'exactVacationCheckpointAvoidsCoreReread', 'vacationOverlayMismatchKeepsLegacyFallback', 'cleanFlushWaitsForDeferredWorkerSave', 'concurrentCleanFlushesShareSettlement', 'actualWorkerSettlementWaitsForDeferredPromise', 'legacyDecisionAutosaveRaceReproduced', 'actualCoachAutosaveJoinsNewerWriter', 'actualNamedSaveWaitsForJoinedWriter', 'joinedFailureRejectsNamedSaveAndRearms', 'concurrentRealEditStillInvalidatesWriter', 'decisionScheduledDuringWriterGetsNewCheckpoint', 'reusableFingerprintBacking', 'legacyUtf8HashesUnchanged', 'malformedUnicodeAndNulPreserved', 'oversizedFingerprintSupportedWithoutRetainingBuffer', 'unsupportedFingerprintStillDisablesReuse'),
    'jobwait-memory-transfer-18373-tests.json': ('ok', 'zeroFullWorldJobwaitMessages', 'uiReleasedBeforeWorkerBoot', 'verifiedExactCheckpointToken', 'singleCompleteWorldOwner', 'residentNineDayLoop', 'boundedFourDayCheckpoints', 'exactOfferPolicyPreserved', 'fullWorldRestoredBeforeOffer', 'losslessHistoricalReturn', 'scorerAndUnknownTreesBounded', 'partialUIGuarded', 'mismatchedTokenAndCareerRejected', 'failedStreamRecoversDurableWorld', 'unsavedCoachDecisionsPreserved', 'inFlightArchiveMigrationCannotRebuildMirror', 'archiveMigrationResumesAfterReturn', 'archiveMigrationJoinedBeforeWorkerBoot', 'actualLegacyCleanupChainExecuted', 'returnOwnerSurvivesLegacyCleanup', 'exactOwnedMirrorRequiredAtReturn', 'normalReturnUsesNoRecovery', 'ordinaryVacationCleanupPreserved'),
    'vacation-memory-boot-18373-install.json': ('ok', 'boundedCheckpointBeforeVacationBoot', 'exactManifestVerifiedBeforeWorkerDecode', 'staleVacationOverlayDisabledForFreshBoot', 'inFlightArchiveMigrationJoinedBeforeSave', 'completeUiPreservedForVacationQueries'),
    'vacation-memory-boot-18373-tests.json': ('ok', 'actualBaseStartAndWorkerExecuted', 'boundedWriterBeforeWorkerBoot', 'zeroFullWorldVacationMessages', 'currentUnpersistedEditsReachWorker', 'staleSameDayVacationOverlayIgnored', 'failedSaveBlocksWorkerBoot', 'mismatchedManifestRejectedBeforeDecode', 'nationalAndRolloverHistoryPreserved', 'nonVacationDispatchPreserved', 'actualInFlightMigrationJoinedBeforeSave', 'actualBoundedStorageRuntimeExecuted', 'completeUiPreservedForVacationQueries', 'careerChangeDuringSaveAborts'),
    'player-checkpoint-reuse-18373-install.json': ('ok', 'canonicalPackedPlayerHash', 'threeWritersUseAlignedPlayerChunks', 'vacationManifestCarriesPlayerHashes', 'currentContentVerifiedBeforeReuse', 'legacyHashSchemesFailClosed', 'workerScratchNeverTransferred', 'threeUnpackersBuildFastPlayerObjects', 'packedPresenceAndExtraPrecedencePreserved', 'prototypeKeysDecodedAsSafeOwnData'),
    'player-checkpoint-reuse-18373-tests.json': ('ok', 'actualUiAndThreeWorkerPathsExecuted', 'canonicalHashesMatchPackedBytes', 'metadataOnlySaveReusesAllPlayerChunks', 'onePlayerEditRewritesOneChunk', 'knownAndExtraFieldsRoundtrip', 'unicodeAndPresenceBitsPreserved', 'alignedChunksBeforeAndAfter2029', 'vacationHashesPromotedIntoManifest', 'ordinaryWorkerReusesUiPlayerChunks', 'currentEveryBatchFingerprintRecomputed', 'legacyAndNullHashesNeverReused', 'failedCommitPreservesPreviousPlayers', 'transferDoesNotDetachHashScratch', 'workerHashScratchBounded', 'actualThreeUnpackersUseFastProperties', 'densePlayerCohortUsesFastProperties', 'existingPlayerUpdatesKeepFastProperties', 'sparsePackedPresencePreserved', 'extraOverridesAndSymbolsPreserved', 'prototypeKeysDecodedAsSafeOwnData', 'legacyPlayerCodecsRoundtrip'),
    'long-career-memory-browser-18373-tests.json': ('ok', 'fullOriginalWorldIn2029', 'threeHistoricalSeasonsPreserved', 'twoRealDismissalsAndOffers', 'immediateJobSearchAfterDismissal', 'zeroFullWorldJobWaitTransfers', 'zeroFullWorldSaveTransfers', 'zeroRpcWholeWorldReloads', 'workerSoleWorldOwnerDuringSearch', 'completeWorldReturnedWithoutRecovery', 'manualVacationStopThenRealSaveExit', 'cleanAndDirtySaveExitPaths', 'actualNamedReloadPreservesCollections', 'boardRenewalsPreservedAcrossClubs', 'testHooksNotShipped', 'withinMeasuredMemoryBudget', 'zeroFullWorldVacationTransfers', 'exactCheckpointVacationBoots', 'completeUiPreservedAtVacationBoot', 'unchangedPlayerChunksReusedOnSaveExit', 'canonicalPlayerCheckpoints'),
}

def verify_memory_reports(artifacts):
    version = json.loads((artifacts / 'desktop-version-18373-install.json').read_text(encoding='utf-8'))
    if version.get('ok') is not True or version.get('version') != '18.373.0' or version.get('canAutoUpdateFrom18372') is not True:
        raise RuntimeError('18.373 desktop version and upgrade preparation were not verified')
    installation = json.loads((artifacts / 'long-career-memory-18373-install.json').read_text(encoding='utf-8'))
    if installation.get('version') != '18.373.0' or any(installation.get(key) is not True for key in (
            'ok', 'allMemoryCorrectionsIntegrated', 'actualCareerScopeVerified',
            'priorCareerAndDialogCorrectionsPreserved', 'historicalRolloverWriterInstalled',
            'testHooksExcluded', 'editionUpdated', 'vacationBoundedBootIntegrated', 'playerCheckpointReuseIntegrated', 'playerFastUnpackersIntegrated')) or installation.get('parsedScripts', 0) < 1:
        raise RuntimeError('18.373 final game edition or integrated private-scope verification is missing')
    promotion = json.loads((artifacts / 'promotion-confirmations-browser-18372-tests.json').read_text(encoding='utf-8'))
    settlement = promotion.get('phases', {}).get('normal', {}).get('manualSettlement') or {}
    if promotion.get('manualCleanFlushHonorsDeferredSave') is not True or any(settlement.get(key) is not True for key in (
            'ok', 'originalCleanFlush', 'noExtraPersist', 'settledBeforeRelease')):
        raise RuntimeError('18.373 original manual-match flush did not settle the deferred Worker save before release')
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


from validate_career_sync_load_release_18382 import verify_release_reports

def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: publish_signed_update_r2_18382.py <project-dir>")
    project = Path(sys.argv[1]).resolve()
    artifacts = project / "artifacts"
    manifest_path = artifacts / "latest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("version") != "18.382.0":
        raise RuntimeError("Cannot publish manifest for another version")
    if manifest["platforms"]["windows-x86_64"]["url"].split("/")[-1] != FILES[0]:
        raise RuntimeError("Update URL must match signed installer")
    verification = json.loads((artifacts / 'updater-18382-signature-tests.json').read_text(encoding='utf-8'))
    if verification.get('ok') is not True or verification.get('version') != '18.382.0':
        raise RuntimeError('18.382 installer verification must complete before publication')
    for name in ('contract-preferences-18371-tests.json', 'repeated-dismissal-18371-tests.json',
                 'career-transitions-browser-18371-tests.json'):
        report = json.loads((artifacts / name).read_text(encoding='utf-8'))
        if report.get('ok') is not True:
            raise RuntimeError('18.371 career transition verification missing: ' + name)
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
    for name in ('native-confirmations-18372-tests.json', 'career-promotion-offers-18372-tests.json',
                 'promotion-confirmations-browser-18372-tests.json'):
        report = json.loads((artifacts / name).read_text(encoding='utf-8'))
        if report.get('ok') is not True:
            raise RuntimeError('18.372 promotion or confirmation verification missing: ' + name)
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
    verify_release_reports(project, artifacts)
    creds = {
        "account": os.environ.get("R2_ACCOUNT_ID", "").strip(),
        "bucket": os.environ.get("R2_BUCKET", "").strip(),
        "access": os.environ.get("R2_ACCESS_KEY_ID", "").strip(),
        "secret": os.environ.get("R2_SECRET_ACCESS_KEY", "").strip(),
    }
    if not all(creds.values()):
        raise RuntimeError("R2 update publishing requires account, bucket, access and secret")
    import boto3
    client = boto3.client(
        "s3", region_name="auto",
        endpoint_url="https://" + creds["account"] + ".r2.cloudflarestorage.com",
        aws_access_key_id=creds["access"],
        aws_secret_access_key=creds["secret"],
    )
    prefix = os.environ.get("R2_UPDATE_PREFIX", "updates").strip("/")
    for name in FILES:
        path = artifacts / name
        if not path.is_file() or path.stat().st_size < 32:
            raise RuntimeError("Signed update artifact missing: " + name)
        client.upload_file(str(path), creds["bucket"], prefix + "/" + name,
                           ExtraArgs={"ContentType": "application/octet-stream",
                                      "CacheControl": "public, max-age=31536000, immutable"})
        response = client.head_object(Bucket=creds["bucket"], Key=prefix + "/" + name)
        if int(response["ContentLength"]) != path.stat().st_size:
            raise RuntimeError("R2 artifact did not retain expected size: " + name)
        print("Published and verified", name, path.stat().st_size)
    # The public manifest is the last write so clients never see half a release.
    client.put_object(Bucket=creds["bucket"], Key=prefix + "/latest.json",
                      Body=manifest_path.read_bytes(),
                      ContentType="application/json; charset=utf-8",
                      CacheControl="public, max-age=60")
    print("Published version 18.382.0 to R2; public verification is the next workflow gate.")


if __name__ == "__main__":
    main()
