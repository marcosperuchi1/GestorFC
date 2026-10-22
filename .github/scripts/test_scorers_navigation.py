from __future__ import annotations
import json, re, subprocess, sys
from pathlib import Path


def fail(message: str) -> None:
    raise RuntimeError(message)


def extract(html: str, script_id: str) -> str:
    match = re.search(
        rf'<script id="{re.escape(script_id)}">\s*([\s\S]*?)\s*</script>',
        html,
    )
    if not match:
        fail(f"script ausente: {script_id}")
    return match.group(1)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: test_scorers_navigation.py <project-dir>")

    root = Path(sys.argv[1]).resolve()
    html = (root / "src" / "index.html").read_text(encoding="utf-8")
    renderer = extract(html, "futbr-final-integrity-18198")
    navigation = extract(html, "futbr-terminal-scorers-18202")

    required = [
        "postSeasonArchiveFallback:true",
        "allNavigationPaths:true",
        "staleContentObserver:true",
        "persistentIntent:true",
        "window.v18202PaintScorers=v18202Paint",
        "window.v18202EnsureScorers=v18202Ensure",
        "data-v18202-scorers-root",
        "liveHasRows",
        "archived&&(!liveHasRows||!!s.seasonDone)",
        "futbr-terminal-scorers-18203",
        "liveSeason:true",
    ]
    for marker in required:
        if marker not in html:
            fail("marcador de Artilheiros ausente: " + marker)

    old_pos = html.rfind("futbr-terminal-scorers-18199")
    nav_pos = html.rfind("futbr-terminal-scorers-18202")
    live_pos = html.rfind("futbr-terminal-scorers-18203")
    if old_pos < 0 or nav_pos <= old_pos:
        fail("camada 18.202 nao ficou depois da camada antiga")
    if live_pos <= nav_pos:
        fail("camada ao vivo 18.203 nao ficou depois da navegacao 18.202")
    terminal_base = html.rfind("const v18203BaseRenderPage=renderPage")
    terminal_render = html.find("renderPage=function", terminal_base)
    if terminal_base < live_pos or terminal_render < terminal_base:
        fail("wrapper terminal de renderPage 18.203 ausente")
    if html.find("renderPage=function", terminal_render + 1) >= 0:
        fail("outra definicao de renderPage ficou depois da camada 18.203")

    js = r"""
const assert=require('assert');
global.window=global;
global.C=[{id:'bra',name:'Brasil'}];
global.NAT={BRA:['Brasil']};
global.scorerFilter={kind:'all',country:'all',division:'all',year:'',query:'',page:0,nationality:'all'};
global.view='clubrankings';
global.esc=v=>String(v??'').replace(/[&<>\"]/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[ch]));
global.starBadge=()=>'';
global.nation=code=>'<span>'+String(code||'UNK')+'</span>';
global.badge=t=>'<i>'+String(t?.short||t?.name||'')+'</i>';
global.teamButton=t=>'<button>'+String(t?.name||'')+'</button>';
global.v640Flag=code=>'['+code+']';
global.v677RankingTabs=()=>'<nav><button class="v677-ranking-tab" data-view="rankings">Artilheiros</button><button class="v677-ranking-tab" data-view="clubrankings">Clubes</button></nav>';
global.coachesPage=()=>'<div>TECNICOS</div>';
global.E={
 normName:v=>String(v||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase(),
 team:(s,id)=>(s?.teams||[]).find(t=>t.id===id)||null,
 repairLineup:()=>{}
};
global.state={
 year:2026,day:40,lastDay:39,seasonDone:true,user:'t0',
 players:{p1:{id:'p1',name:'Goleador Arquivado',natCode:'BRA',clubId:'t0',pos:'ATA',age:25}},
 teams:[{id:'t0',name:'Clube Teste',short:'CTE',country:'bra',division:1,roster:['p1'],academy:[],proReserve:[],lineup:['p1']}],
 competitions:{},competitionStats:{},allTimeStats:{},v640National:null,
 scorerArchive:[{year:2026,competitions:{'league:bra:1':{p1:{id:'p1',name:'Goleador Arquivado',natCode:'BRA',goals:13,assists:4,apps:18,minutes:1500,clubs:{t0:'Clube Teste'}}}}}]
};

const page={
 innerHTML:'<div>Ranking de Clubes anterior</div>',dataset:{},
 querySelector(selector){return selector.includes('data-v18202-scorers-root')&&this.innerHTML.includes('data-v18202-scorers-root')?{}:null;}
};
const app={};
const listeners={};
global.document={
 documentElement:{},
 querySelector(selector){if(selector==='#v555-page')return page;if(selector==='#app')return app;return null;},
 querySelectorAll(){return [];},
 addEventListener(type,fn){(listeners[type]??=[]).push(fn);}
};
global.MutationObserver=class{constructor(cb){global.__scorerObserver=cb;}observe(){}};
global.requestAnimationFrame=fn=>fn();
global.queueMicrotask=fn=>fn();
global.setTimeout=fn=>{fn();return 1;};
global.renderPage=()=>'<section>Ranking antigo</section>';
global.render=()=>{page.innerHTML='<div>TECNICOS recolocados pelo render antigo</div>';return true;};
global.closeModal=()=>{};
global.scrollTo=()=>{};
""" + renderer + "\n" + navigation + r"""

// No fim do ano, a tela precisa ler scorerArchive mesmo com state.year igual.
const archived=window.v18198ScorersPage();
assert(archived.includes('Goleador Arquivado'),'Artilheiro arquivado nao foi montado');
assert(archived.includes('13'),'Gols arquivados nao foram exibidos');

function target(attrs,text,classes=''){return {
 textContent:text,className:classes,
 getAttribute(name){return attrs[name]??null;},
 closest(){return this;}
};}
function click(node){
 const event={target:node,preventDefault(){this.prevented=true;},stopImmediatePropagation(){this.stopped=true;}};
 for(const fn of listeners.click||[])fn(event);
 return event;
}

// Caminho normal por data-view.
let event=click(target({'data-view':'rankings'},'Artilheiros','v677-ranking-tab'));
assert(event.prevented&&event.stopped,'Clique de Artilheiros nao foi capturado');
assert(page.innerHTML.includes('data-v18202-scorers-root'),'Quadro fisico de Artilheiros nao foi montado');
assert(page.innerHTML.includes('Goleador Arquivado'),'Conteudo arquivado sumiu apos clique');
assert(!page.innerHTML.includes('Ranking de Clubes anterior'),'Quadro anterior continuou visivel');

// Caminho legado identificado apenas pelo texto.
page.innerHTML='<div>SELECOES</div>';view='nationalrankings';
event=click(target({},'Artilheiros','ranking-tab'));
assert(event.prevented&&event.stopped,'Botao legado por texto nao foi capturado');
assert(page.innerHTML.includes('Goleador Arquivado'),'Botao legado nao montou Artilheiros');

// Mesmo que uma rotina antiga altere tambem o view, a intencao persiste.
page.innerHTML='<div>TECNICOS</div>';view='coaches';
global.__scorerObserver();
assert(page.innerHTML.includes('data-v18202-scorers-root'),'Intencao persistente nao recuperou Artilheiros');
assert.equal(view,'rankings','Recuperacao nao restaurou a rota de Artilheiros');

// Uma renderizacao tardia nao pode recolocar clubes, selecoes ou tecnicos.
render();
assert(page.innerHTML.includes('data-v18202-scorers-root'),'Wrapper de render nao restaurou Artilheiros');
page.innerHTML='<div>TECNICOS</div>';
global.__scorerObserver();
assert(page.innerHTML.includes('data-v18202-scorers-root'),'Observer nao removeu conteudo tardio incorreto');
assert(!page.innerHTML.includes('TECNICOS'),'Quadro de tecnicos permaneceu sobre Artilheiros');

// A blindagem termina quando o usuario escolhe explicitamente outra aba.
event=click(target({'data-view':'clubrankings'},'Clubes','v677-ranking-tab'));
assert(!event.prevented&&!event.stopped,'Navegacao para Clubes foi bloqueada');
view='clubrankings';page.innerHTML='<div>CLUBES ESCOLHIDOS</div>';
global.__scorerObserver();
assert(page.innerHTML.includes('CLUBES ESCOLHIDOS'),'Artilheiros impediu saida explicita para outra aba');

console.log(JSON.stringify({
 ok:true,
 postSeasonArchive:true,
 clickFromClubRanking:true,
 legacyTextButton:true,
 persistentIntent:true,
 renderOverwriteRecovered:true,
 mutationOverwriteRecovered:true,
 explicitExitPreserved:true,
 terminalLiveLayer:true,
 goals:13
}));
"""

    tmp = root / ".scorers-navigation-test.js"
    tmp.write_text(js, encoding="utf-8")
    try:
        result = subprocess.run(
            ["node", str(tmp)],
            capture_output=True,
            text=True,
            timeout=30,
        )
    finally:
        tmp.unlink(missing_ok=True)

    if result.returncode:
        fail("teste de Artilheiros falhou:\n" + (result.stderr or result.stdout)[-6000:])

    payload = json.loads(result.stdout.strip().splitlines()[-1])
    if not all(payload.get(key) for key in [
        "postSeasonArchive",
        "clickFromClubRanking",
        "legacyTextButton",
        "persistentIntent",
        "renderOverwriteRecovered",
        "mutationOverwriteRecovered",
        "explicitExitPreserved",
        "terminalLiveLayer",
    ]):
        fail("teste de Artilheiros retornou resultado incompleto")

    (root / "scorers-navigation-tests.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
