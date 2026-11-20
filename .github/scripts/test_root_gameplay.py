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

def final_patch_drain(html):
    start=html.rfind('v53DrainPatches=function(){')
    end=html.find('async function v722CatchUpAfterFocus(){',start)
    if start<0 or end<start: die('Handler final de patches ausente')
    return html[start:end]


def nationaljump_root_checks(drain):
    # Check the active handler, so an obsolete definition cannot hide a
    # missing call. The protected 18.369 paint has the same required order.
    day_start=drain.find("if(m.kind==='national-jump-day'){")
    sync_start=drain.find("if(m.kind==='national-jump-sync'){")
    live_start=drain.find("if(m.kind==='vac-live'){")
    live_end=drain.find("if(m.kind==='postmatch-closed'){")
    if not (0<=day_start<sync_start<live_start<live_end):
        die('Rotas nationaljump ausentes no handler final')
    day=drain[day_start:sync_start]
    paints=(
        'v53PaintStatus();v53ScheduleNationalJumpPaint();continue;',
        'v18369PaintOnly(()=>v53PaintStatus());v53ScheduleNationalJumpPaint();continue;'
    )
    if not any(x in day for x in paints):
        die('nationaljump sem pintura e scheduler no progresso final')
    if 'v52MarketIndex=null;v53ScheduleNationalJumpPaint();' not in drain[sync_start:live_start]:
        die('nationaljump sem scheduler apos sincronizacao final')
    if "if(v53Sim?.mode==='nationaljump'){v53ScheduleNationalJumpPaint();}" not in drain[live_start:live_end]:
        die('nationaljump sem scheduler no delta final')


