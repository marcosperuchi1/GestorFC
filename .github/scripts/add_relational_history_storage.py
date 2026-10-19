from __future__ import annotations
import sys
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
    transfers: Vec<HistoryTransferWrite>,
    retirements: Vec<HistoryRetirementWrite>,
    db: State<'_, DesktopDb>,
) -> Result<(), String> {
    let mut conn = db.0.lock().map_err(|_| "Banco ocupado".to_string())?;
    ensure_history_schema(&conn)?;
    let tx = conn.transaction().map_err(|e| e.to_string())?;
    tx.execute("INSERT OR REPLACE INTO history_seasons(season,closed_at) VALUES(?1,unixepoch('now')*1000)", params![season]).map_err(|e| e.to_string())?;
    tx.execute("DELETE FROM player_season_stats WHERE season=?1", params![season]).map_err(|e| e.to_string())?;
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
        "            kv_put_many,\n            history_store_season,\n            history_player_totals,\n            open_external_url,",
        "history handlers",
    )

    bridge = r"""
<script id="futbr-relational-history-bridge">
(()=>{
 if(!window.FutBRDesktop?.available)return;
 window.FutBRDesktop.storeHistorySeason=(payload)=>window.__TAURI__.core.invoke('history_store_season',payload||{});
 window.FutBRDesktop.playerHistoryTotals=(playerId)=>window.__TAURI__.core.invoke('history_player_totals',{playerId:String(playerId)});
 window.GestorFC=window.GestorFC||{};
 window.GestorFC.relationalHistory={
   version:'19.0-shadow-v1',
   mode:'shadow-validation',
   engine:'sqlite-rusqlite',
   authoritative:false
 };
})();
</script>
"""
    if 'futbr-relational-history-bridge' not in html:
        html = once(html, "</body>", bridge + "\n</body>", "history bridge")

    lib_path.write_text(lib, encoding="utf-8")
    index_path.write_text(html, encoding="utf-8")
    print("relational history storage added")

if __name__ == "__main__":
    main()
