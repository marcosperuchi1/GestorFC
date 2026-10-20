from __future__ import annotations
import re, sys
from pathlib import Path


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        fail(f"{label}: esperado 1, encontrado {count}")
    return text.replace(old, new, 1)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: finalize_prebuilt_boot.py <project-dir>")
    project = Path(sys.argv[1]).resolve()
    index_path = project / "src" / "index.html"
    html = index_path.read_text(encoding="utf-8")

    # A base consolidada ja existe neste ponto do pipeline. Daqui em diante,
    # nenhum codigo de compatibilidade pode decodificar elencos durante o boot.
    html = replace_once(
        html,
        "function v310RosterRecord(id){\n if(v310RosterDeleted.has(id))return undefined;",
        "function v310RosterRecord(id){\n if(!v310RosterText&&!V310_BOOTSTRAP_ROSTERS[id])return undefined;\n if(v310RosterDeleted.has(id))return undefined;",
        "guarda de leitura sincrona da base",
    )

    # Correcoes antigas ja foram materializadas pelo consolidador no asset final.
    html = replace_once(
        html,
        "v526PrioritizeJoaquinRoster();\n\n// Bandeiras offline",
        "/* Joaquin/Joaquim Freitas ja esta ordenado no asset consolidado do build. */\n\n// Bandeiras offline",
        "priorizacao Joaquin no boot",
    )

    old_anthony = """// Corrige a identidade conhecida do Anthony Valencia nesta base antes de qualquer nova carreira.
(function v530PatchRosterFacts(){
 for(const source of [BundledRosters,rosterCache]){
  const list=source?.t0?.players;if(!Array.isArray(list))continue;
  const p=list.find(x=>E.normName(x?.name||'')==='anthony valencia');if(p){p.age=23;p.ageEstimated=false;}
 }
})();"""
    html = replace_once(
        html,
        old_anthony,
        "// Anthony Valencia ja esta corrigido no asset consolidado gerado no build.\n// Nenhum elenco e consultado durante a avaliacao inicial da pagina.",
        "correcao Anthony no boot",
    )

    old_fluminense = """// 18.3 database correction: Fluminense starts new careers with Marcão (BRA).
try{const v183FluBase=v310RosterRecord('t6');if(v183FluBase){v310RosterOverrides.t6={...v183FluBase,coach:{...(v183FluBase.coach||{}),name:'Marcão',natCode:'BRA',real:true,source:'Editor local FutBR Manager 18.3',fetchedAt:'2026-10-06'}};v310RosterCache.delete('t6');}}catch(e){}"""
    html = replace_once(
        html,
        old_fluminense,
        "// Marcao (BRA) no Fluminense ja esta gravado no asset consolidado do build.\n// Nao consultar t6 durante o boot.",
        "correcao Fluminense no boot",
    )

    # Este sweep existia apenas para preparar os 256 registros mantidos no cache.
    # O consolidador ja aplicou as mesmas correcoes ao arquivo definitivo.
    sweep = re.compile(
        r"// Previously the age and position sweeps ran before v206SupportNames\.\n"
        r"for\(const t of \(WorldCatalog\.clubs\|\|\[\]\)\.slice\(-256\)\)\{\n"
        r" const roster=BundledRosters\[t\.id\];\n"
        r" if\(!roster\)continue;\n"
        r" v515ApplyPositionFixesToItem\(t\.id,roster\);\n"
        r" for\(const p of roster\.players\|\|\[\]\)\{\n"
        r"  if\(Number\.isFinite\(Number\(p\.age\)\)&&Number\(p\.age\)>=14&&Number\(p\.age\)<=60\)p\.ageEstimated=false;\n"
        r" \}\n"
        r" v206RenameSupportRoster\(t,roster\);\n"
        r"\}\n"
    )
    match = sweep.search(html)
    if not match:
        fail("sweep legado dos 256 elencos nao encontrado")
    html = (
        html[: match.start()]
        + "// Posicoes, idades e nomes dos 256 registros finais ja foram consolidados no asset durante o build.\n"
          "// O boot nao percorre elencos.\n"
        + html[match.end() :]
    )

    old_meta = """function v691RefreshMeta(){
 EditionMeta.clubs=WorldCatalog.clubs.length;
 EditionMeta.leagues=new Set(WorldCatalog.clubs.map(t=>t.country+':'+(Number(t.division)||1))).size;
 EditionMeta.realPlayers=Object.values(rosterCache||{}).reduce((n,r)=>n+(r?.players?.length||0),0);
}"""
    new_meta = """function v691RefreshMeta(){
 EditionMeta.clubs=WorldCatalog.clubs.length;
 EditionMeta.leagues=new Set(WorldCatalog.clubs.map(t=>t.country+':'+(Number(t.division)||1))).size;
 const prebuilt=Number(window.GestorFC?.baseRosterStats310?.players);
 if(Number.isFinite(prebuilt)&&prebuilt>0)EditionMeta.realPlayers=prebuilt;
 else if(typeof v310RosterText==='string'&&v310RosterText)EditionMeta.realPlayers=Object.values(rosterCache||{}).reduce((n,r)=>n+(r?.players?.length||0),0);
}"""
    html = replace_once(html, old_meta, new_meta, "metadados sem varredura pre-login")

    # Monte o formulario imediatamente. A base de jogadores so pode ser aberta
    # depois que uma sessao valida existir. Isso vale tanto para sessao restaurada
    # quanto para login manual (v548EnterGame ja aguarda a base).
    old_boot = """async function v548Boot(){
 const localPreload=Promise.resolve().then(()=>v260FastLoadLocal(false)).catch(e=>{console.warn('[FutBR] leitura local no boot:',e?.message||e);return null;});
 const rosterPreload=Promise.resolve().then(()=>v310StartRosterLoad()).catch(e=>{console.error('[FutBR] base instalada no boot:',e?.message||e);return null;});
 const authPromise=Promise.resolve().then(()=>v580RestoreRemoteSession()).catch(e=>{console.warn('[FutBR] sessao remota no boot:',e?.message||e);return null;});
 let timeoutId=0;
 const timeout=new Promise(resolve=>{timeoutId=setTimeout(()=>resolve(null),6000);});
 const authenticated=await Promise.race([authPromise,timeout]);
 if(timeoutId)clearTimeout(timeoutId);
 if(authenticated){
  await Promise.all([localPreload,rosterPreload]);
  if(!state)renderWelcome();
  return;
 }
 await localPreload;
 v548RenderAuth('login','Validando sua sessao. Se necessario, entre novamente.');
 authPromise.then(session=>{if(session&&!state){v548EnterGame().catch(e=>console.warn('[FutBR] entrada apos validacao:',e?.message||e));}}).catch(()=>{});
}"""
    new_boot = """async function v548Boot(){
 // O login deve existir visualmente antes de qualquer leitura da base de jogadores.
 v548RenderAuth('login','');
 const localPreload=Promise.resolve().then(()=>v260FastLoadLocal(false)).catch(e=>{console.warn('[FutBR] leitura local no boot:',e?.message||e);return null;});
 const authPromise=Promise.resolve().then(()=>v580RestoreRemoteSession()).catch(e=>{console.warn('[FutBR] sessao remota no boot:',e?.message||e);return null;});
 let timeoutId=0;
 const timeout=new Promise(resolve=>{timeoutId=setTimeout(()=>resolve(null),6000);});
 const authenticated=await Promise.race([authPromise,timeout]);
 if(timeoutId)clearTimeout(timeoutId);
 if(authenticated){
  await localPreload;
  await v310StartRosterLoad();
  if(!state)renderWelcome();
  return;
 }
 // Mantem o formulario ja montado. A base so sera aberta depois de login valido.
 authPromise.then(session=>{if(session&&!state){v548EnterGame().catch(e=>console.warn('[FutBR] entrada apos validacao:',e?.message||e));}}).catch(()=>{});
}"""
    html = replace_once(html, old_boot, new_boot, "boot autenticacao primeiro")

    html = replace_once(
        html,
        "rosterPreloadedDuringAuth:true,\n loginUiIndependentFromRoster:true,",
        "rosterPreloadedDuringAuth:false,\n loginUiIndependentFromRoster:true,\n rosterLoadAfterAuthentication:true,\n noRosterReadBeforeLogin:true,",
        "marcadores do boot",
    )

    # Invariantes da versao final que vai para o Tauri.
    boot_start = html.find("async function v548Boot(){")
    boot_end = html.find("\nv548Boot().catch", boot_start)
    if boot_start < 0 or boot_end < 0:
        fail("nao foi possivel localizar v548Boot final")
    boot = html[boot_start:boot_end]
    first_auth = boot.find("v548RenderAuth('login','');")
    first_roster = boot.find("v310StartRosterLoad()")
    if first_auth < 0 or first_roster < 0 or first_auth > first_roster:
        fail("boot final ainda pode tocar na base antes de montar o login")
    if "rosterPreload=" in boot:
        fail("preload de roster durante autenticacao ainda presente")
    if "await localPreload;\n v548RenderAuth" in boot:
        fail("login ainda espera leitura local")

    index_path.write_text(html, encoding="utf-8")
    print("prebuilt boot finalized: login-first, roster-after-auth")


if __name__ == "__main__":
    main()
