from __future__ import annotations
import json, sys
from pathlib import Path

def find_function(src, name):
    pats=[f"async function {name}(",f"function {name}("]
    start=-1
    for p in pats:
        start=src.find(p)
        if start>=0:
            break
    if start<0:
        return None
    brace=src.find("{",start)
    if brace<0:
        return None
    depth=0;quote=None;esc=False
    for i in range(brace,len(src)):
        ch=src[i]
        if quote:
            if esc:
                esc=False
            elif ch=="\\":
                esc=True
            elif ch==quote:
                quote=None
            continue
        if ch in ("'",'"',chr(96)):
            quote=ch
            continue
        if ch=="{":
            depth+=1
        elif ch=="}":
            depth-=1
            if depth==0:
                return src[start:i+1]
    return src[start:start+12000]

def contexts(src, term, radius=1000, limit=20):
    out=[];pos=0
    while len(out)<limit:
        i=src.find(term,pos)
        if i<0:
            break
        out.append(src[max(0,i-radius):min(len(src),i+len(term)+radius)])
        pos=i+len(term)
    return out

def main():
    if len(sys.argv)!=2:
        raise SystemExit("usage: diagnose_boot_performance.py <project-dir>")
    root=Path(sys.argv[1]).resolve()
    html=(root/"src"/"index.html").read_text(encoding="utf-8")
    body=html.find("<body")
    report={
      "html_bytes":len(html.encode()),
      "body_prefix_repr":repr(html[body:body+900]) if body>=0 else None,
      "literal_backslash_n_total":html.count("\\n"),
      "functions":{},
      "contexts":{},
    }
    for name in [
      "loadLocal","loadSelected","renderWelcome","v548EnterGame","v548RenderAuth",
      "doSave","saveSharded","writeCollection","dbWrite","v171DecodeManifest",
      "v52FlushSave","v52SaveNow","v52ScheduleSave","v53Call"
    ]:
      block=find_function(html,name)
      report["functions"][name]=block[:24000] if block else None
    for term in [
      "\\n","loadLocal();","await loadLocal()","v548Session","DOMContentLoaded",
      "window.onload","op==='create'","op===\"create\"","v53Creating",
      "saveSharded(state","saveSharded(s","doSave(","v52FlushSave()",
      "writeMany(","raw-write-many","indexeddb-hot-sqlite-manual-sync"
    ]:
      report["contexts"][term]=contexts(html,term,1200,16)
    out=root/"boot-performance-diagnostic.json"
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({
      "ok":True,
      "html_bytes":report["html_bytes"],
      "literal_backslash_n_total":report["literal_backslash_n_total"],
      "functions_found":[k for k,v in report["functions"].items() if v]
    },ensure_ascii=False))

if __name__=="__main__":
    main()
