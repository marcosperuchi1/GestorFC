from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: test_player_career_timeline_18339.py <project-dir>")
    root = Path(sys.argv[1])
    src = (root / "src" / "index.html").read_text(encoding="utf-8")
    if "FUTBR_CAREER_NO_PHANTOM_CLUBS_18339" not in src:
        raise RuntimeError("New timeline filter not present")
    for needle in (
        "for(const [year,ids] of timeline)for(const tid of ids)if(tid)rows.push({year:Number(year),teamId:tid",
        "for(const [year,ids] of timeline)for(const tid of ids)if(tid)rows.push({year:Number(year),teamId:tid,teamName:(packed",
    ):
        if needle in src:
            raise RuntimeError("Synthetic club seasons still produced")
    main_scope_end = src.index("window.GestorFC.version='18.155';window.GestorFC.visualVersion='18.155';")
    marker = src.index("/* FUTBR_CAREER_NO_PHANTOM_CLUBS_18339", 0, main_scope_end)
    js = src[marker:main_scope_end]
    test = r"""
const assert=require('node:assert/strict');
const source=[
 {year:2028,teamId:'inter',teamName:'Internacional',apps:18,goals:0,assists:2,yellow:1,red:1},
 {year:2028,teamId:'fla',teamName:'Flamengo',apps:21,goals:2,assists:2,yellow:0,red:0},
 {year:2028,scope:'national',teamCode:'URU',teamName:'Uruguai',apps:10,goals:5,assists:0},
 {year:2027,teamId:'inter',teamName:'Internacional',apps:0,goals:0,assists:0,yellow:0,red:0},
 {year:2027,teamId:'fla',teamName:'Flamengo',apps:36,goals:5,assists:5,yellow:0,red:1},
 {year:2027,scope:'national',teamCode:'URU',teamName:'Uruguai',apps:10,goals:5,assists:1},
 {year:2026,teamId:'inter',teamName:'Internacional',apps:0,goals:0,assists:0,yellow:0,red:0},
 {year:2026,teamId:'fla',teamName:'Flamengo',apps:42,goals:6,assists:7,yellow:4,red:0},
 {year:2026,scope:'national',teamCode:'URU',teamName:'Uruguai',apps:18,goals:1,assists:4},
 {year:2025,teamId:'team1',apps:0,goals:1,assists:0,yellow:0,red:0},
 {year:2024,teamId:'team2',apps:0,goals:0,assists:0,yellow:1,red:0}
];
const before=JSON.stringify(source);
let v539CareerRows=()=>source;
let v538CareerRows=v539CareerRows;
const window={GestorFC:{}};
""" + js + r"""
const rows=v539CareerRows('player-1');
assert.deepEqual(rows.filter(r=>r.teamId==='inter').map(r=>r.year),[2028],
 'No Internacional 2026/2027 if there was no real production');
assert.deepEqual(rows.filter(r=>r.teamId==='fla').map(r=>r.year),[2028,2027,2026],
 'Flamengo registered seasons must be maintained');
assert.equal(rows.filter(r=>r.scope==='national').length,3,
 'National team stats must not be lost');
assert(rows.some(r=>r.teamId==='inter'&&r.year===2028&&r.apps===18&&r.goals===0),
 'Club season with 0 goals but real appearances must remain');
assert(rows.some(r=>r.teamId==='team1'&&r.goals===1),
 'Historical goals without matches still count as recorded production');
assert(rows.some(r=>r.teamId==='team2'&&r.yellow===1),
 'Archived cautions are part of historical statistics');
assert.equal(rows.length,9,'Only two phantom rows should disappear');
assert.equal(JSON.stringify(source),before,'Must not mutate original archives or existing rows');
assert.equal(v538CareerRows,v539CareerRows,'Older player profile must use the fixed list too');
assert(window.GestorFC.careerTimeline18339.noSyntheticClubSeasons);
console.log(JSON.stringify({ok:true,rows:rows.length,historyKept:true,years:[2028,2027,2026]}));
"""
    with tempfile.TemporaryDirectory(prefix="futbr-career-timeline-") as tmp:
        f = Path(tmp) / "check.js"
        f.write_text(test, encoding="utf-8")
        run = subprocess.run(["node", str(f)], capture_output=True, text=True, timeout=30)
        if run.returncode:
            raise RuntimeError("Timeline regression: " + run.stderr)
        payload = json.loads(run.stdout.strip().splitlines()[-1])
        if not payload["ok"]:
            raise RuntimeError("Invalid JS regression output")
    report = {
        "ok": True, "version": "18.339",
        "inter2026And2027Removed": True, "inter2028Preserved": True,
        "flamengo2026To2028Preserved": True, "uruguay2026To2028Preserved": True,
        "midSeasonTransfersPreserved": True, "oldSaveCompatible": True,
        "historicalProductionUntouched": True, "noAllZeroClubRows": True,
        "sourceArchivesUnmodified": True,
    }
    (root / "career-timeline-18339-tests.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
