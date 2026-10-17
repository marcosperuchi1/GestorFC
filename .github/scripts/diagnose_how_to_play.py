from __future__ import annotations
import re, sys
from pathlib import Path

def compact(s):
    return re.sub(r"\s+"," ",s).strip()

def main():
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
    if len(sys.argv)!=2: raise SystemExit("usage: diagnose_how_to_play.py <project-dir>")
    html=(Path(sys.argv[1])/"src"/"index.html").read_text(encoding="utf-8")
    print("HTML_BYTES",len(html))
    terms=["Como jogar","COMO JOGAR","como jogar","Como Jogar","como-jogar","how to play","versao","versão","novidades","alteracoes","alterações","changelog","ajuda"]
    seen=set()
    for term in terms:
        print("\n===== TERM",term,"=====")
        for m in list(re.finditer(re.escape(term),html,re.I))[:80]:
            a=max(0,m.start()-2200); b=min(len(html),m.end()+6000)
            key=(a,b)
            if key in seen: continue
            seen.add(key)
            print("@",m.start())
            print(compact(html[a:b]))
    print("\n===== FUNCTIONS WITH HELP/HOW/ABOUT/CHANGE/VERSION =====")
    pat=re.compile(r"function\s+([A-Za-z_$][\w$]*)\s*\(([^)]*)\)\s*\{")
    for m in pat.finditer(html):
        name=m.group(1)
        if not re.search(r"help|how|about|change|version|guide|tutorial|jogar|ajuda",name,re.I):
            continue
        a=m.start(); b=min(len(html),a+12000)
        print("\n###",name,m.group(2))
        print(compact(html[a:b]))

if __name__=="__main__": main()
