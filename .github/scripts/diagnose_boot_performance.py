from __future__ import annotations
import json, subprocess, sys
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


def run_script(script: Path, root: Path) -> str:
    result=subprocess.run([sys.executable,str(script),str(root)],capture_output=True,text=True)
    if result.returncode:
        raise RuntimeError(f"{script.name} falhou:\n{(result.stderr or result.stdout)[-6000:]}")
    return result.stdout.strip()


def main():
    if len(sys.argv)!=2:
        raise SystemExit("usage: diagnose_boot_performance.py <project-dir>")
    root=Path(sys.argv[1]).resolve()
    scripts=Path(__file__).resolve().parent

    # Esta etapa e executada imediatamente depois do finalizador do HTML. Assim,
    # a correcao da MLS fica sobre o arquivo definitivo e e testada antes do Rust.
    applied={}
    for name in ["fix_mls_vacation.py","fix_mls_vacation_ui.py"]:
        applied[name]=run_script(scripts/name,root)
    mls_test_output=run_script(scripts/"test_mls_vacation.py",root)
    mls_report=json.loads((root/"mls-vacation-tests.json").read_text(encoding="utf-8"))

    html=(root/"src"/"index.html").read_text(encoding="utf-8")
    body=html.find("<body")
    report={
      "html_bytes":len(html.encode()),
      "body_prefix_repr":repr(html[body:body+900]) if body>=0 else None,
      "literal_backslash_n_total":html.count("\\n"),
      "mls_vacation_fix":{
        "applied":applied,
        "test_output":mls_test_output,
        "result":mls_report,
      },
      "functions":{},
      "contexts":{},
    }
    for name in [
      "loadLocal","loadSelected","renderWelcome","v548EnterGame","v548RenderAuth",
      "doSave","saveSharded","writeCollection","dbWrite","v171DecodeManifest",
      "v52FlushSave","v52SaveNow","v52ScheduleSave","v52EncodeSnapshot","v52RequestSave","persist","saveLocal","ensureSaved","v53Saved","v53Prepare","v53Call",
      "v18200MLSResultWinner","v18200MLSRepairState","v18200MLSRecover"
    ]:
      block=find_function(html,name)
      report["functions"][name]=block[:24000] if block else None
    for term in [
      "\\n","loadLocal();","await loadLocal()","v548Session","DOMContentLoaded",
      "window.onload","op==='create'","op===\"create\"","v53Creating",
      "saveSharded(state","saveSharded(s","doSave(","v52FlushSave()",
      "writeMany(","raw-write-many","indexeddb-hot-sqlite-manual-sync",
      "futbr-mls-vacation-18200-meta","futbr-mls-vacation-18201-ui","v18201-vac-nextmatch"
    ]:
      report["contexts"][term]=contexts(html,term,1200,16)
    out=root/"boot-performance-diagnostic.json"
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({
      "ok":True,
      "html_bytes":report["html_bytes"],
      "literal_backslash_n_total":report["literal_backslash_n_total"],
      "mls_vacation":mls_report,
      "functions_found":[k for k,v in report["functions"].items() if v]
    },ensure_ascii=False))


if __name__=="__main__":
    main()
