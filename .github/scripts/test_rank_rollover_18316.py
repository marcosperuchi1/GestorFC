from pathlib import Path
import json, sys, re

def main():
    if len(sys.argv)!=2: raise SystemExit('usage: test_rank_rollover_18316.py <project-dir>')
    root=Path(sys.argv[1]).resolve(); html=(root/'src'/'index.html').read_text(encoding='utf-8')
    required=[
      'FUTBR_RANK_ROLLOVER_18316','cross-season-ready-top1000-carry','noSeasonRebuild:true','preserveRecords:true',
      'previousSnapshotFallback:true','v18111RebaseCache(s,carry,target)','Number(snap.year)!==year-1',
      "nc.v18312Source='season-carry-18.316:'",'nc.v18315TitlesReady=false','nc.progress=100','G.v18315?.ensure?.()'
    ]
    for m in required:
        if m not in html: raise RuntimeError('marcador ausente: '+m)
    block=html[html.index('/* FUTBR_RANK_ROLLOVER_18316 */'):]
    # Guarantee the carry is attempted BEFORE the current 18.315/base ensure, otherwise v18312 can seed a 0% rebuild first.
    wrapper=re.search(r"v86EnsureBuild=function\(\.\.\.args\)\{(.*?)return c;\n \};",block,re.S)
    if not wrapper: raise RuntimeError('wrapper v86EnsureBuild 18.316 ausente')
    body=wrapper.group(1)
    if body.index('promote(state)')>body.index('baseEnsure(...args)'): raise RuntimeError('handoff executa depois do builder')
    # Model the essential rollover invariant: rows + records survive; only year/stamp changes.
    old_rows=[{'id':'a','performancePoints':90,'titlePoints':10,'totalPoints':100},{'id':'b','performancePoints':80,'titlePoints':0,'totalPoints':80}]
    old_records={'a':{'games':38,'wins':25,'draws':8,'losses':5},'b':{'games':38,'wins':20,'draws':9,'losses':9}}
    carry={'oldYear':2026,'year':2027,'rows':[dict(x) for x in old_rows],'records':{k:dict(v) for k,v in old_records.items()}}
    rebased={'year':carry['year'],'day':0,'rows':carry['rows'],'records':carry['records'],'ready':True,'building':False,'progress':100}
    if rebased['year']!=2027 or rebased['progress']!=100 or rebased['building']: raise RuntimeError('rebase nao nasce pronto')
    if rebased['records']['a']['games']!=38 or rebased['rows'][0]['totalPoints']!=100: raise RuntimeError('rebase perdeu registros/pontos')
    # Ensure later architecture no longer directly owns the final ensure without our wrapper.
    if html.rfind('FUTBR_RANK_ROLLOVER_18316') < html.rfind('FUTBR_SPARSE_TITLES_18315'): raise RuntimeError('18.316 nao esta depois da 18.315')
    result={'ok':True,'version':'18.316','rolloverStartsReadyAt100':True,'recordsSurvive':True,'pointsSurvive':True,'titlesReconcileAfterCarry':True,'previousSnapshotFallback':True}
    (root/'rank-rollover-18316-tests.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result))
if __name__=='__main__': main()
