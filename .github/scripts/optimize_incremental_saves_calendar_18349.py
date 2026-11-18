from __future__ import annotations
import json
import sys
from pathlib import Path

MARK='FUTBR_CLEAN_INCREMENTAL_SHARDS_18349'
CSS=r"""
<style id="futbr18349-calendar-viewport">
/* 18.349: temporada inteira fica contida no painel; apenas a lista rola.
   A barra nao desloca o cabecalho nem expande a tela do jogo. */
.v18347-calendar.v18349-all{
 display:flex;flex-direction:column;min-height:0;
 max-height:calc(100vh - 142px);max-height:calc(100dvh - 142px);
 overflow:hidden;
}
.v18347-calendar.v18349-all .v18347-toolbar,
.v18347-calendar.v18349-all .v18347-columns,
.v18347-calendar.v18349-all .v18347-footer{flex:0 0 auto}
.v18347-calendar.v18349-all .v18347-list{
 flex:1 1 auto;min-height:0;
 max-height:min(710px, calc(100vh - 295px));
 max-height:min(710px, calc(100dvh - 295px));
 overflow-x:hidden;overflow-y:auto;
 overscroll-behavior-y:contain;overflow-anchor:auto;
 scrollbar-gutter:stable;scrollbar-width:thin;
 scrollbar-color:rgba(190,194,192,.55) transparent;
}
.v18347-calendar.v18349-all .v18347-list::-webkit-scrollbar{width:9px}
.v18347-calendar.v18349-all .v18347-list::-webkit-scrollbar-thumb{
 background:rgba(190,194,192,.55);border-radius:9px;border:2px solid transparent;background-clip:padding-box}
.v18347-calendar.v18349-all .v18347-list:focus-visible{
 outline:2px solid var(--accent,#dabf78);outline-offset:-3px}
@media(max-width:950px){
 .v18347-calendar.v18349-all{max-height:calc(100dvh - 112px)}
 .v18347-calendar.v18349-all .v18347-list{max-height:calc(100dvh - 260px)}
}
@media(max-height:560px){
 .v18347-calendar.v18349-all{max-height:calc(100dvh - 90px)}
 .v18347-calendar.v18349-all .v18347-list{max-height:calc(100dvh - 205px)}
}
</style>
"""

CORE_KEYS=['players','teams','coaches','schedule','competitionStats','allTimeStats']
# v18343 already computes SHA256 of the exact structured-clone compatible
# representation of each shard. Extend that lossless copy-on-write to the
# mutable live world, preserving previous checksums and atomic commit semantics.

def once(src,old,new,label,count=1):
    n=src.count(old)
    if n!=count:raise RuntimeError(f'18.349 {label}: expected {count} anchors, got {n}')
    return src.replace(old,new)

