from __future__ import annotations

import json
import sys
from pathlib import Path

VERSION = "18.339"
MARK = "FUTBR_CAREER_NO_PHANTOM_CLUBS_18339"

# The 5.39 and 5.55 engines injected a zero-statistical record for every
# apparent club/year in a *heuristic* membership timeline. On a transfer,
# the timeline can project the new club backwards into already closed seasons.
# These two statements were display-only; removing them loses no actual stats.
SYNTHETIC_539 = (
    "for(const [year,ids] of timeline)for(const tid of ids)if(tid)rows.push("
    "{year:Number(year),teamId:tid,teamName:E.team(state,tid)?.name||'Clube não registrado',"
    "apps:0,goals:0,assists:0,yellow:0,red:0,legacy:false,clubIds:[tid]});"
)
SYNTHETIC_555 = (
    "for(const [year,ids] of timeline)for(const tid of ids)if(tid)rows.push("
    "{year:Number(year),teamId:tid,teamName:(packed?.[year]?.n||{})[tid]||"
    "E.team(state,tid)?.name||'Clube não registrado',"
    "apps:0,goals:0,assists:0,yellow:0,red:0,legacy:false,clubIds:[tid]});"
)

FILTER_JS = r'''
/* FUTBR_CAREER_NO_PHANTOM_CLUBS_18339
   Render real season/club production only. Keep archives, SQLite mirrors,
   transfer records and national careers completely untouched.
   Existing saves with synthetic 0/0/0 club seasons are corrected on read.
   A real 0-goal season with one or more appearances remains visible. */
const v18339CareerRowsRaw=v539CareerRows;
function v18339CareerProductionRecorded(row){
 if(!row)return false;
 if(row.scope==='national')return true;
 return Number(row.apps)>0||Number(row.goals)>0||Number(row.assists)>0||
        Number(row.yellow)>0||Number(row.red)>0;
}
v539CareerRows=function(pid){
 const rows=v18339CareerRowsRaw(pid);
 return Array.isArray(rows)?rows.filter(v18339CareerProductionRecorded):[];
};
v538CareerRows=v539CareerRows;
window.GestorFC=window.GestorFC||{};
window.GestorFC.careerTimeline18339={
 version:'18.339',noSyntheticClubSeasons:true,
 rows:pid=>v539CareerRows(pid)
};
'''


def once(html: str, old: str, new: str, what: str) -> str:
    n = html.count(old)
    if n != 1:
        raise RuntimeError(f"18.339 {what}: expected one exact source anchor, found {n}")
    return html.replace(old, new, 1)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: fix_player_career_timeline_18339.py <project-dir>")
    project = Path(sys.argv[1]).resolve()
    path = project / "src" / "index.html"
    html = path.read_text(encoding="utf-8")
    if MARK in html:
        raise RuntimeError("Career fix 18.339 already applied")
    for dep in ("FUTBR_LONG_CAREER_SAVE_18338_BEGIN",
                "FUTBR_CHAMPIONS_RETIREMENT_18322",
                "function v555PackedRows(s,year,pid)"):
        if dep not in html:
            raise RuntimeError("Expected tested career archive base missing: " + dep)
    html = once(html, SYNTHETIC_539, "/* 18.339: no artificial club/year rows */", "5.39 synthetic club rows")
    html = once(html, SYNTHETIC_555, "/* 18.339: no artificial club/year rows */", "5.55 synthetic club rows")
    career_anchor = (
        "window.GestorFC.version='18.155';window.GestorFC.visualVersion='18.155';\n})();\n</script>"
    )
    html = once(html, career_anchor, FILTER_JS + "\n" + career_anchor, "main-career scoped timeline filter")
    path.write_text(html, encoding="utf-8")
    report = {
        "ok": True, "version": VERSION,
        "syntheticEmptyClubYearsRemoved": True, "existingPhantomZeroRowsHidden": True,
        "realSeasonProductionPreserved": True, "multipleClubsSameSeasonPreserved": True,
        "nationalSeasonRowsPreserved": True, "savesModified": False,
        "sqliteHistoricalTotalsModified": False,
    }
    (project / "career-timeline-18339-install.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
