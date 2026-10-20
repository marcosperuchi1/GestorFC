from __future__ import annotations
import json,re,sys
from pathlib import Path

def die(msg): raise RuntimeError(msg)

def function_block(src,name):
    m=re.search(r'(?:async\s+)?function\s+'+re.escape(name)+r'\s*\(',src)
    if not m: die(name+' ausente')
    b=src.find('{',m.end());depth=0;quote=None;esc=False
    for i in range(b,len(src)):
        ch=src[i]
        if quote:
            if esc: esc=False
            elif ch=='\\': esc=True
            elif ch==quote: quote=None
            continue
        if ch in ("'",'"','\`'): quote=ch; continue
        if ch=='{': depth+=1
        elif ch=='}':
            depth-=1
            if depth==0: return src[m.start():i+1]
    die(name+' nao fechada')

def main():
    if len(sys.argv)!=2: raise SystemExit('usage: test_login_boot.py <project-dir>')
    root=Path(sys.argv[1]).resolve()
    html=(root/'src'/'index.html').read_text(encoding='utf-8')
    enter=function_block(html,'v548EnterGame')
    boot=function_block(html,'v548Boot')

    if 'await loadLocal()' in enter or 'await loadLocal(false)' in enter:
        die('v548EnterGame ainda chama loadLocal pesado')
    if 'await v260FastLoadLocal(false)' not in enter:
        die('v548EnterGame nao usa carregamento rapido')
    if 'Promise.resolve().then(()=>loadLocal(false))' in boot:
        die('boot ainda usa loadLocal pesado')
    if 'Promise.resolve().then(()=>v260FastLoadLocal(false))' not in boot:
        die('boot nao usa carregamento rapido')
    if 'base local para nova carreira' not in enter:
        die('base inicial nao ficou restrita ao fluxo posterior de nova carreira')

    submit_marker="document.addEventListener('submit',async e=>"
    si=html.find(submit_marker)
    if si<0: die('submit de login ausente')
    se=html.find("document.addEventListener('click'",si)
    block=html[si:se if se>si else si+5000]
    if 'v310StartRosterLoad' in block or 'v310EnsureRosterTextSync' in block or 'v310RosterSlice' in block:
        die('submit de login ainda toca diretamente na base inicial')

    result={
      'ok':True,
      'loginUsesFastMetadataLoad':True,
      'bootUsesFastMetadataLoad':True,
      'loginRosterIndependent':True,
      'newCareerRosterDeferred':True
    }
    (root/'login-boot-tests.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__': main()
