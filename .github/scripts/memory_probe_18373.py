"""Bounded test-only browser memory observation; no game objects are retained.

Call mark() from the Playwright thread. Only process RSS is sampled in the
background thread. RSS is the sum of process working sets, so shared pages can
be counted more than once. It is deliberately reported separately from V8 heap.
"""
from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path

import psutil


def _env_mib(name: str, default: int | None) -> int | None:
    raw = os.environ.get(name, "").strip()
    value = default if not raw else int(raw)
    if value is not None and value <= 0:
        raise ValueError(name + " must be a positive number of MiB")
    return value


def chromium_memory_args() -> list[str]:
    """A V8 old-space limit, not a limit on total browser process memory."""
    return ["--enable-automation", "--js-flags=--max-old-space-size=" + str(
        _env_mib("FUTBR_MEMORY_HEAP_MB", 1024))]


class MemoryProbe18373:
    def __init__(self, browser, *, interval: float = 0.1,
                 rss_budget_mib: int | None = None):
        if interval < 0.05:
            raise ValueError("RSS sampling faster than 50 ms is not permitted")
        self._browser_session = browser.new_browser_cdp_session()
        processes = self._browser_session.send("SystemInfo.getProcessInfo")["processInfo"]
        roots = [int(row["id"]) for row in processes if row["type"] == "browser"]
        if len(roots) != 1:
            raise RuntimeError("Cannot identify exactly one Chromium browser PID")
        self.browser_pid = roots[0]
        self._process = psutil.Process(self.browser_pid)
        self.interval = interval
        self.heap_limit_mib = _env_mib("FUTBR_MEMORY_HEAP_MB", 1024)
        arguments = self._browser_session.send("Browser.getBrowserCommandLine")["arguments"]
        expected_flag = "--max-old-space-size=" + str(self.heap_limit_mib)
        self.old_space_argument_verified = any(
            arg.startswith("--js-flags=") and expected_flag in arg.split("=", 1)[1].split()
            for arg in arguments)
        self.rss_budget_mib = rss_budget_mib if rss_budget_mib is not None else _env_mib(
            "FUTBR_MEMORY_RSS_BUDGET_MIB", None)
        if self.rss_budget_mib is not None and self.rss_budget_mib <= 0:
            raise ValueError("RSS budget must be positive")
        self._roles = {int(row["id"]): str(row["type"]) for row in processes}
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None
        self._started = time.monotonic()
        self._stage = "boot"
        self._count = 0
        self._samples = []
        self._omitted_samples = 0
        self._peak_rss = 0
        self._peak_private = 0
        self._max_processes = 0
        self._first_rss = None
        self._last_rss = None
        self._stages = {}
        self._errors = []
        self._heap = []
        self._page_sessions = {}
        self._finished = None

    def _error(self, message):
        with self._lock:
            if len(self._errors) < 20:
                self._errors.append(str(message)[:500])

    def _sample_rss(self):
        try:
            processes = {self.browser_pid: self._process}
            for child in self._process.children(recursive=True):
                processes[child.pid] = child
            rss = private = count = 0
            for process in processes.values():
                try:
                    info = process.memory_info()
                    rss += int(info.rss)
                    private += int(getattr(info, "private", 0))
                    count += 1
                except psutil.NoSuchProcess:
                    # A Worker or renderer may finish between enumeration and read.
                    continue
            elapsed = round(time.monotonic() - self._started, 3)
            with self._lock:
                self._count += 1
                self._peak_rss = max(self._peak_rss, rss)
                self._peak_private = max(self._peak_private, private)
                self._max_processes = max(self._max_processes, count)
                if self._first_rss is None:
                    self._first_rss = rss
                self._last_rss = rss
                sample = {"seconds": elapsed, "stage": self._stage,
                          "rssBytes": rss, "processes": count}
                if len(self._samples) < 24000:
                    self._samples.append(sample)
                else:
                    self._omitted_samples += 1
                stage = self._stages.setdefault(self._stage, {
                    "stage": self._stage, "samples": 0, "peakRssBytes": 0,
                    "firstSeconds": elapsed, "lastSeconds": elapsed})
                stage["samples"] += 1
                stage["peakRssBytes"] = max(stage["peakRssBytes"], rss)
                stage["lastSeconds"] = elapsed
        except (psutil.Error, OSError) as error:
            self._error("RSS observation failed: " + str(error))

    def _run(self):
        while not self._stop.wait(self.interval):
            self._sample_rss()

    def start(self):
        if self._thread is not None:
            raise RuntimeError("Memory probe already started")
        self._sample_rss()
        self._thread = threading.Thread(target=self._run,
                                        name="futbr-18373-browser-rss", daemon=True)
        self._thread.start()
        return self

    def mark(self, page, stage: str):
        """Observe the UI isolate on the Playwright thread without triggering GC."""
        if self._finished is not None:
            raise RuntimeError("Memory probe already finished")
        with self._lock:
            self._stage = str(stage)[:100]
        try:
            key = id(page)
            if key not in self._page_sessions:
                self._page_sessions[key] = page.context.new_cdp_session(page)
            usage = self._page_sessions[key].send("Runtime.getHeapUsage")
            row = {"seconds": round(time.monotonic() - self._started, 3),
                   "stage": self._stage, "usedBytes": int(usage["usedSize"]),
                   "allocatedBytes": int(usage["totalSize"])}
            for source, target in (("backingStorageSize", "backingStorageBytes"),
                                   ("embedderHeapUsedSize", "embedderHeapUsedBytes")):
                if source in usage:
                    row[target] = int(usage[source])
            # A scalar browser diagnostic only; never inspect/serialize game state.
            row["observedHeapLimitBytes"] = page.evaluate(
                "() => performance.memory?.jsHeapSizeLimit ?? null")
            processes = self._browser_session.send("SystemInfo.getProcessInfo")["processInfo"]
            with self._lock:
                self._roles.update({int(p["id"]): str(p["type"]) for p in processes})
                self._heap.append(row)
            return row
        except Exception as error:
            self._error("UI heap observation failed: " + str(error))
            return {"stage": self._stage, "error": str(error)[:500]}

    def finish(self):
        """Call before browser.close(); return a compact report, not the full trace."""
        if self._finished is not None:
            return self._finished
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2)
            if self._thread.is_alive():
                self._error("RSS sampler did not stop within two seconds")
        self._sample_rss()
        budget = self.rss_budget_mib * 1024 * 1024 if self.rss_budget_mib else None
        with self._lock:
            within_budget = budget is None or self._peak_rss <= budget
            self._finished = {
                "ok": self._count >= 2 and bool(self._heap) and not self._errors and within_budget and self.old_space_argument_verified,
                "browserPid": self.browser_pid,
                "sampleIntervalMs": round(self.interval * 1000),
                "rssSampleCount": self._count,
                "traceSamplesOmitted": self._omitted_samples,
                "peakRssBytes": self._peak_rss,
                "initialRssBytes": self._first_rss,
                "finalRssBytes": self._last_rss,
                "maxProcessCount": self._max_processes,
                "peakPrivateBytesWhenAvailable": self._peak_private,
                "rssScope": "Chromium process tree RSS sum; shared pages may be counted more than once",
                "heapScope": "UI V8 isolate; Worker heap is included only in process RSS",
                "requestedOldSpaceLimitMiB": self.heap_limit_mib,
                "oldSpaceArgumentVerified": self.old_space_argument_verified,
                "rssBudgetBytes": budget,
                "withinRssBudget": within_budget,
                "forcedGarbageCollection": False,
                "peakUiHeapUsedBytes": max((r["usedBytes"] for r in self._heap), default=0),
                "peakUiBackingStorageBytes": max((r.get("backingStorageBytes", 0) for r in self._heap), default=0),
                "phases": list(self._stages.values()),
                "heapProbes": list(self._heap),
                "processTypes": sorted(set(self._roles.values())),
                "errors": list(self._errors),
            }
        for session in [*self._page_sessions.values(), self._browser_session]:
            try:
                session.detach()
            except Exception:
                pass
        self._page_sessions.clear()
        return self._finished

    def write_trace(self, path):
        """Optional JSONL artifact; write after finish() to obtain a stable trace."""
        if self._finished is None:
            raise RuntimeError("Finish the probe before writing its trace")
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as stream:
            for sample in self._samples:
                stream.write(json.dumps(sample, separators=(",", ":")) + "\n")
