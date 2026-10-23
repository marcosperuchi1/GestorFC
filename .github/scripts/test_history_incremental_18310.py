from __future__ import annotations
import json, sqlite3, sys, time
from pathlib import Path
from optimize_season_sync_18310 import HISTORY_BEFORE,HISTORY_SUBTRACT,HISTORY_ADD,HISTORY_APPLY

FIELDS='apps,starts,minutes,goals,assists,yellow,red'

def batch(c,sql):
    for statement in sql.split(';'):
        if statement.strip():c.execute(statement)

def test():
    c=sqlite3.connect(':memory:')
    c.executescript('CREATE TABLE player_season_stats(player_id TEXT,season INTEGER,competition_id TEXT,club_id TEXT,'+','.join(f+' INTEGER NOT NULL' for f in FIELDS.split(','))+',PRIMARY KEY(player_id,season,competition_id,club_id)); CREATE INDEX old_player_idx ON player_season_stats(player_id,season); CREATE TABLE player_career_totals(player_id TEXT PRIMARY KEY,'+','.join(f+' INTEGER NOT NULL' for f in FIELDS.split(','))+',updated_at INTEGER);')
    def store(year,rows,fail=False):
        with c:
            batch(c,HISTORY_BEFORE)
            c.execute(HISTORY_SUBTRACT,(year,))
            c.execute('DELETE FROM player_season_stats WHERE season=?',(year,))
            c.executemany('INSERT INTO player_season_stats VALUES('+','.join(['?']*11)+')',rows)
            c.execute(HISTORY_ADD,(year,))
            batch(c,HISTORY_APPLY)
            if fail:raise RuntimeError('injected failure before commit')
    def expected():return c.execute('SELECT player_id,'+','.join('SUM('+f+')' for f in FIELDS.split(','))+' FROM player_season_stats GROUP BY player_id ORDER BY player_id').fetchall()
    def actual():return c.execute('SELECT player_id,'+FIELDS+' FROM player_career_totals ORDER BY player_id').fetchall()
    elapsed=[]
    for year in range(2026,2031):
        n=12000 if year<2029 else 24000
        rows=[('p'+str(i),year,'league','club'+str(i%60),i%45,i%39,i%3000,i%37,i%21,i%8,i%3) for i in range(n)]
        rows += [('p'+str(i),year,'cup','club'+str(i%60),8,5,550,3,2,1,0) for i in range(0,n,7)]
        t=time.perf_counter();store(year,rows);elapsed.append({'year':year,'rows':len(rows),'ms':round((time.perf_counter()-t)*1000)})
        assert actual()==expected(),f'Incorrect totals after {year}'
        previous=actual();store(year,rows);assert actual()==previous,'Repeated save double-counted'
    corrected=[('special',2027,'league','new',0,0,0,0,0,0,0),('p3',2027,'league','new',12,8,900,7,9,1,0)]
    store(2027,corrected);assert actual()==expected()
    before=actual();before_stats=c.execute('SELECT * FROM player_season_stats ORDER BY 1,2,3,4').fetchall()
    try:store(2028,[('never-committed',2028,'cup','new',1,1,90,1,0,0,0)],fail=True)
    except RuntimeError:pass
    else:raise AssertionError('Expected simulated storage failure')
    assert actual()==before
    assert c.execute('SELECT * FROM player_season_stats ORDER BY 1,2,3,4').fetchall()==before_stats
    store(2027,[]);assert actual()==expected();assert not any(r[0]=='special' for r in actual())
    return {'ok':True,'scope':'SQLite season-delta integrity, not a Windows gameplay benchmark','cycles':elapsed,'repeatIdempotent':True,'correctedSeasonReplacesOldTotals':True,'rollbackPreservesPreviousData':True,'zeroStatRowsPreserved':True,'emptySeasonSupported':True,'careerTotalsMatchFullRecalculation':True}

if __name__=='__main__':
    result=test()
    if len(sys.argv)>1:
        project=Path(sys.argv[1]);native=(project/'src-tauri/src/lib.rs').read_text(encoding='utf-8')
        assert '#[tauri::command(async)]\nfn history_store_season(' in native
        for sql in [HISTORY_BEFORE,HISTORY_SUBTRACT,HISTORY_ADD,HISTORY_APPLY]:assert sql in native
        assert '"DELETE FROM player_career_totals", []' not in native
        (project/'history-incremental-18310-tests.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