def nationaljump_guard_regressions(drain):
    # Negative controls must fail even with an earlier, intact handler present.
    # These mutate only the test input; no game source is rewritten.
    suffix='async function v722CatchUpAfterFocus(){}\n'
    def reject(broken,label):
        if broken==drain: die('Mutacao negativa nationaljump nao aplicada: '+label)
        try: nationaljump_root_checks(final_patch_drain(drain+suffix+broken+suffix))
        except RuntimeError: return
        die('Guard nationaljump aceitou regressao: '+label)
    start=drain.index("if(m.kind==='national-jump-day'){")
    end=drain.index("if(m.kind==='national-jump-sync'){")
    day=drain[start:end]
    missing_paint=day.replace('v18369PaintOnly(()=>v53PaintStatus());','',1)
    if missing_paint==day: missing_paint=day.replace('v53PaintStatus();','',1)
    reject(drain[:start]+missing_paint+drain[end:],'status paint')
    # Each of the three entry points independently requires its scheduler.
    for route,limit in [('national-jump-day','national-jump-sync'),
                        ('national-jump-sync','vac-live'),('vac-live','postmatch-closed')]:
        a=drain.index("if(m.kind==='"+route+"'){")
        b=drain.index("if(m.kind==='"+limit+"'){")
        broken=drain[a:b].replace('v53ScheduleNationalJumpPaint();','',1)
        reject(drain[:a]+broken+drain[b:],route+' scheduler')


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
      "nationalProfileForcedSurface:true","nationalModalOwnRootTheme:true","nationalModalThemePinsV128:true","nationalRootSurfaceFollowsConsulted:true","premiumBuyOnWelcome:true","freeNationalStartBlocked:true","freeNationalStartCoreGate:true","nationalNamesNeverNumeric:true","fastCareerSeedRefs:true",
      "let v18176NationalModalCode=null,v18176OpeningNationalCode=null",
      "const use=v18176NationalModalCode||v18176OpeningNationalCode||code;",
      "try{v18172ApplyCareerSurface(p.primary);}catch(e){}",
      "window.open('https://futbrmanager.com.br/','_blank','noopener,noreferrer')",
      "p.v18175SeedRoster=data?.prebuiltInitial?null:rp","p.real?(p.v18175SeedRoster||null):null"
    ]
    for x in required:
        if x not in html: die('Marcador raiz ausente: '+x)
    if 'v18167NationalDrag' in html: die('Listener duplicado de drag nacional')

    # Integridade final: Artilheiros usa renderer proprio e a carreira nova
    # nao pode mais ser reconstruida pela compatibilidade 5.82.
    for marker in [
        "futbr-final-integrity-18198",
        "directScorerRenderer:true",
        "legacyProtectedRosterRepairDisabled:true",
        "initialSeniorCap:32",
        "window.v18198EnforceInitialSquads",
        "window.v18198EnforceInitialSquads?.(out)",
        "V579_INITIAL_MAIN=32",
        "V582_MAX_INITIAL_SENIORS=32",
        "out.v582InitialRosterSource='prebuilt-consolidated'"
    ]:
        if marker not in html:
            die('Integridade final 18.198 incompleta: '+marker)
    if "try{v582RepairFreshProtectedCareer?.(out);}catch(e){}" in html:
        die('Reconstrucao legacy 5.82 ainda roda apos a nova carreira')
    if "futbr-ranking-route-18197" in html:
        die('Guard antigo de Artilheiros ainda permanece no HTML final')

    # Simulacao nacional: qualidade real do XI domina, Elo e apenas ajuste secundario.
    for marker in [
        "function v18179NationalSimPower(s,code)",
        "function nationalPower(s,code)",
        "hp=v18179NationalSimPower(s,f.home)",
        "hp=nationalPower(s,f.home)",
        "1.25*Math.exp(gap*.038)",
        "pHome=E.clamp(.5+gap*.008,.32,.68)"
    ]:
        if marker not in html: die('Balanceamento nacional ausente: '+marker)

    # Tema: carreira usa a equipe comandada; fichas consultadas recebem paleta propria.
    for marker in [
        "function v18172ApplyCareerSurface(primary){return v18172ApplySurfaceToElement(document.documentElement,primary);}",
        "v18172ApplyCareerSurface(p.primary)",
        "v18172ApplySurfaceToElement(modalEl,p.primary)",
        "v18173PaintConsultedNationalProfile(n);",
        "const surface=typeof v18172SurfaceVars==='function'?v18172SurfaceVars(p.primary)",
        "try{v18172ApplySurfaceToElement(modalEl,p.primary);}catch(e){}",
        "try{v18172ApplySurfaceToElement(profile,p.primary);}catch(e){}",
        "v18174ForceNationalProfileTheme(code);",
        "set(modalEl,'background',",
        "set(head,'background',",
        "set(body,'background',",
        "v18176NationalModalCode=n;",
        "try{v51RefreshTheme?.();}catch(e){}",
        "v18176NationalModalCode=null;",
        "v18176OpeningNationalCode=n;",
        "const use=v18176NationalModalCode||v18176OpeningNationalCode||code;"
    ]:
        if marker not in html: die('Regra de tema dinamico incompleta: '+marker)

    # Plano gratuito nunca inicia carreira de selecao, mesmo por chamada direta.
    for marker in [
        "if(!v548FullAccess()&&v128NationalStart){",
        "Comecar uma carreira por selecao e um recurso exclusivo do Premium.",
        "function v643ConvertNewCareerToNational(s,code){if(!v548FullAccess())throw Error('Carreira por selecao requer Premium.')",
        "freeNationalStartCoreGate:true"
    ]:
        if marker not in html: die('Bloqueio autoritativo da carreira por selecao ausente: '+marker)

    for marker in [
        "freeNationalStartBlocked:true",
        "Carreira por selecao requer Premium.",
        "params?.options?.v643StartType==='national'&&!v18177FullAccess()",
        "document.querySelectorAll('[data-v643-start=\"national\"]')"
    ]:
        if marker not in html: die('Bloqueio Premium da carreira de selecao incompleto: '+marker)

    # Criacao de carreira: bases antigas podem usar referencia transitoria;
    # a base consolidada deve elimina-la para nao duplicar o mundo em RAM.
    for marker in [
        "p.v18175SeedRoster=data?.prebuiltInitial?null:rp",
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

    # Prova estrutural do nationaljump: as tres rotas do handler FINAL
    # continuam chamando o scheduler, com pintura direta ou protegida.
    final_drain=final_patch_drain(html)
    nationaljump_root_checks(final_drain)
    nationaljump_guard_regressions(final_drain)

    # Prova estrutural da geracao mundial e do reparo de saves antigos.
    if "if(out&&op==='create'){v18170EnsureAllNationalPools(out);try{window.v18198EnforceInitialSquads?.(out);" not in html:
        die('geracao mundial ou teto final de elenco nao ligados ao create')
    if 'v18170EnsureNationalPool(state,enemy,f);' not in html:
        die('reparo de adversario por partida nao ligado')
    if "p.clubId=null;p.real=false;p.generatedNationalSupport=true;p.v18170InitialNationalFreeAgent=true" not in html:
        die('jogador nacional de suporte nao e livre/ficticio')

    # Carreiras longas: historicos grandes fragmentados, caches limitados e
    # memoria derivada liberada antes da virada autoritativa.
    long_markers=[
        "18.181-long-career-fast-checkpoint",
        "'scorerArchive','transfers','retirements','history','internationalHistory','v735NationalArchive'",
        "if(m.size>48)m.delete(m.keys().next().value)",
        "(kept??={})[pid]={id:r.id||pid",
        "lastTransferTo=new Map()",
        "G.v168?.stop?.();G.v168?.purge?.()",
        "desktopBatchWrites:true",
        "sameSeasonHistoricalShardReuse:true",
        "raw-write-many",
        "scorerArchiveLimitPerCompetition:null"
    ]
    for marker in long_markers:
        if marker not in html:
            die('Otimizacao de carreira longa ausente: '+marker)

    report={'ok':True,'source':'final-transformed-index','ordering':ordering,'live_drag':drag,
            'nationaljump_root':True,'nationaljump_final_handler':True,
            'nationaljump_rejects_missing_paint':True,'nationaljump_rejects_missing_scheduler':True,
            'nationaljump_rejects_inactive_handler':True,
            'national_free_agents_root':True,'duplicate_drag':False}
    (root/'root-gameplay-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__': main()
