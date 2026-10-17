from __future__ import annotations
import re, sys
from pathlib import Path

def balanced_body(text: str, brace: int):
    depth=0; quote=None; esc=False; i=brace
    while i < len(text):
        ch=text[i]
        if quote:
            if esc: esc=False
            elif ch=="\\": esc=True
            elif ch==quote: quote=None
        else:
            if ch in ("'", '"', "`"): quote=ch
            elif ch=="{": depth+=1
            elif ch=="}":
                depth-=1
                if depth==0: return text[brace:i+1]
        i+=1
    return ""

def main():
    if len(sys.argv)!=2: raise SystemExit("usage: diagnose_match_engine.py <project-dir>")
    html=(Path(sys.argv[1])/"src"/"index.html").read_text(encoding="utf-8")
    print("HTML_BYTES",len(html))
    defs=[]
    for m in re.finditer(r"function\s+([A-Za-z_$][\w$]*)\s*\(([^)]*)\)\s*\{",html):
        body=balanced_body(html,m.end()-1)
        if not body: continue
        low=body.lower()
        score=0
        for k,w in [("nationalfixtures",6),(".result",5),("pens",4),("overall(",3),("rng(",2),("fixture",2),("lineup",2),("strength",4),("xg",3),("goal",2)]:
            if k in low: score+=w
        if score>=7:
            defs.append((score,m.group(1),m.group(2),body))
    for score,name,args,body in sorted(defs,key=lambda x:(-x[0],x[1]))[:40]:
        compact=re.sub(r"\s+"," ",body)
        print(f"\n### FUNCTION {name}({args}) SCORE={score} LEN={len(body)}")
        print(compact[:2600])
    pats=[
        r"nationalFixtures",r"\.result\s*=",r"result\s*:",r"pens",r"xg",
        r"overall\(",r"E\.rng\(",r"rng\(",r"strength",r"simulate"
    ]
    seen=set()
    for pat in pats:
        print(f"\n===== PATTERN {pat} =====")
        for m in list(re.finditer(pat,html,re.I))[:30]:
            a=max(0,m.start()-700); b=min(len(html),m.end()+1200)
            key=(a,b)
            if key in seen: continue
            seen.add(key)
            snip=re.sub(r"\s+"," ",html[a:b])
            print(f"@{m.start()} {snip}")

if __name__=="__main__": main()