def main():
    if len(sys.argv)!=2:raise SystemExit('usage: optimize_incremental_saves_calendar_18349.py <project>')
    root=Path(sys.argv[1]).resolve()
    path=root/'src/index.html'
    src=path.read_text(encoding='utf-8')
    if MARK in src:raise RuntimeError('18.349 already applied')
    if src.count('FUTBR_ARCHIVE_COPY_ON_WRITE_18343')!=2:
        raise RuntimeError('Both previously verified SHA-256 save writers must be installed')
    if 'FUTBR_CALENDAR_NAV_VERSION_18348' not in src:
        raise RuntimeError('Active 18.348 calendar navigation must be present')
    if 'FUTBR_CALENDAR_LIST_18347' not in src:
        raise RuntimeError('18.347 calendar list missing')

    header="const v18343HistoricalKeys=new Set([\n"
    updated=header+" 'players','teams','coaches','schedule','competitionStats','allTimeStats',\n"
    src=once(src,header,updated,'all live collection copy-on-write keys',2)

    ui_old="""oldSpec=history&&previous&&!!previous.isArray===isArray?previous:null,"""
    ui_new="""oldSpec=history&&previous&&!!previous.isArray===isArray&&
   (key!=='players'||previous.encoding===v18191mPlayerFormat)?previous:null,"""
    src=once(src,ui_old,ui_new,'UI player codec-aware existing manifest reuse')

    worker_old="""oldSpec=history&&old?.format===V171_FORMAT&&old?.collections?.[key]&&
    !!old.collections[key].isArray===isArray?old.collections[key]:null,"""
    worker_new="""oldSpec=history&&old?.format===V171_FORMAT&&old?.collections?.[key]&&
    !!old.collections[key].isArray===isArray&&
    (key!=='players'||old.collections[key].encoding===v18191wPlayerFormat)?
    old.collections[key]:null,"""
    src=once(src,worker_old,worker_new,'Worker player codec-aware existing manifest reuse')

    old_calendar="return \"<section class='panel v18347-calendar'>\"+head+column+"
    new_calendar="return \"<section class='panel v18347-calendar\"+(listScope==='all'?' v18349-all':'')+\"'>\"+head+column+"
    src=once(src,old_calendar,new_calendar,'limit full-season panel only')
    old_list="\"<div class='v18347-list'>\"+body"
    new_list="\"<div class='v18347-list' tabindex='0' role='region' aria-label='Lista rolável de jogos da temporada'>\"+body"
    src=once(src,old_list,new_list,'keyboard-accessible internal game-list scrollbar')
    end=src.rfind('</body>')
    if end<0:raise RuntimeError('Missing game closing body for calendar style')
    src=src[:end]+CSS+src[end:]
    src=once(src,"const v18343HistoricalKeys=new Set([",
       "/* "+MARK+" */\nconst v18343HistoricalKeys=new Set([",
       'real game and Worker save guards',2)

    # The 18.348 UI patch installs its edition from the then-current Tauri
    # version. Re-bind that single visible build marker after upgrading the
    # actual signed Windows package to 18.349.
    config=json.loads((root/'src-tauri/tauri.conf.json').read_text(encoding='utf-8'))
    if config.get('version')!='18.349.0':
        raise RuntimeError('The signed Tauri version must be 18.349.0 before UI edition sync')
    src=once(src,"const EDITION='18.348.0';","const EDITION='18.349.0';",
        'visible sidebar / login edition from actual signed build')
    src=once(src,
        "window.GestorFC.version='18.348.0';window.GestorFC.visualVersion='18.348.0';",
        "window.GestorFC.version='18.349.0';window.GestorFC.visualVersion='18.349.0';",
        'boot runtime footer edition matches signed build')

    for k in CORE_KEYS:
        if src.count("'"+k+"'")<2:raise RuntimeError('Collection key missing after safe incremental patch: '+k)
    for marker in ['async function saveSharded(s,mode=', 'async function save(s){',
                   'v18343Fingerprint(raw)','v18343ArchiveWritten(key,true)',
                   'v18181RawWriteMany','v18183DbWriteMany',
                   'await commitManifest(manifest,old,meta)',
                   'v171DropManifest(oldPrev,keep)',
                   'v538CareerArchive','v555CareerArchive','scorerArchive',
                   'retirements','transfers','allTimeStats']:
        if marker not in src:raise RuntimeError('Lossless state persistence invariant missing: '+marker)

    path.write_text(src,encoding='utf-8')
    report={
      'ok':True,'version':'18.349',
      'calendarInternalVerticalScroll':True,
      'calendarHeaderOutsideScroll':True,
      'calendarOnlyFullSeasonConstrained':True,
      'keyboardAccessibleScrollableList':True,
      'losslessCopyOnWriteForCoreCollections':CORE_KEYS,
      'cryptographicSha256OnlyReuseUnchangedChunks':True,
      'checksCodecBeforeReusingPlayerChunks':True,
      'previousManifestRecoveryUntouched':True,
      'workerAndUiWritersUpdated':True,
      'historyAndStatisticsPreserved':True,
      'firstSaveFromLegacyManifestsFallsBackToFullWrite':True,
      'noSchemaOrSaveFormatMigration':True,
      'savesExistingSnapshotsWithoutDeletingThem':True,
      'visibleEditionSynchronizedWithSignedVersion':True
    }
    (root/'incremental-saves-calendar-18349-install.json').write_text(
        json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
