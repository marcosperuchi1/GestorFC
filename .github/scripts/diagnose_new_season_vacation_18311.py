from __future__ import annotations
import json, re, sys
from pathlib import Path

def balanced_function(src: str, pos: int) -> str:
    starts=[m.start() for m in re.finditer(r'(?:async\s+)?function\s+[A-Za-z0-9_$]+\s*\(',src[:pos+1])]
    if not starts:return ''
    start=starts[-1]
    brace=src.find('{',start)
    if brace<0:return ''
    depth=0;quote=None;escape=False;comment=None;i=brace
    while i<len(src):
        c=src[i];n=src[i:i+2]
        if comment=='line':
            if c=='\\n':comment=None
        elif comment=='block':
            if n=='*/':comment=None;i+=1
        elif quote:
            if escape:escape=False
            elif c=='\\\\':escape=True
            elif c==quote:quote=None
        elif n=='//':comment='line';i+=1
        elif n=='/*':comment='block';i+=1
        elif c in "'\\\"\\`":quote=c
        elif c=='{':depth+=1
        elif c=='}':
            depth-=1
            if depth==0:return src[start:i+1]
        i+=1
    return src[start:start+6000]

def main():
    if len(sys.argv)!=2:raise SystemExit('usage: diagnose_new_season_vacation_18311.py <project-dir>')
    root=Path(sys.argv[1]).resolve();html=(root/'src/index.html').read_text(encoding='utf-8')
    terms=['v18121NewSeasonPreparation','Salvando o calendário da nova temporada','Salvando o calendario da nova temporada','advanceWaitsPendingCheckpoint','createCheckpointOptimization','v53Pending','checkpoint','Iniciando férias','Iniciando ferias']
    report={}
    printed=set()
    for term in terms:
        hits=[]
        for m in re.finditer(re.escape(term),html,re.I):
            fn=balanced_function(html,m.start())
            snippet=html[max(0,m.start()-900):min(len(html),m.end()+1800)]
            hits.append({'pos':m.start(),'snippet':snippet})
            key=fn[:200]
            if fn and key not in printed:
                printed.add(key)
                print('\\n===== FUNCTION FOR',term,'=====\\n'+fn[:12000],flush=True)
        report[term]=hits
        if hits:
            print('\\n===== HITS',term,len(hits),'=====\\n',flush=True)
            for h in hits[:12]:print(h['snippet'],flush=True)
    (root/'new-season-vacation-18311-diagnostic.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    if not report['v18121NewSeasonPreparation']:raise RuntimeError('v18121NewSeasonPreparation ausente')
if __name__=='__main__':main()
