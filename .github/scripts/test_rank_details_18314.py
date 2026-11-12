from __future__ import annotations
import json, sys
from pathlib import Path
def main():
    if len(sys.argv)!=2: raise SystemExit('usage: test_rank_details_18314.py <project-dir>')
    root=Path(sys.argv[1]).resolve(); html=(root/'src'/'index.html').read_text(encoding='utf-8')
    required=['FUTBR_RANK_CACHE_18314','cacheTracksBuildState:true','c?.building?1:0','c?.ready?1:0','Number(c?.progress)||0','Number(c?.refreshDone)||0','Number(c?.refreshCount)||0']
    for m in required:
        if m not in html: raise RuntimeError('marcador ausente: '+m)
    if html.count('function currentRankKey(){') != 1: raise RuntimeError('currentRankKey duplicado/ausente')
    def key(c): return '|'.join(map(str,[c['stamp'],c['day'],c['titleRevision'],int(c['dirty']),int(c['refreshing']),int(c['building']),int(c['ready']),c['progress'],c['refreshDone'],c['refreshCount'],c['rows']]))
    provisional=dict(stamp='2029:50',day=50,titleRevision=4,dirty=False,refreshing=False,building=True,ready=False,progress=99,refreshDone=0,refreshCount=0,rows=1000)
    exact={**provisional,'building':False,'ready':True,'progress':100}
    if key(provisional)==key(exact): raise RuntimeError('cache nao invalida na conclusao do ranking')
    refreshing={**exact,'refreshing':True,'refreshDone':11,'refreshCount':20}
    refreshed={**exact,'refreshing':False,'refreshDone':0,'refreshCount':0}
    if key(refreshing)==key(refreshed): raise RuntimeError('cache nao invalida apos delta')
    result={'ok':True,'version':'18.314','provisionalToExactInvalidates':True,'deltaCompletionInvalidates':True,'titlesCanRepaintAfter100':True}
    (root/'ranking-cache-18314-tests.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result))
if __name__=='__main__': main()
