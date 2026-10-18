from __future__ import annotations
import re, sys
from pathlib import Path

KEYWORDS = [
    'season','temporad','newseason','nextseason','rollover','year',
    'history','histor','archive','snapshot','ranking','news','movements',
    'transfer','schedule','fixture','competition','alltime','careerarchive',
    'academy','youth','retire','retirement','save','shard','cache','memo',
    'worker','clone','structuredclone','json.stringify','json.parse'
]

def balanced(text, brace):
    depth=0; quote=None; esc=False; i=brace
    while i<len(text):
        ch=text[i]
        if quote:
            if esc: esc=False
            elif ch=='\\': esc=True
            elif ch==quote: quote=None
        else:
            if ch in ("'",'"','`'): quote=ch
            elif ch=='{': depth+=1
            elif ch=='}':
                depth-=1
                if depth==0: return i+1
        i+=1
    return -1

def compact(s):
    return re.sub(r'\s+',' ',s).strip()

def main():
    if len(sys.argv)!=2: raise SystemExit('usage: diagnose_memory_growth.py <project-dir>')
    html=(Path(sys.argv[1])/'src'/'index.html').read_text(encoding='utf-8')
    print('HTML_BYTES',len(html))

    funcs=[]
    pat=re.compile(r'function\s+([A-Za-z_$][\w$]*)\s*\(([^)]*)\)\s*\{')
    for m in pat.finditer(html):
        end=balanced(html,m.end()-1)
        if end<0: continue
        body=html[m.start():end]
        low=body.lower()
        score=sum(1 for k in KEYWORDS if k in low)
        if score>=3:
            funcs.append((score,len(body),m.group(1),m.group(2),body))
    print('\n===== HIGH-RISK FUNCTIONS =====')
    for score,n,name,args,body in sorted(funcs,key=lambda x:(-x[0],-x[1]))[:120]:
        print(f'\n### {name}({args}) score={score} len={n}')
        print(compact(body)[:7000])

    print('\n===== STATE GROWTH EXPRESSIONS =====')
    growth_patterns=[
        r'([A-Za-z_$][\w$\.\[\]"\'\-]+)\.push\(',
        r'([A-Za-z_$][\w$\.\[\]"\'\-]+)\.unshift\(',
        r'([A-Za-z_$][\w$\.\[\]"\'\-]+)\.concat\(',
        r'([A-Za-z_$][\w$\.\[\]"\'\-]+)\s*=\s*\[\.\.\.',
    ]
    found=[]
    for p in growth_patterns:
        for m in re.finditer(p,html):
            a=max(0,m.start()-500); b=min(len(html),m.end()+1000)
            sn=compact(html[a:b])
            low=sn.lower()
            if any(k in low for k in KEYWORDS):
                found.append((m.start(),sn))
    for pos,sn in sorted(found)[:500]:
        print(f'@{pos} {sn}')

    print('\n===== SUSPICIOUS GLOBALS / COLLECTIONS =====')
    names=[
      'v538CareerArchive','v555CareerArchive','competitionStats','allTimeStats',
      'schedule','competitions','history','news','movements','transfers',
      'ranking','rankings','snapshots','previous','archive','seasonHistory',
      'transferHistory','matchHistory','managerHistory'
    ]
    for name in names:
        print(f'\n--- {name} ---')
        count=0
        for m in re.finditer(re.escape(name),html,re.I):
            a=max(0,m.start()-500);b=min(len(html),m.end()+1200)
            print('@',m.start(),compact(html[a:b]))
            count+=1
            if count>=20: break

if __name__=='__main__': main()
