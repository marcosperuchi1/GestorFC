from __future__ import annotations

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
        raise SystemExit("usage: bootstrap_rankings_api.py <project-dir>")

    project = Path(sys.argv[1]).resolve()
    index_path = project / "src" / "index.html"
    html = index_path.read_text(encoding="utf-8")

    if "FUTBR_RANKINGS_EARLY_API_18222" in html:
        print("Early rankings API 18.222 already installed")
        return

    html = replace_once(
        html,
        "let v18220ScorerCacheState=null,v18220ScorerCacheKey='',v18220ScorerCacheRows=[];",
        "var v18220ScorerCacheState,v18220ScorerCacheKey,v18220ScorerCacheRows;",
        "cache de artilheiros hoisted",
    )
    html = replace_once(
        html,
        "let v18221ClubRankCacheState=null,v18221ClubRankCacheKey='',v18221ClubRankCacheHTML='',v18221ClubRankRevision=0,v18221ClubRankPendingKey='';\nconst v18221ClubRankStats={hits:0,misses:0,prewarms:0,invalidations:0};",
        "var v18221ClubRankCacheState,v18221ClubRankCacheKey,v18221ClubRankCacheHTML,v18221ClubRankRevision=0,v18221ClubRankPendingKey='',v18221ClubRankStats;\nfunction v18221Stats(){return v18221ClubRankStats||(v18221ClubRankStats={hits:0,misses:0,prewarms:0,invalidations:0});}",
        "cache de clubes hoisted",
    )
    for old, new in (
        ("v18221ClubRankStats.hits++", "v18221Stats().hits++"),
        ("v18221ClubRankStats.misses++", "v18221Stats().misses++"),
        ("v18221ClubRankStats.prewarms++", "v18221Stats().prewarms++"),
        ("v18221ClubRankStats.invalidations++", "v18221Stats().invalidations++"),
        ("stats:v18221ClubRankStats,", "get stats(){return v18221Stats();},"),
    ):
        if old not in html:
            fail("uso antigo do cache ausente: " + old)
        html = html.replace(old, new)

    marker_pos = html.find("FUTBR_SCORERS_IN_SCOPE_18220_START")
    script_open = html.rfind("<script", 0, marker_pos)
    script_tag_end = html.find(">", script_open)
    script_close = html.find("</script>", marker_pos)
    if min(marker_pos, script_open, script_tag_end, script_close) < 0:
        fail("script principal dos rankings nao localizado")

    bootstrap = r'''
/* FUTBR_RANKINGS_EARLY_API_18222 */
window.GestorFC=window.GestorFC||{};
window.GestorFC.scorersInScope18220={version:'18.220',sameEngineScope:true,earlyApi:true,renderWith:(s,f)=>v18220RankingsPage(s,f),collectWith:(s,f)=>v18220Collect(s,f)};
window.GestorFC.clubRankingCache18221={version:'18.221',boundedSingleSnapshot:true,idlePrewarm:true,dayRevisionKey:true,preservesRankingMethodology:true,earlyApi:true,get stats(){return v18221Stats();},invalidate:v18221InvalidateClubRanking,probe:(key,factory)=>v18221ClubRankCached('__probe__',String(key),factory,false)};
'''
    html = html[: script_tag_end + 1] + bootstrap + html[script_tag_end + 1 :]

    for marker in (
        "FUTBR_RANKINGS_EARLY_API_18222",
        "earlyApi:true",
        "function v18221Stats()",
        "get stats(){return v18221Stats();}",
    ):
        if marker not in html:
            fail("marcador early API ausente: " + marker)

    index_path.write_text(html, encoding="utf-8")
    print("Early in-scope rankings API 18.222 installed")


if __name__ == "__main__":
    main()
