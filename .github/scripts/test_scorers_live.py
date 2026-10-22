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
        raise SystemExit("usage: test_scorers_live.py <project-dir>")

    root = Path(sys.argv[1]).resolve()
    html = (root / "src" / "index.html").read_text(encoding="utf-8")
    renderer = extract(html, "futbr-final-integrity-18198")
    navigation = extract(html, "futbr-terminal-scorers-18202")
    live = extract(html, "futbr-terminal-scorers-18203")

    required = [
        "liveSeason:true",
        "windowCapture:true",
        "ancestorPathRouting:true",
        "safeNationalityLookup:true",
        "defensiveLiveRows:true",
        "data-v18203-scorers-root",
        "typeof NAT!=='undefined'",
        "typeof C!=='undefined'",
        "rows?.players||rows?.stats||rows",
    ]
    for marker in required:
        if marker not in html:
            fail("marcador de Artilheiros ao vivo ausente: " + marker)

    if html.rfind("futbr-terminal-scorers-18203") <= html.rfind("futbr-terminal-scorers-18202"):
        fail("camada ao vivo nao ficou depois da navegacao 18.202")

    js = r"""
const assert=require('assert');
global.window=global;
global.GestorFC={};
global.scorerFilter={kind:'all',country:'all',division:'all',year:'',query:'',page:0,nationality:'all'};
global.view='clubrankings';
global.esc=v=>String(v??'').replace(/[&<>\"]/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[ch]));
global.starBadge=()=>'';
global.nation=code=>'<span>'+String(code||'UNK')+'</span>';
global.badge=t=>'<i>'+String(t?.short||t?.name||'')+'</i>';
global.teamButton=t=>'<button>'+String(t?.name||'')+'</button>';
global.v640Flag=code=>'['+code+']';
global.v677RankingTabs=()=>'<nav><button class="v677-ranking-tab" data-view="rankings"><span>Artilheiros</span></button><button data-view="clubrankings">Clubes</button></nav>';
global.coachesPage=()=>'<div>TECNICOS</div>';
global.E={
 normName:v=>String(v||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase(),
 team:(s,id)=>(s?.teams||[]).find(t=>t.id===id)||null,
 repairLineup:()=>{}
};
global.state={
 year:2026,day:3,lastDay:38,seasonDone:false,user:'t0',
 players:{
  p1:{id:'p1',name:'Atacante Vivo',natCode:'BRA',clubId:'t0',pos:'ATA',age:25},
  p2:{id:'p2',name:'Segundo Goleador',natCode:'ARG',clubId:'t1',pos:'ATA',age:27}
 },
 teams:[
  {id:'t0',name:'Clube Teste',short:'CTE',country:'bra',division:1,roster:['p1'],academy:[],proReserve:[],lineup:['p1']},
  {id:'t1',name:'Rival Teste',short:'RIV',country:'bra',division:1,roster:['p2'],academy:[],proReserve:[],lineup:['p2']}
 ],
 competitions:{},allTimeStats:{},scorerArchive:[],v640National:null,
 competitionStats:{
  'league:bra:1':{
   p1:{name:'Atacante Vivo',natCode:'BRA',goals:2,assists:1,apps:2,minutes:180,clubs:{t0:'Clube Teste'}},
   p2:{playerId:'p2',name:'Segundo Goleador',natCode:'ARG',goals:1,assists:0,apps:2,minutes:155,clubs:{t1:'Rival Teste'}}
  }
 }
};

const page={
 innerHTML:'<div>TECNICOS - quadro anterior</div>',dataset:{},
 querySelector(selector){
  if(selector.includes('data-v18203-scorers-root')&&this.innerHTML.includes('data-v18203-scorers-root'))return {};
  if(selector.includes('data-v18202-scorers-root')&&this.innerHTML.includes('data-v18202-scorers-root'))return {};
  return null;
 }
};
const app={};
const documentListeners={},windowListeners={},observers=[];
global.document={
 documentElement:{},
 querySelector(selector){if(selector==='#v555-page')return page;if(selector==='#app')return app;return null;},
 querySelectorAll(){return [];},
 addEventListener(type,fn){(documentListeners[type]??=[]).push(fn);}
};
global.addEventListener=(type,fn)=>{(windowListeners[type]??=[]).push(fn);};
global.MutationObserver=class{constructor(cb){this.cb=cb;observers.push(cb);}observe(){}};
global.requestAnimationFrame=fn=>fn();
global.queueMicrotask=fn=>fn();
global.setTimeout=fn=>{fn();return 1;};
global.renderPage=()=>'<section>Ranking antigo</section>';
global.render=()=>{page.innerHTML='<div>CLUBES recolocados pelo render antigo</div>';return true;};
global.closeModal=()=>{};
global.scrollTo=()=>{};
""" + renderer + "\n" + navigation + "\n" + live + r"""

// NAT e C nao foram declarados de proposito. O primeiro artilheiro nao pode
// provocar ReferenceError nem impedir a substituicao do quadro anterior.
let mounted=window.v18198ScorersPage();
assert(mounted.includes('Atacante Vivo'),'Artilheiro ao vivo nao foi montado');
assert(mounted.includes('Segundo Goleador'),'Segundo artilheiro ao vivo nao foi montado');
assert(mounted.includes('green strong">2</td>'),'Gols ao vivo incorretos');

function node(attrs,text,parent=null){return {
 nodeType:1,textContent:text,parentElement:parent,parentNode:parent,
 getAttribute(name){return attrs[name]??null;}
};}
const button=node({'data-view':'rankings','data-action':'nav'},'Artilheiros');
const span=node({},'Artilheiros',button);
function fire(type,target){
 const event={
  type,target,prevented:false,stopped:false,
  composedPath(){return [target,button];},
  preventDefault(){this.prevented=true;},
  stopImmediatePropagation(){this.stopped=true;}
 };
 for(const fn of windowListeners[type]||[])fn(event);
 return event;
}

fire('pointerdown',span);
const click=fire('click',span);
assert(click.prevented&&click.stopped,'Clique real de Artilheiros nao foi capturado');
assert(page.innerHTML.includes('data-v18203-scorers-root'),'Quadro fisico ao vivo nao foi montado');
assert(page.innerHTML.includes('Atacante Vivo'),'Quadro ao vivo perdeu o lider');
assert(!page.innerHTML.includes('TECNICOS - quadro anterior'),'Tela anterior permaneceu visivel');

// Uma rotina tardia nao pode recolocar clubes/selecoes/tecnicos.
page.innerHTML='<div>SELECOES</div>';
for(const cb of observers)cb([],null);
assert(page.innerHTML.includes('data-v18203-scorers-root'),'Observer nao restaurou Artilheiros');
assert(!page.innerHTML.includes('SELECOES'),'Selecoes continuou sobre Artilheiros');

// A tabela precisa atualizar quando a rodada seguinte alterar os gols.
state.competitionStats['league:bra:1'].p1.goals=4;
page.innerHTML='<div>CLUBES</div>';
assert(window.v18203PaintScorers(true),'Pintura explicita falhou');
assert(page.innerHTML.includes('Atacante Vivo'),'Lider sumiu apos nova rodada');
assert(page.innerHTML.includes('green strong">4</td>'),'Gols nao atualizaram apos nova rodada');
assert(!page.innerHTML.includes('<div>CLUBES</div>'),'Clubes permaneceu sobre Artilheiros');

console.log(JSON.stringify({
 ok:true,
 liveRowsWithoutEmbeddedId:true,
 missingNatAndCountryGlobalsSafe:true,
 clickFromNestedSpan:true,
 firstRoundsMounted:true,
 staleRankingRecovered:true,
 nextRoundUpdated:true,
 goals:4
}));
"""

    tmp = root / ".scorers-live-test.js"
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
        fail("teste de Artilheiros ao vivo falhou:\n" + (result.stderr or result.stdout)[-8000:])

    payload = json.loads(result.stdout.strip().splitlines()[-1])
    checks = [
        "liveRowsWithoutEmbeddedId",
        "missingNatAndCountryGlobalsSafe",
        "clickFromNestedSpan",
        "firstRoundsMounted",
        "staleRankingRecovered",
        "nextRoundUpdated",
    ]
    if not all(payload.get(key) for key in checks):
        fail("teste de Artilheiros ao vivo retornou resultado incompleto")

    (root / "scorers-live-tests.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
