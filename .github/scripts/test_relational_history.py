from __future__ import annotations
import json, re, subprocess, sys
from pathlib import Path

def die(msg):
    raise RuntimeError(msg)

def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: test_relational_history.py <project-dir>")

    root = Path(sys.argv[1]).resolve()
    html = (root / "src" / "index.html").read_text(encoding="utf-8")
    lib = (root / "src-tauri" / "src" / "lib.rs").read_text(encoding="utf-8")

    m = re.search(r'<script id="futbr-relational-history-bridge">(.*?)</script>', html, re.S)
    if not m:
        die("Bridge relacional nao foi injetado no HTML final")
    bridge = m.group(1)

    rust_markers = [
        "fn history_store_season(",
        "fn history_player_totals(",
        "fn history_player_seasons(",
        "fn history_player_club_seasons(",
        "fn history_competition_ranking(",
        "fn history_database_info(",
        "CREATE TABLE IF NOT EXISTS player_club_season(",
        "PRIMARY KEY(player_id,season,club_id)",
    ]
    for marker in rust_markers:
        if marker not in lib:
            die("Marcador Rust relacional ausente: " + marker)

    handler_match = re.search(r"tauri::generate_handler!\[(.*?)\]", lib, re.S)
    if not handler_match:
        die("invoke_handler do Tauri nao encontrado")
    handler = handler_match.group(1)
    for command in [
        "history_store_season",
        "history_player_totals",
        "history_player_seasons",
        "history_player_club_seasons",
        "history_competition_ranking",
        "history_database_info",
    ]:
        if command not in handler:
            die("Comando relacional nao registrado: " + command)

    js = r"""
const invocations=[];
global.window={
  FutBRDesktop:{available:true},
  __TAURI__:{core:{invoke:async(cmd,args)=>{
    if(cmd==='history_player_club_seasons'){
      return [{year:2025,teamId:'t-old',apps:12,goals:7,assists:6,yellow:2,red:1}];
    }
    if(cmd==='history_store_season'){
      invocations.push({cmd,args});
      return null;
    }
    if(cmd==='history_database_info') return {seasons:1,statRows:1,players:1,transfers:0,retirements:0};
    return null;
  }}}
};
global.document={addEventListener:()=>{}};
global.performance={now:()=>0};
global.setTimeout=()=>0;
global.state={
  year:2026,
  scorerArchive:[{
    year:2025,
    competitions:{
      league:{p1:{id:'p1',apps:9,minutes:700,goals:5,assists:4}}
    }
  }],
  v555CareerArchive:{2025:{p:{p1:1}}},
  transfers:[],
  retirements:[]
};
global.v555PackedRows=(s,year,pid)=>pid==='p1'?[{
  year:2025,teamId:'t-old',apps:12,goals:7,assists:6,yellow:2,red:1
}]:[];
global.v539CareerRows=(pid)=>[
  {scope:'club',year:2026,teamId:'t-now',teamName:'Clube Atual',apps:3,goals:2,assists:1,yellow:0,red:0},
  {scope:'club',year:2025,teamId:'legacy-old',teamName:'Legado Antigo',apps:99,goals:99,assists:99,yellow:9,red:9},
  {scope:'national',year:2025,teamCode:'BRA',teamName:'Brasil',apps:4,goals:1,assists:2,yellow:1,red:0}
];
global.v538CareerRows=global.v539CareerRows;
global.E={
  team:(s,id)=>({name:id==='t-old'?'Clube Antigo':String(id)}),
  nextSeason:(s)=>s
};
"""
    js += "\n" + bridge + "\n"
    js += r"""
(async()=>{
  const before=v539CareerRows('p1');
  if(!before.some(r=>r.teamId==='legacy-old'&&r.goals===99)){
    throw Error('fallback anterior ao SQLite nao preservou a carreira atual');
  }

  const loaded=await window.GestorFC.relationalHistory.hydratePlayerCareer('p1');
  if(!loaded.length) throw Error('SQLite nao retornou carreira encerrada');

  const rows=v539CareerRows('p1');
  const closed=rows.find(r=>r.scope==='club'&&r.year===2025&&r.teamId==='t-old');
  const current=rows.find(r=>r.scope==='club'&&r.year===2026&&r.teamId==='t-now');
  const national=rows.find(r=>r.scope==='national'&&r.year===2025&&r.teamCode==='BRA');

  if(!closed) throw Error('temporada encerrada do SQLite ausente na Carreira global');
  if(closed.apps!==12||closed.goals!==7||closed.assists!==6||closed.yellow!==2||closed.red!==1){
    throw Error('estatisticas encerradas divergiram: '+JSON.stringify(closed));
  }
  if(!current||current.apps!==3||current.goals!==2||current.assists!==1){
    throw Error('temporada atual deixou de usar o estado vivo: '+JSON.stringify(current));
  }
  if(!national||national.apps!==4||national.goals!==1||national.assists!==2){
    throw Error('historico de selecao foi perdido: '+JSON.stringify(national));
  }
  if(rows.some(r=>r.teamId==='legacy-old')){
    throw Error('historico legado encerrado duplicou a linha autoritativa do SQLite');
  }

  const mirrored=await window.GestorFC.relationalHistory.mirrorSeason(2025);
  if(!mirrored) throw Error('espelhamento da temporada encerrada retornou false');
  const write=invocations.find(x=>x.cmd==='history_store_season');
  if(!write) throw Error('history_store_season nao foi chamado');
  const payload=write.args;
  const club=payload.clubStats?.find(x=>x.playerId==='p1'&&x.clubId==='t-old');
  const comp=payload.stats?.find(x=>x.playerId==='p1'&&x.competitionId==='league');
  if(!club||club.apps!==12||club.goals!==7||club.assists!==6||club.yellow!==2||club.red!==1){
    throw Error('payload de clube perdeu estatisticas: '+JSON.stringify(club));
  }
  if(!comp||comp.apps!==9||comp.minutes!==700||comp.goals!==5||comp.assists!==4){
    throw Error('payload por competicao perdeu estatisticas: '+JSON.stringify(comp));
  }

  console.log(JSON.stringify({
    ok:true,
    fallbackBeforeHydration:true,
    rowsAfterHydration:rows.length,
    closedClub:{apps:closed.apps,goals:closed.goals,assists:closed.assists,yellow:closed.yellow,red:closed.red},
    currentClub:{apps:current.apps,goals:current.goals,assists:current.assists},
    national:{apps:national.apps,goals:national.goals,assists:national.assists},
    mirroredClub:{apps:club.apps,goals:club.goals,assists:club.assists,yellow:club.yellow,red:club.red},
    mirroredCompetition:{apps:comp.apps,minutes:comp.minutes,goals:comp.goals,assists:comp.assists}
  }));
})().catch(e=>{console.error(e&&e.stack||e);process.exit(1);});
"""

    tmp = root / ".futbr_relational_history_test.js"
    tmp.write_text(js, encoding="utf-8")
    try:
        run = subprocess.run(["node", str(tmp)], capture_output=True, text=True)
    finally:
        tmp.unlink(missing_ok=True)

    if run.returncode:
        die("Teste JS relacional falhou: " + (run.stderr or run.stdout)[-3000:])

    try:
        result = json.loads(run.stdout.strip().splitlines()[-1])
    except Exception as e:
        die("Saida do teste relacional invalida: " + str(e) + "\n" + run.stdout[-1500:])

    report = {
        "ok": True,
        "source": "final-transformed-index-and-rust",
        "career_global": result,
        "rust_commands_registered": True,
        "sqlite_closed_seasons": True,
        "live_current_season_fallback": True,
        "national_history_fallback": True,
    }
    (root / "relational-history-tests.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False))

if __name__ == "__main__":
    main()
