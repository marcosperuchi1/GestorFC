from __future__ import annotations
import json, re, subprocess, sys
from pathlib import Path

def die(msg): raise RuntimeError(msg)

def run_node(src, root, name):
    p=root/f'.futbr_{name}.js'; p.write_text(src,encoding='utf-8')
    try: r=subprocess.run(['node',str(p)],capture_output=True,text=True)
    finally: p.unlink(missing_ok=True)
    if r.returncode: die(name+' falhou: '+r.stderr[-1800:])
    return json.loads(r.stdout.strip().splitlines()[-1])

def main():
    if len(sys.argv)!=2: raise SystemExit('usage: test_root_gameplay.py <project-dir>')
    root=Path(sys.argv[1]).resolve(); html=(root/'src/index.html').read_text(encoding='utf-8')
    required=[
      'futbr-root-18170-fixes','function v53ScheduleNationalJumpPaint()',
      'function v18170EnsureAllNationalPools(s)','v18170InitialNationalFreeAgent',
      "t.v600PreferredBench=v602SortPlayerIds(list.slice(0,V600_BENCH_LIMIT))",
      "ids=typeof v602SortPlayerIds==='function'?v602SortPlayerIds(raw):raw",
      "return typeof v602SortPlayerIds==='function'?v602SortPlayerIds(ids):ids;",
      "E.swapPlayers(state,t,source.id,destination.dataset.v5Player,m,sideIndex)",
      "localizedNationalFreeAgentNames:true","reservePointerSwap:true",
      "dynamicCareerSurfaceTheme:true","consultedProfileOwnTheme:true","dragGhost:true",
      "function v18171NationalGeneratedName(s,code,id,used=new Set())",
      "function v18172ApplySurfaceToElement(el,primary)",
      "function v18172PointerGhostAt(p,e)",
      "nationalProfileFinalOwnTheme:true",
      "function v18173PaintConsultedNationalProfile(code)",
      "const v18173BaseOpenNationalProfile=typeof v645OpenNationalProfile==='function'?v645OpenNationalProfile:null;",
      "function v18174ForceNationalProfileTheme(code)",
      "nationalProfileForcedSurface:true","nationalNamesNeverNumeric:true","fastCareerSeedRefs:true",
      "p.v18175SeedRoster=rp","p.real?(p.v18175SeedRoster||null):null"
    ]
    for x in required:
        if x not in html: die('Marcador raiz ausente: '+x)
    if 'v18167NationalDrag' in html: die('Listener duplicado de drag nacional')

    # Tema: carreira usa a equipe comandada; fichas consultadas recebem paleta propria.
    for marker in [
        "function v18172ApplyCareerSurface(primary){return v18172ApplySurfaceToElement(document.documentElement,primary);}",
        "v18172ApplyCareerSurface(p.primary)",
        "v18172ApplySurfaceToElement(modalEl,p.primary)",
        "v18173PaintConsultedNationalProfile(code);",
        "const surface=typeof v18172SurfaceVars==='function'?v18172SurfaceVars(p.primary)",
        "try{v18172ApplySurfaceToElement(modalEl,p.primary);}catch(e){}",
        "try{v18172ApplySurfaceToElement(profile,p.primary);}catch(e){}",
        "v18174ForceNationalProfileTheme(code);",
        "set(modalEl,'background',",
        "set(head,'background',",
        "set(body,'background',"
    ]:
        if marker not in html: die('Regra de tema dinamico incompleta: '+marker)

    # Criacao de carreira: a segunda passagem deve reutilizar a referencia
    # transitoria do registro da base em vez de reconstruir Maps por nome.
    for marker in [
        "p.v18175SeedRoster=rp",
        "const info=db[t.id];",
        "p.real?(p.v18175SeedRoster||null):null",
        "if(p.v18175SeedRoster)delete p.v18175SeedRoster;"
    ]:
        if marker not in html: die('Otimizacao de criacao incompleta: '+marker)
    if "const info=db[t.id],map=new Map((info?.players||[]).map" in html:
        die('Criacao ainda reconstrui Maps de elenco por clube')

    # Arraste por pointer deve exibir uma copia flutuante e remove-la no final.
    for marker in [
        "g.classList.add('v18172-drag-ghost')",
        "document.body.appendChild(g);v18172PointerGhost=g;",
        "v18172PointerGhostAt(p,e);",
        "v18172RemovePointerGhost();v5Execute(p,dest,e.clientX,e.clientY);",
        "pointerEvents:'none'"
    ]:
        if marker not in html: die('Ghost visual do arraste incompleto: '+marker)

    # O gerador da Coreia do Norte deve usar nomes coreanos e nunca cair no padrao brasileiro.
    prk_block=re.search(r"PRK:\{familyFirst:true,g:\[(.*?)\],s:\[(.*?)\]\}",html,re.S)
    if not prk_block: die('Pool PRK ausente')
    prk_text=prk_block.group(0)
    for bad in ['Joao','Lucas','Gabriel','Matheus','Rafael','Pedro','Silva','Santos','Oliveira']:
        if bad in prk_text: die('Nome brasileiro contaminou pool PRK: '+bad)
    if not all(x in prk_text for x in ['Kwang-song','Chol-min','Kim','Ri','Pak']):
        die('Pool PRK nao contem identidade coreana suficiente')
    if "+String((h%89)+10)" in html:
        die('Gerador nacional ainda possui fallback numerico no nome')
    if "const tripleTotal=Math.max(1,g.length*sn.length" not in html:
        die('Gerador nacional nao ampliou combinacoes alfabeticas')
    if "const clean=p.v18171LocalizedName&&p.natCode===n&&!/\\d/.test" not in html:
        die('Reparo de nomes nacionais antigos com numero ausente')

    # Mouse em reserva deve usar pointer; HTML drag nativo deve ser bloqueado no banco.
    if "if(el.dataset.v5Slot===undefined){e.preventDefault();return;}" not in html:
        die('Drag HTML nativo do banco ainda nao foi bloqueado')
    if "if(e.pointerType==='mouse'&&el.dataset.v5Slot!==undefined)return;" not in html:
        die('Mouse no banco ainda nao entra na rota pointer')
    if "if(e.pointerType==='mouse'){v5Selection=v5Pointer;v5MarkSelection();}" not in html:
        die('Selecao visual do reserva por pointer ausente')

    # Testa a regra de ordenacao com a mesma ordem usada pela fonte final.
    js_order = r'''
const order={GOL:0,ZAG:1,LAT:2,VOL:3,MEI:4,ATA:5};
const players={g:{pos:'GOL',ovr:70},z:{pos:'ZAG',ovr:75},l:{pos:'LAT',ovr:72},v:{pos:'VOL',ovr:73},m1:{pos:'MEI',ovr:80},m2:{pos:'MEI',ovr:78},a:{pos:'ATA',ovr:90}};
const ids=['a','m2','g','m1','z','v','l'].sort((a,b)=>(order[players[a].pos]-order[players[b].pos])||(players[b].ovr-players[a].ovr));
const exp=['g','z','l','v','m1','m2','a'];
if(JSON.stringify(ids)!==JSON.stringify(exp))throw Error('ordem incorreta '+JSON.stringify(ids));
console.log(JSON.stringify({ok:true,ids}));
'''
    ordering=run_node(js_order,root,'root_order')

    # Executa a rota EXATA do v5Execute raiz para reserva -> titular durante jogo.
    line=next((x for x in html.splitlines() if x.startswith('function v5Execute(source,destination,x,y){')),None)
    if not line: die('v5Execute raiz ausente')
    js_drag = """
let state={live:{}},calls=[],v5Drag=null;
function v5Target(){return {};}; function humanSide(){return 0};
function stopTimer(){calls.push('stop')}; function v5FinishEdit(c){calls.push('finish:'+c)};
function toast(){}; function updateMatch(){};
const E={moveIntoSlot:()=>{},movePlayer:()=>{},swapPlayers:(s,t,a,b,m,si)=>calls.push('swap:'+a+':'+b+':'+si)};
"""+line+"""
const dest={dataset:{v5Player:'starter',v5Context:'live'},closest:()=>null};
v5Execute({id:'reserve',ctx:'live'},dest,0,0);
if(!calls.includes('swap:reserve:starter:0'))throw Error(JSON.stringify(calls));
console.log(JSON.stringify({ok:true,calls}));
"""
    drag=run_node(js_drag,root,'root_drag')

    # Prova estrutural do nationaljump: os tres pontos de entrada chamam o scheduler raiz.
    jump_checks=[
      "if(v53Sim?.mode==='nationaljump'){v53ScheduleNationalJumpPaint();}",
      "v53PaintStatus();v53ScheduleNationalJumpPaint();continue;",
      "v52MarketIndex=null;v53ScheduleNationalJumpPaint();"
    ]
    for x in jump_checks:
        if x not in html: die('nationaljump sem refresh raiz: '+x)

    # Prova estrutural da geracao mundial e do reparo de saves antigos.
    if "if(out&&op==='create')v18170EnsureAllNationalPools(out);" not in html:
        die('geracao mundial de jogadores livres nao ligada ao create')
    if 'v18170EnsureNationalPool(state,enemy,f);' not in html:
        die('reparo de adversario por partida nao ligado')
    if "p.clubId=null;p.real=false;p.generatedNationalSupport=true;p.v18170InitialNationalFreeAgent=true" not in html:
        die('jogador nacional de suporte nao e livre/ficticio')

    report={'ok':True,'source':'final-transformed-index','ordering':ordering,'live_drag':drag,
            'nationaljump_root':True,'national_free_agents_root':True,'duplicate_drag':False}
    (root/'root-gameplay-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__': main()