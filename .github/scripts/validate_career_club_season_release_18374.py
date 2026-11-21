"""Require real behavior and exact tested-source provenance before publication."""
from __future__ import annotations

import gzip
import hashlib
import json
import sys
from pathlib import Path

VERSION = "18.374.0"
REQUIREMENTS = {
    "season-job-offers-18374-tests.json": (
        "actualFunctionsExecuted", "allActiveOverridesShareCalendar",
        "existing2031SaveRecovers", "latestSeasonStampStored", "calendarLengthChangesHandled",
        "eligibleWaitBoundedAtEightRounds", "realisticReputationCeilingPreserved",
        "freshOfferStopsGeneration", "repeatedDismissalYearsCovered", "actualCompactPacketAndDelta",
    ),
    "season-job-offers-browser-18374-tests.json": (
        "legacy2031SaveRecovered", "fullOriginalWorld", "actualJobSearchButtonAndWorker",
        "compactWorkerTransportPreserved", "zeroWholeWorldSaveTransfers",
        "completeWorldReturnedWithoutRecovery", "oldDismissalHistoryPreserved", "automaticOfferModal",
        "offerAndDatedClockSurviveNamedReload", "twentySavedCollectionsPreserved",
        "realOfferAcceptedAndSaved", "boardRenewalsFollowNewClub", "withinMeasuredMemoryBudget",
    ),
    "club-management-18374-tests.json": (
        "fullProductionEngineExecuted", "eightAreasAndTwelveLevels", "legacyLevelFivePreserved",
        "constructionNotInstant", "twoConcurrentProjectsEnforced", "paymentExactlyOnce",
        "financeAndProgressIdempotent", "seasonBoundaryAndReloadPreserved",
        "clubOwnershipAcrossManagerChanges", "cancellationRefundAndNoDoubleRefund",
        "insufficientFundsAndInvalidActionsRejected", "stadiumCapacityPreserved",
        "boundedMedicalTrainingAndYouthEffects", "actualCommercialAndSupporterEffects",
        "actualPerformanceLearningEffect", "scoutFutureMissionImprovement",
        "fourManagementPlansHaveTradeoffs", "noExtraWorldScan", "potentialAndGrowthCapsPreserved",
        "worldAndNationalDatesAdvanceProjects",
    ),
    "club-management-browser-18374-tests.json": (
        "originalClubRendererAndClickHandlers", "realFullWorld", "paymentAndNoInstantBenefitVerified",
        "twoConcurrentProjectsEnforced", "realManualMatchAndWorkerAdvanceProjectsOnce",
        "realVacationWorkerAdvancesProjectsOnce", "actualStorageReloadPreservesCostAndProgress",
        "cancelModalKeepsProjectUntilConfirmed", "proportionalRefundVerified",
        "planChoiceSurvivesReload", "nationalCoachCannotManageOldClub",
        "desktopAndMobileLayoutsVerified", "noNativeDialogs",
    ),
    "season-rollover-18374-tests.json": (
        "originalEngineExecuted", "originalFullCatalog", "sameWorldCupQualifiersAndReasons",
        "sameCalendarAndRandomState", "currentAndHistoricalTitleProfilesIdentical",
        "legacyNameOnlyAndDuplicateTitlesPreserved", "sameDayChangesVisible", "yearChangeVisible",
        "cacheReleasedAfterSuccessAndFailure", "profileWorkBoundedByClubs",
        "coachScansBoundedBySorts", "worldCupDrawRulesPreserved", "noHistoryDeleted",
    ),
    "season-rollover-browser-18374-tests.json": (
        "actualNextSeasonUiAndEngine", "fullOriginalCatalog", "priorAndClosedSeasonHistoryPreserved",
        "sameCalendarParticipantsAndPots", "sameHistoricalArchives",
        "finalRoundDismissalReceivesNextYearOffer", "boundedOfferWaitAfterRollover",
        "memoryBudgetPreserved", "fullTransitionFaster",
    ),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def measured_memory(report: dict, label: str) -> None:
    require(all(report.get(k) is True for k in ("ok", "withinRssBudget", "oldSpaceArgumentVerified")),
            label + ": measured memory gate is missing")
    require(0 < report.get("peakRssBytes", 0) <= report.get("rssBudgetBytes", 0) <= 3 * 1024 ** 3,
            label + ": Chromium RSS exceeded the unchanged 3 GiB budget")
    require(0 < report.get("requestedOldSpaceLimitMiB", 0) <= 1024,
            label + ": V8 old-space constraint was removed")
    require(report.get("forcedGarbageCollection") is False and report.get("rssSampleCount", 0) >= 10,
            label + ": memory measurement is incomplete or relies on forced collection")


def clean_flow(report: dict, label: str) -> None:
    require(not report.get("nativeDialogs") and not report.get("crashes") and not report.get("flowErrors"),
            label + ": native dialog, crash or runtime exception")
    require(not [e for e in report.get("errors", []) if e.get("phase") != "startup"],
            label + ": error during the actual game flow")


def verify_release_reports(project: Path, reports: Path | None = None, *, require_desktop: bool = True) -> dict:
    project = Path(project).resolve()
    reports = Path(reports).resolve() if reports else project
    source_path = project / "src/index.html"
    source = source_path.read_text(encoding="utf-8")
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()

    def read(name: str) -> dict:
        return json.loads((reports / name).read_text(encoding="utf-8-sig"))

    install = read("career-club-season-18374-install.json")
    require(install.get("version") == VERSION and install.get("sourceSha256") == digest,
            "The finalized source differs from the game being packaged")
    require(all(install.get(k) is True for k in (
        "ok", "allCorrectionsIntegrated", "actualEngineAndUiScopesVerified",
        "priorMemoryCareerAndDialogCorrectionsPreserved", "testHooksNotShipped", "editionUpdated")),
        "Integrated correction, actual scope or preserved regression marker is missing")
    require(install.get("parsedScripts", 0) >= 129, "Integrated JavaScript syntax check is incomplete")
    prepare = read("career-club-season-18374-prepare.json")
    baseline = hashlib.sha256((project / "baseline-18373.html").read_text(encoding="utf-8").encode("utf-8")).hexdigest()
    require(prepare.get("ok") is True and prepare.get("sourceSha256") == digest
            and prepare.get("baselineSourceSha256") == baseline and prepare.get("baselineOutsideShippedSource") is True,
            "The A/B baseline or final preparation does not match this run")
    tested = {}
    for name, flags in REQUIREMENTS.items():
        report = read(name)
        require(report.get("version") == VERSION and report.get("sourceSha256") == digest,
                "Regression ran against a different source: " + name)
        require(all(report.get(k) is True for k in ("ok", "testHooksNotShipped", *flags)),
                "Required behavioral regression is incomplete: " + name)
        if "baselineSourceSha256" in report:
            require(report["baselineSourceSha256"] == baseline, "Regression used a different baseline: " + name)
        clean_flow(report, name)
        tested[name] = report

    offers = tested["season-job-offers-18374-tests.json"]
    require(len(offers.get("newGenerators", [])) == 3 and len(offers.get("oldSourceReproduced", [])) == 2,
            "Every active generator and the original failures must be exercised")
    require(all(row.get("offers") == 0 and row.get("throughDay", -1) >= 33 for row in offers["oldSourceReproduced"]),
            "The original cross-season failure was not reproduced")
    offers_browser = tested["season-job-offers-browser-18374-tests.json"]
    require(offers_browser.get("initial", {}).get("players", 0) >= 180000,
            "The stuck-career scenario must use the complete player catalog")
    measured_memory(offers_browser.get("memory", {}), "Stuck-career recovery")
    progression = tested["club-management-18374-tests.json"].get("multiSeasonProgression", {})
    require(progression.get("trainingFromFiveToTwelveJornadas", 0) >= 180
            and progression.get("trainingFromFiveToTwelveCost", 0) >= 100000000,
            "Advanced management progression lost its meaningful time or financial cost")
    rollover = tested["season-rollover-browser-18374-tests.json"]
    for label in ("baseline", "patched"):
        clean_flow(rollover.get(label, {}), "Season rollover " + label)
        require(rollover.get(label, {}).get("ok") is True, "Full season rollover did not finish: " + label)
    measured_memory(rollover["patched"].get("memory", {}), "Complete season rollover")
    require(rollover.get("fullTransitionSpeedup", 0) > 1 / .85,
            "Complete 2028-to-2029 transition did not meet the measured improvement gate")

    # The constrained 2029 save/exit regression is rerun after all new patches.
    memory = read("long-career-memory-browser-18373-tests.json")
    require(memory.get("ok") is True and len(memory.get("cycles", [])) == 2,
            "Both final 2029 dismissal/save/exit/reload cycles must pass")
    clean_flow(memory, "Preserved 2029 memory regression")
    measured_memory(memory.get("memory", {}), "Preserved 2029 memory regression")
    require(read("vacation-checkpoint-18373-tests.json").get("sourceSha256") == digest,
            "The durable vacation checkpoint was not tested on the final source")
    require(read("jobwait-memory-transfer-18373-tests.json").get("sourceSha256") == digest,
            "The compact ownership regression was not tested on the final source")
    require(read("jobwait-memory-transfer-18373-tests.json").get("sharedCalendarMarketEngineExecuted18374") is True,
            "The compact transfer test did not execute the actual updated market")
    require(read("promotion-confirmations-browser-18372-tests.json").get("ok") is True,
            "Promotion and in-game confirmation regression failed")

    if require_desktop:
        desktop = read("desktop-version-18374-install.json")
        config = json.loads((project / "src-tauri/tauri.conf.json").read_text(encoding="utf-8-sig"))
        require(desktop.get("ok") is True and desktop.get("version") == VERSION
                and desktop.get("canAutoUpdateFrom18373") is True and config.get("version") == VERSION,
                "The desktop version or upgrade configuration is incorrect")
    archived_source = gzip.decompress((project / "artifacts/prepared-source-18374.html.gz").read_bytes())
    require(hashlib.sha256(archived_source).hexdigest() == digest,
            "The retained source artifact differs from the tested game")
    report = {
        "ok": True, "version": VERSION, "sourceSha256": digest,
        "rawSourceSha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "baselineSourceSha256": baseline, "sixBehavioralReportsMatchPackagedSource": True,
        "priorMemoryAndPromotionRegressionsPreserved": True,
        "measuredRollOverImprovement": True, "unchangedMemoryLimits": True,
        "desktopVersionVerified": require_desktop, "reports": list(REQUIREMENTS),
    }
    (project / "artifacts/release-validation-18374.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: validate_career_club_season_release_18374.py <project>")
    print(json.dumps(verify_release_reports(Path(sys.argv[1]), require_desktop=False), ensure_ascii=False))


if __name__ == "__main__":
    main()
