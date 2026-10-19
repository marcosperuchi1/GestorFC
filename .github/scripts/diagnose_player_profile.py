from __future__ import annotations
import re,sys
from pathlib import Path

def main():
    if len(sys.argv)!=2: raise SystemExit("usage: diagnose_player_profile.py <project-dir>")
    html=(Path(sys.argv[1]).resolve()/"src"/"index.html").read_text(encoding="utf-8")
    terms=["Carreira global","v555CareerArchive","allTimeStats","playerProfile","player profile","ficha","assist","goals"]
    for term in terms:
        print("\n===== "+term+" =====")
        n=0
        for m in re.finditer(re.escape(term),html,re.I):
            a=max(0,m.start()-1400);b=min(len(html),m.end()+3200)
            print("\n@",m.start(),re.sub(r"\s+"," ",html[a:b]))
            n+=1
            if n>=25: break
if __name__=="__main__": main()
