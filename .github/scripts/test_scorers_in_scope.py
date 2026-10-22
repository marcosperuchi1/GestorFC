from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path


def find_browser() -> str | None:
    candidates: list[Path] = []
    for executable in ("chrome", "chrome.exe", "msedge", "msedge.exe", "chromium", "chromium.exe"):
        found = shutil.which(executable)
        if found:
            candidates.append(Path(found))
    for env_name in ("PROGRAMFILES", "ProgramFiles", "PROGRAMFILES(X86)", "ProgramFiles(x86)", "LOCALAPPDATA", "LocalAppData"):
        base = os.environ.get(env_name)
        if not base:
            continue
        root = Path(base)
        candidates.extend(
            [
                root / "Google" / "Chrome" / "Application" / "chrome.exe",
                root / "Microsoft" / "Edge" / "Application" / "msedge.exe",
            ]
        )
    candidates.extend([Path("/usr/bin/chromium"), Path("/usr/bin/google-chrome"), Path("/usr/bin/microsoft-edge")])
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


def fail(message: str) -> None:
    raise RuntimeError(message)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: test_scorers_in_scope.py <project-dir>")

    project = Path(sys.argv[1]).resolve()
    html_path = project / "src" / "index.html"
    html = html_path.read_text(encoding="utf-8")

    required = [
        "FUTBR_SCORERS_IN_SCOPE_18220_START",
        "sameEngineScope:true",
        "data-v18220-rankings-page",
        "data-v18220-scorers-root",
        "FUTBR_RANKING_CACHE_18221_START",
        "boundedSingleSnapshot:true",
        "idlePrewarm:true",
        "window.v18198EnforceInitialSquads=v18198EnforceInitialSquads",
        "else if(view==='clubrankings')v18220PageHTML=v18221ClubRankPage()",
    ]
    for marker in required:
        if marker not in html:
            fail("marcador in-scope ausente: " + marker)

    forbidden_ids = [
        "futbr-final-integrity-18198",
        "futbr-terminal-scorers-18199",
        "futbr-terminal-scorers-18202",
        "futbr-terminal-scorers-18203",
        "futbr-scorers-root-18210",
        "futbr-scorers-render-root-18211",
    ]
    for script_id in forbidden_ids:
        if f'id="{script_id}"' in html or f"id='{script_id}'" in html:
            fail("camada externa antiga ainda executavel: " + script_id)

    marker_pos = html.find("FUTBR_SCORERS_IN_SCOPE_18220_START")
    script_open = html.rfind("<script", 0, marker_pos)
    script_close = html.find("</script>", marker_pos)
    if min(marker_pos, script_open, script_close) < 0 or not script_open < marker_pos < script_close:
        fail("Artilheiros 18.220 nao esta dentro do script principal")

    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        raise RuntimeError("Playwright nao instalado") from exc

    browser_path = find_browser()
    if not browser_path:
        fail("Chrome/Edge/Chromium nao encontrado")

    page_errors: list[str] = []
    console_errors: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=browser_path,
            headless=True,
            args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"],
        )
        page = browser.new_page(viewport={"width": 1600, "height": 900})
        page.on("pageerror", lambda error: page_errors.append(str(error)))
        page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
        page.set_content(html, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(2500)

        result = page.evaluate(
            """
            () => {
              const scorerApi=window.GestorFC?.scorersInScope18220;
              const clubApi=window.GestorFC?.clubRankingCache18221;
              if(!scorerApi||typeof scorerApi.renderWith!=='function')return {ok:false,error:'API 18.220 ausente',scorerApi:typeof scorerApi};
              if(!clubApi||typeof clubApi.probe!=='function')return {ok:false,error:'API cache 18.221 ausente',clubApi:typeof clubApi};
              const filter={kind:'all',country:'all',division:'all',year:'',query:'',nationality:'all',page:0};
              const state={
                year:2026,day:11,seasonDone:false,user:'t0',
                players:{
                  p1:{id:'p1',name:'Artilheiro Real',natCode:'BRA',clubId:'t0',goals:5,assists:2,apps:8,minutes:700},
                  p2:{id:'p2',name:'Segundo Goleador',natCode:'ARG',clubId:'t1',goals:3,assists:1,apps:8,minutes:650}
                },
                teams:[
                  {id:'t0',name:'Flamengo Teste',short:'FLA',country:'bra',roster:['p1'],academy:[],proReserve:[],lineup:['p1']},
                  {id:'t1',name:'Rival Teste',short:'RIV',country:'arg',roster:['p2'],academy:[],proReserve:[],lineup:['p2']}
                ],
                competitions:{},allTimeStats:{},scorerArchive:[],v640National:null,
                competitionStats:{
                  'league:bra:1':{
                    p1:{name:'Artilheiro Real',natCode:'BRA',goals:5,assists:2,apps:8,minutes:700,clubs:{t0:'Flamengo Teste'}},
                    p2:{playerId:'p2',name:'Segundo Goleador',natCode:'ARG',goals:3,assists:1,apps:8,minutes:650,clubs:{t1:'Rival Teste'}}
                  }
                }
              };
              const live=scorerApi.renderWith(state,filter);
              state.day=12;state.competitionStats['league:bra:1'].p1.goals=6;
              const updated=scorerApi.renderWith(state,{...filter});
              const archived={...state,day:156,seasonDone:true,competitionStats:{},scorerArchive:[{year:2026,competitions:{'league:bra:1':{p1:{id:'p1',name:'Artilheiro Real',natCode:'BRA',goals:18,assists:7,apps:30,minutes:2500,clubs:{t0:'Flamengo Teste'}}}}}]};
              const archive=scorerApi.renderWith(archived,{...filter});

              let calls=0;
              const first=clubApi.probe('journey-11',()=>{calls++;return '<div>RANK-A</div>';});
              const second=clubApi.probe('journey-11',()=>{calls++;return '<div>RANK-B</div>';});
              const third=clubApi.probe('journey-12',()=>{calls++;return '<div>RANK-C</div>';});

              const capPlayers={},capRoster=[];
              for(let i=0;i<40;i++){const id='x'+i;capPlayers[id]={id,age:i>=32?18:25,squad:i>=32?'youth':'senior',clubId:'x'};capRoster.push(id);}
              const capState={year:2026,players:capPlayers,teams:[{id:'x',roster:capRoster,academy:[],proReserve:[],lineup:capRoster.slice(0,11)}]};
              const cap=window.v18198EnforceInitialSquads(capState);

              return {
                ok:true,
                scorerApiVersion:scorerApi.version,
                cacheApiVersion:clubApi.version,
                hasTabs:live.includes('v677-ranking-tabs')&&live.includes('Artilheiros')&&live.includes('Clubes'),
                hasTitle:live.includes('Ranking de Artilheiros'),
                livePlayers:live.includes('Artilheiro Real')&&live.includes('Segundo Goleador'),
                liveGoals:live.includes('green strong\">5</td>'),
                updatedGoals:updated.includes('green strong\">6</td>'),
                archivedGoals:archive.includes('green strong\">18</td>'),
                emptyMessage:live.includes('Nenhum artilheiro registrado'),
                cacheCalls:calls,
                cacheSame:first===second,
                cacheChanged:third!==second,
                cacheHits:clubApi.stats.hits,
                cacheMisses:clubApi.stats.misses,
                roster:capState.teams[0].roster.length,
                academy:capState.teams[0].academy.length,
                capMax:cap.max
              };
            }
            """
        )
        browser.close()

    checks = {
        "api": result.get("ok") is True,
        "tabs": result.get("hasTabs") is True,
        "title": result.get("hasTitle") is True,
        "livePlayers": result.get("livePlayers") is True,
        "liveGoals": result.get("liveGoals") is True,
        "updatedGoals": result.get("updatedGoals") is True,
        "archivedGoals": result.get("archivedGoals") is True,
        "notEmpty": result.get("emptyMessage") is False,
        "cacheOneComputationPerKey": result.get("cacheCalls") == 2 and result.get("cacheSame") is True and result.get("cacheChanged") is True,
        "seniorCap": result.get("roster") == 32 and result.get("capMax") == 32,
    }
    result["checks"] = checks
    result["browser"] = browser_path
    result["mainScriptScope"] = True
    result["pageErrorCount"] = len(page_errors)
    result["consoleErrorCount"] = len(console_errors)
    result["ok"] = all(checks.values())

    output = project / "scorers-in-scope-tests.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    if not result["ok"]:
        fail("Teste real in-scope falhou: " + json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
