from __future__ import annotations
import re, sys
from pathlib import Path

def fail(msg):
    raise RuntimeError(msg)

def once(text, old, new, label):
    if old not in text:
        fail(label + ": ancora nao encontrada")
    return text.replace(old, new, 1)

def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: add_relational_history_storage.py <project-dir>")
    project = Path(sys.argv[1]).resolve()
    lib_path = project / "src-tauri" / "src" / "lib.rs"
    index_path = project / "src" / "index.html"
    lib = lib_path.read_text(encoding="utf-8")
    html = index_path.read_text(encoding="utf-8")

    if "fn history_store_season(" in lib:
        print("relational history already present")
        return

    structs = r"""
#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
struct HistoryStatWrite {
    player_id: String,
    season: i64,
    competition_id: String,
    club_id: Option<String>,
    apps: i64,
    starts: i64,
    minutes: i64,
    goals: i64,
    assists: i64,
    yellow: i64,
    red: i64,
}

#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
struct HistoryClubStatWrite {
    player_id: String,
    season: i64,
    club_id: String,
    apps: i64,
    goals: i64,
    assists: i64,
    yellow: i64,
    red: i64,
}

#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
struct HistoryTransferWrite {
    player_id: String,
    season: i64,
    from_club_id: Option<String>,
    to_club_id: Option<String>,
    day: Option<i64>,
    fee: Option<f64>,
}

#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
struct HistoryRetirementWrite {
    player_id: String,
    season: i64,
    day: Option<i64>,
    club_id: Option<String>,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct HistoryTotalsRow {
    player_id: String,
    apps: i64,
    starts: i64,
    minutes: i64,
    goals: i64,
    assists: i64,
    yellow: i64,
    red: i64,
}

fn ensure_history_schema(conn: &Connection) -> Result<(), String> {
    conn.execute_batch(r#"
        CREATE TABLE IF NOT EXISTS history_seasons(
            season INTEGER PRIMARY KEY,
            closed_at INTEGER NOT NULL DEFAULT (unixepoch('now')*1000)
        );
        CREATE TABLE IF NOT EXISTS player_season_stats(
            player_id TEXT NOT NULL,
            season INTEGER NOT NULL,
            competition_id TEXT NOT NULL,
            club_id TEXT,
            apps INTEGER NOT NULL DEFAULT 0,
            starts INTEGER NOT NULL DEFAULT 0,
            minutes INTEGER NOT NULL DEFAULT 0,
            goals INTEGER NOT NULL DEFAULT 0,
            assists INTEGER NOT NULL DEFAULT 0,
            yellow INTEGER NOT NULL DEFAULT 0,
            red INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY(player_id,season,competition_id,club_id)
        );
        CREATE INDEX IF NOT EXISTS idx_pss_player_season ON player_season_stats(player_id,season);
        CREATE INDEX IF NOT EXISTS idx_pss_comp_season ON player_season_stats(competition_id,season);
        CREATE INDEX IF NOT EXISTS idx_pss_club_season ON player_season_stats(club_id,season);
        CREATE TABLE IF NOT EXISTS player_club_season(
            player_id TEXT NOT NULL,
            season INTEGER NOT NULL,
            club_id TEXT NOT NULL,
            apps INTEGER NOT NULL DEFAULT 0,
            goals INTEGER NOT NULL DEFAULT 0,
            assists INTEGER NOT NULL DEFAULT 0,
            yellow INTEGER NOT NULL DEFAULT 0,
            red INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY(player_id,season,club_id)
        );
        CREATE INDEX IF NOT EXISTS idx_pcs_player_season ON player_club_season(player_id,season);
        CREATE INDEX IF NOT EXISTS idx_pcs_club_season ON player_club_season(club_id,season);
        CREATE TABLE IF NOT EXISTS player_career_totals(
            player_id TEXT PRIMARY KEY,
            apps INTEGER NOT NULL DEFAULT 0,
            starts INTEGER NOT NULL DEFAULT 0,
            minutes INTEGER NOT NULL DEFAULT 0,
            goals INTEGER NOT NULL DEFAULT 0,
            assists INTEGER NOT NULL DEFAULT 0,
            yellow INTEGER NOT NULL DEFAULT 0,
            red INTEGER NOT NULL DEFAULT 0,
            updated_at INTEGER NOT NULL DEFAULT (unixepoch('now')*1000)
        );
        CREATE TABLE IF NOT EXISTS transfer_history(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id TEXT NOT NULL,
            season INTEGER NOT NULL,
            from_club_id TEXT,
            to_club_id TEXT,
            day INTEGER,
            fee REAL
        );
        CREATE INDEX IF NOT EXISTS idx_transfer_player_season ON transfer_history(player_id,season);
        CREATE TABLE IF NOT EXISTS retirement_history(
            player_id TEXT NOT NULL,
            season INTEGER NOT NULL,
            day INTEGER,
            club_id TEXT,
            PRIMARY KEY(player_id,season)
        );
        CREATE INDEX IF NOT EXISTS idx_retirement_season ON retirement_history(season);
    "#).map_err(|e| e.to_string())
}
"""
    lib = once(
        lib,
        "struct DesktopDb(Mutex<Connection>);",
        "struct DesktopDb(Mutex<Connection>);\n" + structs,
        "history structs",
    )

    commands = r"""
#[tauri::command]
fn history_store_season(
    season: i64,
    stats: Vec<HistoryStatWrite>,
    club_stats: Vec<HistoryClubStatWrite>,
    transfers: Vec<HistoryTransferWrite>,
    retirements: Vec<HistoryRetirementWrite>,
    db: State<'_, DesktopDb>,
) -> Result<(), String> {
    let mut conn = db.0.lock().map_err(|_| "Banco ocupado".to_string())?;
    ensure_history_schema(&conn)?;
    let tx = conn.transaction().map_err(|e| e.to_string())?;
    tx.execute("INSERT OR REPLACE INTO history_seasons(season,closed_at) VALUES(?1,unixepoch('now')*1000)", params![season]).map_err(|e| e.to_string())?;
    tx.execute("DELETE FROM player_season_stats WHERE season=?1", params![season]).map_err(|e| e.to_string())?;
    tx.execute("DELETE FROM player_club_season WHERE season=?1", params![season]).map_err(|e| e.to_string())?;
    tx.execute("DELETE FROM transfer_history WHERE season=?1", params![season]).map_err(|e| e.to_string())?;
    tx.execute("DELETE FROM retirement_history WHERE season=?1", params![season]).map_err(|e| e.to_string())?;

    {
        let mut stmt = tx.prepare(
            "INSERT INTO player_season_stats(player_id,season,competition_id,club_id,apps,starts,minutes,goals,assists,yellow,red)
             VALUES(?1,?2,?3,?4,?5,?6,?7,?8,?9,?10,?11)"
        ).map_err(|e| e.to_string())?;
        for x in &stats {
            stmt.execute(params![
                x.player_id,x.season,x.competition_id,x.club_id,
                x.apps,x.starts,x.minutes,x.goals,x.assists,x.yellow,x.red
            ]).map_err(|e| e.to_string())?;
        }
    }

    {
        let mut stmt = tx.prepare(
            "INSERT INTO player_club_season(player_id,season,club_id,apps,goals,assists,yellow,red)
             VALUES(?1,?2,?3,?4,?5,?6,?7,?8)"
        ).map_err(|e| e.to_string())?;
        for x in &club_stats {
            stmt.execute(params![x.player_id,x.season,x.club_id,x.apps,x.goals,x.assists,x.yellow,x.red]).map_err(|e| e.to_string())?;
        }
    }

    {
        let mut stmt = tx.prepare(
            "INSERT INTO transfer_history(player_id,season,from_club_id,to_club_id,day,fee)
             VALUES(?1,?2,?3,?4,?5,?6)"
        ).map_err(|e| e.to_string())?;
        for x in &transfers {
            stmt.execute(params![x.player_id,x.season,x.from_club_id,x.to_club_id,x.day,x.fee]).map_err(|e| e.to_string())?;
        }
    }

    {
        let mut stmt = tx.prepare(
            "INSERT OR REPLACE INTO retirement_history(player_id,season,day,club_id)
             VALUES(?1,?2,?3,?4)"
        ).map_err(|e| e.to_string())?;
        for x in &retirements {
            stmt.execute(params![x.player_id,x.season,x.day,x.club_id]).map_err(|e| e.to_string())?;
        }
    }

    tx.execute("DELETE FROM player_career_totals", []).map_err(|e| e.to_string())?;
    tx.execute(
        "INSERT INTO player_career_totals(player_id,apps,starts,minutes,goals,assists,yellow,red,updated_at)
         SELECT player_id,SUM(apps),SUM(starts),SUM(minutes),SUM(goals),SUM(assists),SUM(yellow),SUM(red),unixepoch('now')*1000
         FROM player_season_stats GROUP BY player_id",
        []
    ).map_err(|e| e.to_string())?;

    tx.commit().map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
fn history_player_totals(
    player_id: String,
    db: State<'_, DesktopDb>,
) -> Result<Option<HistoryTotalsRow>, String> {
    let conn = db.0.lock().map_err(|_| "Banco ocupado".to_string())?;
    ensure_history_schema(&conn)?;
    let mut stmt = conn.prepare(
        "SELECT player_id,apps,starts,minutes,goals,assists,yellow,red
         FROM player_career_totals WHERE player_id=?1"
    ).map_err(|e| e.to_string())?;
    let mut rows = stmt.query(params![player_id]).map_err(|e| e.to_string())?;
    if let Some(row) = rows.next().map_err(|e| e.to_string())? {
        Ok(Some(HistoryTotalsRow {
            player_id: row.get(0).map_err(|e| e.to_string())?,
            apps: row.get(1).map_err(|e| e.to_string())?,
            starts: row.get(2).map_err(|e| e.to_string())?,
            minutes: row.get(3).map_err(|e| e.to_string())?,
            goals: row.get(4).map_err(|e| e.to_string())?,
            assists: row.get(5).map_err(|e| e.to_string())?,
            yellow: row.get(6).map_err(|e| e.to_string())?,
            red: row.get(7).map_err(|e| e.to_string())?,
        }))
    } else {
        Ok(None)
    }
}


#[tauri::command]
fn history_player_seasons(
    player_id: String,
    db: State<'_, DesktopDb>,
) -> Result<Vec<serde_json::Value>, String> {
    let conn = db.0.lock().map_err(|_| "Banco ocupado".to_string())?;
    ensure_history_schema(&conn)?;
    let mut stmt = conn.prepare(
        "SELECT season,competition_id,club_id,apps,starts,minutes,goals,assists,yellow,red
         FROM player_season_stats WHERE player_id=?1
         ORDER BY season DESC,competition_id ASC"
    ).map_err(|e| e.to_string())?;
    let rows = stmt.query_map(params![player_id], |row| {
        Ok(serde_json::json!({
            "season":row.get::<_,i64>(0)?,
            "competitionId":row.get::<_,String>(1)?,
            "clubId":row.get::<_,Option<String>>(2)?,
            "apps":row.get::<_,i64>(3)?,
            "starts":row.get::<_,i64>(4)?,
            "minutes":row.get::<_,i64>(5)?,
            "goals":row.get::<_,i64>(6)?,
            "assists":row.get::<_,i64>(7)?,
            "yellow":row.get::<_,i64>(8)?,
            "red":row.get::<_,i64>(9)?
        }))
    }).map_err(|e| e.to_string())?;
    rows.collect::<Result<Vec<_>,_>>().map_err(|e| e.to_string())
}

#[tauri::command]
fn history_player_club_seasons(
    player_id: String,
    db: State<'_, DesktopDb>,
) -> Result<Vec<serde_json::Value>, String> {
    let conn = db.0.lock().map_err(|_| "Banco ocupado".to_string())?;
    ensure_history_schema(&conn)?;
    let mut stmt = conn.prepare(
        "SELECT season,club_id,apps,goals,assists,yellow,red
         FROM player_club_season WHERE player_id=?1
         ORDER BY season DESC,club_id ASC"
    ).map_err(|e| e.to_string())?;
    let rows=stmt.query_map(params![player_id],|row|{
        Ok(serde_json::json!({
            "year":row.get::<_,i64>(0)?,
            "teamId":row.get::<_,String>(1)?,
            "apps":row.get::<_,i64>(2)?,
            "goals":row.get::<_,i64>(3)?,
            "assists":row.get::<_,i64>(4)?,
            "yellow":row.get::<_,i64>(5)?,
            "red":row.get::<_,i64>(6)?
        }))
    }).map_err(|e|e.to_string())?;
    rows.collect::<Result<Vec<_>,_>>().map_err(|e|e.to_string())
}

#[tauri::command]
fn history_competition_ranking(
    season: i64,
    competition_id: String,
    limit: Option<i64>,
    db: State<'_, DesktopDb>,
) -> Result<Vec<serde_json::Value>, String> {
    let conn = db.0.lock().map_err(|_| "Banco ocupado".to_string())?;
    ensure_history_schema(&conn)?;
    let take=limit.unwrap_or(150).clamp(1,1000);
    let mut stmt = conn.prepare(
        "SELECT player_id,club_id,apps,minutes,goals,assists,yellow,red
         FROM player_season_stats
         WHERE season=?1 AND competition_id=?2
         ORDER BY goals DESC,assists DESC,minutes ASC,player_id ASC
         LIMIT ?3"
    ).map_err(|e| e.to_string())?;
    let rows = stmt.query_map(params![season,competition_id,take], |row| {
        Ok(serde_json::json!({
            "playerId":row.get::<_,String>(0)?,
            "clubId":row.get::<_,Option<String>>(1)?,
            "apps":row.get::<_,i64>(2)?,
            "minutes":row.get::<_,i64>(3)?,
            "goals":row.get::<_,i64>(4)?,
            "assists":row.get::<_,i64>(5)?,
            "yellow":row.get::<_,i64>(6)?,
            "red":row.get::<_,i64>(7)?
        }))
    }).map_err(|e| e.to_string())?;
    rows.collect::<Result<Vec<_>,_>>().map_err(|e| e.to_string())
}

#[tauri::command]
fn history_database_info(db: State<'_, DesktopDb>) -> Result<serde_json::Value, String> {
    let conn = db.0.lock().map_err(|_| "Banco ocupado".to_string())?;
    ensure_history_schema(&conn)?;
    let seasons:i64=conn.query_row("SELECT COUNT(*) FROM history_seasons",[],|r|r.get(0)).map_err(|e|e.to_string())?;
    let stats:i64=conn.query_row("SELECT COUNT(*) FROM player_season_stats",[],|r|r.get(0)).map_err(|e|e.to_string())?;
    let players:i64=conn.query_row("SELECT COUNT(*) FROM player_career_totals",[],|r|r.get(0)).map_err(|e|e.to_string())?;
    let transfers:i64=conn.query_row("SELECT COUNT(*) FROM transfer_history",[],|r|r.get(0)).map_err(|e|e.to_string())?;
    let retirements:i64=conn.query_row("SELECT COUNT(*) FROM retirement_history",[],|r|r.get(0)).map_err(|e|e.to_string())?;
    Ok(serde_json::json!({"seasons":seasons,"statRows":stats,"players":players,"transfers":transfers,"retirements":retirements}))
}
"""
    lib = once(
        lib,
        "#[tauri::command]\nfn desktop_info",
        commands + "\n#[tauri::command]\nfn desktop_info",
        "history commands",
    )
    lib = once(
        lib,
        "            kv_put_many,\n            open_external_url,",
        "            kv_put_many,\n            history_store_season,\n            history_player_totals,\n            history_player_seasons,\n            history_player_club_seasons,\n            history_competition_ranking,\n            history_database_info,\n            open_external_url,",
        "history handlers",
    )

    bridge = r"""
<script id="futbr-relational-history-bridge">
(()=>{
 if(!window.FutBRDesktop?.available)return;
 const G=window.GestorFC=window.GestorFC||{};
 window.FutBRDesktop.storeHistorySeason=(payload)=>window.__TAURI__.core.invoke('history_store_season',payload||{});
 window.FutBRDesktop.playerHistoryTotals=(playerId)=>window.__TAURI__.core.invoke('history_player_totals',{playerId:String(playerId)});
 window.FutBRDesktop.playerHistorySeasons=(playerId)=>window.__TAURI__.core.invoke('history_player_seasons',{playerId:String(playerId)});
 window.FutBRDesktop.playerClubHistory=(playerId)=>window.__TAURI__.core.invoke('history_player_club_seasons',{playerId:String(playerId)});
 window.FutBRDesktop.competitionHistoryRanking=(season,competitionId,limit=150)=>window.__TAURI__.core.invoke('history_competition_ranking',{season:Number(season),competitionId:String(competitionId),limit:Number(limit)||150});
 window.FutBRDesktop.historyDatabaseInfo=()=>window.__TAURI__.core.invoke('history_database_info');

 const status={version:'19.0-shadow-v2',mode:'shadow-validation',engine:'sqlite-rusqlite',authoritative:false,lastSeason:null,lastRows:0,lastMs:0,lastError:null};
 const careerCache=new Map(),careerLoading=new Map(),careerEmpty=new Set();
 async function hydratePlayerCareer(pid){
  pid=String(pid||'');if(!pid)return [];
  if(careerCache.has(pid))return careerCache.get(pid);
  if(careerLoading.has(pid))return careerLoading.get(pid);
  const p=window.FutBRDesktop.playerClubHistory(pid).then(rows=>{
   const out=(rows||[]).map(r=>({...r,teamName:E.team(state,r.teamId)?.name||r.teamId,scope:'club',legacy:false,clubIds:[r.teamId]}));
   careerLoading.delete(pid);
   if(out.length){careerCache.set(pid,out);careerEmpty.delete(pid);}else{careerCache.delete(pid);careerEmpty.add(pid);}
   return out;
  }).catch(e=>{careerLoading.delete(pid);console.warn('[FutBR] leitura relacional da carreira:',e);return [];});
  careerLoading.set(pid,p);return p;
 }

 function n(v){const x=Number(v);return Number.isFinite(x)?x:0;}
 function seasonPayload(s,year){
  const archive=(s?.scorerArchive||[]).find(a=>Number(a?.year)===Number(year));
  const stats=[];
  for(const [competitionId,db] of Object.entries(archive?.competitions||{})){
   for(const [pid,row] of Object.entries(db||{})){
    stats.push({
     playerId:String(row?.id||pid),season:Number(year),competitionId:String(competitionId),clubId:null,
     apps:n(row?.apps),starts:0,minutes:n(row?.minutes),goals:n(row?.goals),assists:n(row?.assists),yellow:0,red:0
    });
   }
  }
  const clubStats=[];
  const packed=s?.v555CareerArchive?.[year];
  if(packed?.p){
   for(const pid of Object.keys(packed.p)){
    const rows=typeof v555PackedRows==='function'?v555PackedRows(s,year,pid):[];
    for(const r of rows)if(r?.teamId)clubStats.push({playerId:String(pid),season:Number(year),clubId:String(r.teamId),apps:n(r.apps),goals:n(r.goals),assists:n(r.assists),yellow:n(r.yellow),red:n(r.red)});
   }
  }else{
   for(const [pid,rows] of Object.entries(s?.v538CareerArchive?.[year]||{}))for(const r of rows||[])if(r?.teamId)clubStats.push({playerId:String(pid),season:Number(year),clubId:String(r.teamId),apps:n(r.apps),goals:n(r.goals),assists:n(r.assists),yellow:n(r.yellow),red:n(r.red)});
  }
    const transfers=(s?.transfers||[]).filter(x=>Number(x?.year)===Number(year)).map(x=>({
   playerId:String(x?.id||x?.playerId||''),season:Number(year),
   fromClubId:x?.from==null?null:String(x.from),toClubId:x?.to==null?null:String(x.to),
   day:Number.isFinite(Number(x?.day))?Number(x.day):null,fee:Number.isFinite(Number(x?.fee))?Number(x.fee):null
  })).filter(x=>x.playerId);
  const retirements=(s?.retirements||[]).filter(x=>Number(x?.year)===Number(year)).map(x=>({
   playerId:String(x?.id||x?.playerId||x||''),season:Number(year),
   day:Number.isFinite(Number(x?.day))?Number(x.day):null,clubId:x?.clubId==null?null:String(x.clubId)
  })).filter(x=>x.playerId&&x.playerId!=='[object Object]');
  return {season:Number(year),stats,clubStats,transfers,retirements};
 }
 async function mirrorSeason(s,year){
  if(!s||!Number.isFinite(Number(year)))return false;
  const payload=seasonPayload(s,year),t=performance.now();
  if(!payload.stats.length&&!payload.clubStats.length)return false;
  try{
   await window.FutBRDesktop.storeHistorySeason(payload);
   status.lastSeason=Number(year);status.lastRows=payload.stats.length;status.lastMs=Math.round(performance.now()-t);status.lastError=null;
   return true;
  }catch(e){status.lastError=String(e?.message||e);console.warn('[FutBR] histórico relacional:',e);return false;}
 }
 const baseCareerRows=v539CareerRows;
 v539CareerRows=function(pid){
  const cached=careerCache.get(String(pid||''));
  if(!cached)return baseCareerRows(pid);
  const live=baseCareerRows(pid).filter(r=>r?.scope==='national'||Number(r?.year)===Number(state?.year));
  const rows=[],seen=new Set();
  for(const r of [...cached,...live]){
   const k=[r?.scope||'club',r?.year,r?.teamId||r?.teamCode||''].join('|');
   if(seen.has(k))continue;seen.add(k);rows.push(r);
  }
  return rows.sort((a,b)=>b.year-a.year||(a.scope===b.scope?String(a.teamName||'').localeCompare(String(b.teamName||''),'pt-BR'):(a.scope==='club'?-1:1)));
 };
 v538CareerRows=v539CareerRows;
 document.addEventListener('click',async e=>{
  const btn=e.target?.closest?.('[data-action="player"][data-player]');
  if(!btn||btn.dataset.v190RelationalReplay==='1')return;
  const pid=String(btn.dataset.player||'');
  if(!pid||careerCache.has(pid)||careerEmpty.has(pid))return;
  e.preventDefault();e.stopImmediatePropagation();
  await hydratePlayerCareer(pid);
  btn.dataset.v190RelationalReplay='1';
  try{btn.click();}finally{delete btn.dataset.v190RelationalReplay;}
 },true);

 const baseNextSeason=E.nextSeason;
 E.nextSeason=function(s,...args){
  const closed=s?.seasonDone?Number(s.year):null;
  const out=baseNextSeason(s,...args);
  if(Number.isFinite(closed))setTimeout(()=>mirrorSeason(out||s,closed),1200);
  return out;
 };
 G.relationalHistory={...status,mirrorSeason:(year)=>mirrorSeason(state,Number(year)),hydratePlayerCareer,status:()=>({...status,careerCachePlayers:careerCache.size,careerEmptyPlayers:careerEmpty.size})};
})();
</script>
"""
    if 'futbr-relational-history-bridge' not in html:
        html = once(html, "</body>", bridge + "\n</body>", "history bridge")

    # Final document-boundary cleanup. Literal backslash-n sequences between
    # HTML tags become visible text nodes in WebView2 (the "\\n" seen on blank boot).
    # Match the two literal characters backslash+n between HTML tags.
    # The prior pattern was over-escaped and therefore missed the visible "\\n".
    html = re.sub(r'(?<=>)\\\\n(?=\\s*<)', '\n', html)

    lib_path.write_text(lib, encoding="utf-8")
    index_path.write_text(html, encoding="utf-8")
    print("relational history storage added")

if __name__ == "__main__":
    main()
