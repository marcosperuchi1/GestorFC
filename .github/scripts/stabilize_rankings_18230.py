from __future__ import annotations

import json
import sys
from pathlib import Path


def fail(message: str) -> None:
    raise RuntimeError(message)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        fail(f"{label}: esperado 1, encontrado {count}")
    return text.replace(old, new, 1)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: stabilize_rankings_18230.py <project-dir>")

    project = Path(sys.argv[1]).resolve()
    index_path = project / "src" / "index.html"
    html = index_path.read_text(encoding="utf-8")

    if "FUTBR_RANKING_CACHE_18230_STABLE" in html:
        print("Ranking 18.230 ja estabilizado")
        return
    if "FUTBR_RANKING_CACHE_18230_START" not in html:
        fail("cache 18.230 ausente")

    html = replace_once(
        html,
        "  if(state!==s||v18221ClubRankKey(s)!==key){if(v18221ClubRankPendingKey===key)v18221ClubRankPendingKey='';return;}\n  if(v18230RankBusy()){",
        "  if(state!==s||v18221ClubRankKey(s)!==key){if(v18221ClubRankPendingKey===key)v18221ClubRankPendingKey='';return;}\n  if(v18230ClubRankEntries.has(key)){if(v18221ClubRankPendingKey===key)v18221ClubRankPendingKey='';return;}\n  if(v18230RankBusy()){",
        "evitar recomputacao depois do cache sincronico",
    )

    html = replace_once(
        html,
        " if(v18230ClubRankLastHTML&&v18230ClubRankLastBaseKey!==baseKey){v18221ClubRankStats.staleServed++;return v18230SyncNotice(v18230ClubRankLastHTML);}",
        " if(v18230ClubRankLastHTML&&v18221ClubRankCacheKey!==key){v18221ClubRankStats.staleServed++;return v18230SyncNotice(v18230ClubRankLastHTML);}",
        "stale while revalidate para jornada e filtros",
    )

    html = replace_once(
        html,
        "document.addEventListener('input',event=>{\n try{if(view!=='clubrankings'||!v18230IsClubRankControl(event.target))return;clearTimeout(v18230ClubRankFilterTimer);v18230ClubRankFilterTimer=setTimeout(()=>v18221InvalidateClubRanking('input'),160);}catch(e){}\n},true);",
        "document.addEventListener('input',event=>{\n try{if(view!=='clubrankings'||!v18230IsClubRankControl(event.target))return;clearTimeout(v18230ClubRankFilterTimer);v18221InvalidateClubRanking('input');v18230ClubRankFilterTimer=setTimeout(()=>{try{if(view==='clubrankings')v18221ScheduleClubRankPrewarm();}catch(e){}},160);}catch(e){}\n},true);",
        "invalidacao imediata dos filtros de clubes",
    )

    marker = "/* FUTBR_RANKING_CACHE_18230_END */"
    html = replace_once(
        html,
        marker,
        "/* FUTBR_RANKING_CACHE_18230_STABLE: no-duplicate-compute, stale-on-filter, immediate-filter-key */\n" + marker,
        "marcador de estabilizacao",
    )

    required = [
        "FUTBR_RANKING_CACHE_18230_STABLE",
        "v18230ClubRankEntries.has(key)",
        "v18221ClubRankCacheKey!==key",
        "v18221InvalidateClubRanking('input')",
    ]
    for item in required:
        if item not in html:
            fail("estabilizacao ausente: " + item)

    report = {
        "ok": True,
        "version": "18.230",
        "duplicateBackgroundCalculation": False,
        "staleWhileRevalidateOnFilters": True,
        "filterInvalidationBeforeLegacyHandler": True,
        "boundedSnapshots": 3,
    }
    (project / "rankings-18230-stability.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    index_path.write_text(html, encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
