from __future__ import annotations
import json, re, subprocess, sys
from pathlib import Path


def die(msg: str) -> None:
    raise RuntimeError(msg)


def function_block(src: str, name: str) -> str:
    match = re.search(r"function\s+" + re.escape(name) + r"\s*\(", src)
    if not match:
        die(f"funcao ausente: {name}")
    brace = src.find("{", match.end())
    depth = 0
    quote = None
    escaped = False
    for index in range(brace, len(src)):
        ch = src[index]
        if quote:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
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
    die(f"funcao nao fechada: {name}")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: test_mls_vacation.py <project-dir>")
    root = Path(sys.argv[1]).resolve()
    html = (root / "src" / "index.html").read_text(encoding="utf-8")

    required = [
        "futbr-mls-vacation-18200-meta",
        "mandatoryShootout:true",
        "idempotentRecovery:true",
        "noRestartOnResume:true",
        "seasonWaitsForCup:true",
        "futbr-mls-vacation-18201-ui",
        "pausedVacationNextMatch:true",
        "takesCommandBeforeAdvance:true",
        "v18201-vac-nextmatch",
        "return v1891AdvanceToNextMatch();",
        "v.active=false;v.paused=false;v.remaining=0;v.untilSeason=false;",
        "if(!mls.champion)",
        "v18200MLSRecover(out)",
    ]
    for marker in required:
        if marker not in html:
            die("marcador MLS ausente: " + marker)
    if "Playoff da MLS sem vencedor." in html:
        die("a excecao que pausava as ferias ainda existe")

    names = [
        "v18200MLSResultWinner",
        "v18200EnsureMLSMatchWinner",
        "v18200MLSFinalizeChampion",
        "v18200MLSRepairState",
        "v18200MLSNormalizeSchedule",
        "v18200MLSStageLabel",
        "v18200MLSEnsureStage",
        "v18200MLSRequiredRound",
        "v18200MLSPruneObsoleteFuture",
        "v18200MLSEnsureResolutionStages",
        "v18200MLSRecover",
    ]
    blocks = "\n".join(function_block(html, name) for name in names)

    js = r'''
const assert=require('assert');
function hash5(text){let h=2166136261>>>0;for(const ch of String(text)){h^=ch.charCodeAt(0);h=Math.imul(h,16777619)>>>0;}return h;}
function team(s,id){return (s.teams||[]).find(t=>t.id===id)||null;}
function ledger(){} function news(){} function financeFactor58(){return 1;}
function v629MLSStage(round,label){return {type:'mlsplayoff',round,label,fixtures:[],prepared:false};}
function shootout(s,m){m.pens={score:[5,4],kicks:[],winner:m.sides[0].id};}
''' + blocks + r'''
function makeTie(a,b){return {a,b,score:[0,0],winner:null,results:[],wins:{}};}
const c={id:'mls',champion:null,played:0,mls:{seeded:true,seeds:{east:[],west:[]},seedRank:{},combinedRank:{},r1Scheduled:false,conferenceChampions:{}},rounds:{
 wild_east:[{a:'e8',b:'e9',winner:'e8',results:[]}],wild_west:[{a:'w8',b:'w9',winner:'w8',results:[]}],
 r1_east:[makeTie('e1','e8'),makeTie('e2','e7'),makeTie('e3','e6'),makeTie('e4','e5')],
 r1_west:[makeTie('w1','w8'),makeTie('w2','w7'),makeTie('w3','w6'),makeTie('w4','w5')]
}};
const state={seed:123456,year:2026,day:2,seasonDone:false,teams:[],competitions:{mls:c},vacation:{active:true,paused:false,remaining:10,untilSeason:true},schedule:[]};
const game1={type:'mlsplayoff',round:1,label:'jogo 1',prepared:true,fixtures:[]};
const game2={type:'mlsplayoff',round:2,label:'jogo 2',prepared:true,fixtures:[]};
let globalIndex=0;
for(const key of ['r1_east','r1_west'])for(let i=0;i<c.rounds[key].length;i++){
 const tie=c.rounds[key][i];
 const f1={id:'g1-'+globalIndex,phase:key,tieIndex:i,home:tie.a,away:tie.b,leg:1,mlsSeries:true,result:{home:1,away:1,winner:null,pens:null}};
 const first=v18200MLSResultWinner(state,f1,f1.result);
 const second=globalIndex<4?(first===tie.a?tie.b:tie.a):first;
 const f2={id:'g2-'+globalIndex,phase:key,tieIndex:i,home:tie.b,away:tie.a,leg:2,mlsSeries:true,result:{home:second===tie.b?2:1,away:second===tie.a?2:1,winner:second,pens:null}};
 game1.fixtures.push(f1);game2.fixtures.push(f2);globalIndex++;
}
state.schedule=[
 {type:'mlsplayoff',round:0,label:'wild',prepared:true,fixtures:[]},
 game1,game2,
 {type:'mlsplayoff',round:2,label:'duplicada',prepared:false,fixtures:[]},
 {type:'mlsplayoff',round:5,label:'finais conf',prepared:false,fixtures:[]},
 {type:'mlsplayoff',round:6,label:'cup',prepared:false,fixtures:[]}
];

const match={sides:[{id:'h',goals:1},{id:'a',goals:1}],pens:null};
assert.equal(v18200EnsureMLSMatchWinner(state,{home:'h',away:'a',id:'draw'},match),'h');
assert.equal(match.pens.winner,'h');

assert(v18200MLSRecover(state));
const unresolved=[...c.rounds.r1_east,...c.rounds.r1_west].filter(t=>!t.winner);
assert.equal(unresolved.length,4,'quatro series deveriam ir ao jogo 3');
assert.equal(state.schedule.filter(d=>d.type==='mlsplayoff'&&d.round===3).length,1,'jogo 3 deve existir uma vez');
assert.equal(state.schedule.filter(d=>d.type==='mlsplayoff'&&d.round===4).length,1,'semifinal deve existir uma vez');
assert.equal(c.mls.v18200RequiredRound,3,'a fase requerida deve ser o jogo 3');
const signature=state.schedule.map(d=>d.type+':'+d.round).join('|');
assert(v18200MLSRecover(state));
assert.equal(state.schedule.map(d=>d.type+':'+d.round).join('|'),signature,'recuperar duas vezes nao pode reiniciar ou duplicar a MLS');
assert.equal(state.schedule.filter(d=>d.type==='mlsplayoff'&&d.round===3).length,1);
assert.equal(state.schedule.filter(d=>d.type==='mlsplayoff'&&d.round===4).length,1);
for(const f of [...game1.fixtures,...game2.fixtures])if(f.result.home===f.result.away){assert(f.result.winner);assert(Array.isArray(f.result.pens));}

console.log(JSON.stringify({
 ok:true,
 mandatoryShootout:true,
 repairedDraws:true,
 requiredRound:c.mls.v18200RequiredRound,
 unresolvedSeries:unresolved.length,
 round3Stages:state.schedule.filter(d=>d.type==='mlsplayoff'&&d.round===3).length,
 round4Stages:state.schedule.filter(d=>d.type==='mlsplayoff'&&d.round===4).length,
 idempotent:true,
 vacationRemaining:state.vacation.remaining,
 pausedVacationNextMatch:true
}));
'''
    tmp = root / ".mls-vacation-test.js"
    tmp.write_text(js, encoding="utf-8")
    try:
        result = subprocess.run(["node", str(tmp)], capture_output=True, text=True, timeout=30)
    finally:
        tmp.unlink(missing_ok=True)
    if result.returncode:
        die("teste MLS falhou: " + (result.stderr or result.stdout)[-5000:])
    report = json.loads(result.stdout.strip().splitlines()[-1])
    (root / "mls-vacation-tests.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
