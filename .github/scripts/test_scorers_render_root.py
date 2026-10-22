from __future__ import annotations
import json
import re
import subprocess
import sys
from pathlib import Path


def fail(message: str) -> None:
    raise RuntimeError(message)


def extract_function(src: str, name: str) -> str:
    match = re.search(r"function\s+" + re.escape(name) + r"\s*\(", src)
    if not match:
        fail(f"funcao ausente: {name}")
    brace = src.find("{", match.end())
    depth = 0
    quote = None
    escaped = False
    template_depth = 0
    for index in range(brace, len(src)):
        ch = src[index]
        if quote:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif quote == "`" and ch == "$" and index + 1 < len(src) and src[index + 1] == "{":
                template_depth += 1
            elif quote == "`" and ch == "}" and template_depth:
                template_depth -= 1
            elif ch == quote and template_depth == 0:
                quote = None
            continue
        if ch in ("'", '"', "`"):
            quote = ch
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return src[match.start(): index + 1]
    fail(f"funcao nao fechada: {name}")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: test_scorers_render_root.py <project-dir>")
    root = Path(sys.argv[1]).resolve()
    html = (root / "src" / "index.html").read_text(encoding="utf-8")

    match = re.search(r'<script id="futbr-scorers-render-root-18211">\s*([\s\S]*?)\s*</script>', html)
    if not match:
        fail("script raiz de renderizacao 18.211 ausente")
    terminal = match.group(1)
    render_function = extract_function(html, "v555RenderPage")

    clear_pos = render_function.find("page.innerHTML=''")
    factory_pos = render_function.find("window.v18211RankingsHTML")
    assign_pos = render_function.find("page.innerHTML=String(pageHTML||'')")
    if min(clear_pos, factory_pos, assign_pos) < 0 or not clear_pos < factory_pos < assign_pos:
        fail("v555RenderPage nao limpa a pagina antes de avaliar Artilheiros")

    required = [
        "clearsStalePageBeforeEvaluation:true",
        "safeFallback:true",
        "rootRenderBranch:true",
        "noObserver:true",
        "noClickInterceptor:true",
        "preservesPerformanceArchitecture:true",
        "data-v18211-safe-root",
    ]
    for marker in required:
        if marker not in html:
            fail("marcador 18.211 ausente: " + marker)

    js = r'''
const assert=require('assert');
global.window=global;
global.GestorFC={debugScorersErrors:false};
let view='rankings';
let state={
 year:2026,day:3,seasonDone:false,nextId:9,
 players:{p1:{id:'p1',name:'Atacante Real',natCode:'BRA',clubId:'t0'}},
 teams:[{id:'t0',name:'Clube Real',short:'CRE'}],
 competitionStats:{'league:bra:1':{p1:{id:'p1',name:'Atacante Real',natCode:'BRA',goals:3,assists:1,apps:3,minutes:270,clubs:{t0:'Clube Real'}}}},
 scorerArchive:[]
};
const E={team:(s,id)=>(s.teams||[]).find(t=>t.id===id)||null};
function esc(v){return String(v??'');}
function v677RankingTabs(){return '<nav><button data-view="rankings">Artilheiros</button></nav>';}
'''+terminal+r'''

let current='<div id="old-clubs">RANKING DE CLUBES ANTIGO</div>',writes=[];
const page={dataset:{},isConnected:true,querySelector:()=>null};
Object.defineProperty(page,'innerHTML',{get(){return current;},set(value){current=String(value);writes.push(current);}});
const notices={innerHTML:''};
const root={querySelector(selector){if(selector==='#v555-page')return page;if(selector==='#v555-notices')return notices;return null;}};
const performance={now:(()=>{let n=0;return()=>++n;})()};
const v555Perf={pageRenders:0,lastPageMs:0};
let v555LastView='';
function v555NoticesHTML(){return '';}
function v551CleanScreen(){}
function v554CleanLegacyCopy(){}
function v548ApplyFeatureLocks(){}
function v1882EnhanceCountrySelects(){}
function v54ApplyPositionOrder(){}
function v5MarkSelection(){}
function v510ApplyTrophyPhotos(){}
function v555ScheduleDecor(){}
let renderPage=()=>{throw new Error('falha proposital no renderer completo');};
'''+render_function+r'''

const originalRankingsHTML=window.v18211RankingsHTML;

// A tela antiga precisa ser apagada antes mesmo de o renderer falhar.
window.v18211RankingsHTML=()=>{throw new Error('falha proposital no factory raiz');};
writes=[];current='<div id="old-clubs">RANKING DE CLUBES ANTIGO</div>';
v555RenderPage(root);
const failedFactoryFirstWrite=writes[0];
assert.equal(failedFactoryFirstWrite,'','a tela anterior nao foi limpa antes da avaliacao');
assert(!current.includes('RANKING DE CLUBES ANTIGO'),'conteudo antigo permaneceu');
assert(current.includes('data-v18211-safe-root="1"'),'fallback seguro nao foi montado');
assert(current.includes('Atacante Real'),'fallback nao trouxe dados ao vivo');
assert(current.includes('green strong">3</td>'),'fallback perdeu os gols ao vivo');

// O proprio factory terminal tambem deve transformar excecao rica em pagina valida.
window.v18211RankingsHTML=originalRankingsHTML;
window.v18210RankingsPage=()=>{throw new Error('linha real inconsistente');};
const recovered=window.v18211RankingsHTML();
assert(recovered.includes('data-v18211-safe-root="1"'),'factory terminal nao recuperou excecao');
assert(recovered.includes('Atacante Real'),'factory terminal nao preservou artilheiros');

// Caminho normal continua substituindo integralmente a pagina.
window.v18211RankingsHTML=()=>'<div data-v18210-scorers-root="1">ARTILHEIROS NOVOS</div>';
writes=[];current='<div>TECNICOS ANTIGOS</div>';
v555RenderPage(root);
assert.equal(writes[0],'','caminho normal nao limpou antes de renderizar');
assert.equal(current,'<div data-v18210-scorers-root="1">ARTILHEIROS NOVOS</div>');

// Outras rotas continuam usando o renderizador normal.
view='clubrankings';renderPage=()=>'<div>CLUBES NOVOS</div>';
writes=[];current='<div>ARTILHEIROS</div>';
v555RenderPage(root);
assert.equal(current,'<div>CLUBES NOVOS</div>','rota de clubes foi alterada');

console.log(JSON.stringify({
 ok:true,
 stalePageClearedBeforeEvaluation:true,
 richRendererFailureRecovered:true,
 liveRowsInFallback:true,
 normalScorersPath:true,
 otherRankingRoutesPreserved:true,
 failedFactoryFirstWrite,
 goals:3
}));
'''

    tmp = root / ".scorers-render-root-test.js"
    tmp.write_text(js, encoding="utf-8")
    try:
        result = subprocess.run(["node", str(tmp)], capture_output=True, text=True, timeout=30)
    finally:
        tmp.unlink(missing_ok=True)
    if result.returncode:
        fail("teste raiz de renderizacao falhou:\n" + (result.stderr or result.stdout)[-8000:])
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    (root / "scorers-render-root-tests.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
