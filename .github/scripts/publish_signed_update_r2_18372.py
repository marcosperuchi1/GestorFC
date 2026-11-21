from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# This script is only called after the signed installer and all regression
# reports have been verified. The mutable latest.json is published LAST.
FILES = ("FutBR-Manager-18.372-Windows.exe", "FutBR-Manager-18.372-Windows.exe.sig")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: publish_signed_update_r2_18372.py <project-dir>")
    project = Path(sys.argv[1]).resolve()
    artifacts = project / "artifacts"
    manifest_path = artifacts / "latest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("version") != "18.372.0":
        raise RuntimeError("Cannot publish manifest for another version")
    if manifest["platforms"]["windows-x86_64"]["url"].split("/")[-1] != FILES[0]:
        raise RuntimeError("Update URL must match signed installer")
    verification = json.loads((artifacts / 'updater-18372-signature-tests.json').read_text(encoding='utf-8'))
    if verification.get('ok') is not True or verification.get('version') != '18.372.0':
        raise RuntimeError('18.372 installer verification must complete before publication')
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
    print("Published version 18.372.0 to R2; verify the public Pages route separately.")


if __name__ == "__main__":
    main()
