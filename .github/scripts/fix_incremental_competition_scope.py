from __future__ import annotations

import json
import sys
from pathlib import Path


def fail(message: str) -> None:
    raise RuntimeError(message)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: fix_incremental_competition_scope.py <project-dir>")

    project = Path(sys.argv[1]).resolve()
    index_path = project / "src" / "index.html"
    html = index_path.read_text(encoding="utf-8")

    if "FUTBR_INCREMENTAL_COMPETITION_SCOPE_18302" in html:
        print("Escopo incremental 18.302 ja corrigido")
        return
    if "FUTBR_INCREMENTAL_CLUB_RANKING_18301_START" not in html:
        fail("ranking incremental 18.301 ausente")

    old = r'''function v18301CompetitionClubs(s,stage,fixture,affected){
 const add=id=>{if(id)affected.add(id);};
 const competitionId=fixture?.competition||stage?.competition||stage?.competitionId;
 const competition=competitionId?s.competitions?.[competitionId]:null;
 if(competition){
  for(const id of competition.participants||[])add(id);
  for(const id of Object.keys(competition.standings||{}))add(id);
  for(const group of competition.groups||[])for(const id of group||[])add(id);
  for(const ties of Object.values(competition.rounds||{}))for(const tie of Array.isArray(ties)?ties:[]){add(tie?.a);add(tie?.b);add(tie?.winner);}
 }
 const country=fixture?.country||stage?.country,division=Number(fixture?.division??stage?.division);
 if(country&&Number.isFinite(division))for(const team of s.teams||[])if(team.country===country&&Number(team.division||1)===division)add(team.id);
}'''

    new = r'''function v18301CompetitionClubs(s,stage,fixture,affected){
 const add=id=>{if(id)affected.add(id);};
 const competitionId=fixture?.competition||stage?.competition||stage?.competitionId;
 const competition=competitionId?s.competitions?.[competitionId]:null;
 let scoped=false;
 if(competition){
  for(const id of competition.participants||[]){add(id);scoped=true;}
  for(const id of Object.keys(competition.standings||{})){add(id);scoped=true;}
  for(const group of competition.groups||[])for(const id of group||[]){add(id);scoped=true;}
  for(const ties of Object.values(competition.rounds||{}))for(const tie of Array.isArray(ties)?ties:[]){if(tie?.a){add(tie.a);scoped=true;}if(tie?.b){add(tie.b);scoped=true;}if(tie?.winner){add(tie.winner);scoped=true;}}
 }
 // O fallback por pais/divisao so existe para formatos legados que nao possuem
 // participantes/standings/grupos. Quando a competicao ja delimita seus clubes,
 // jamais ampliar a atualizacao para todos os clubes do pais.
 const country=fixture?.country||stage?.country,division=Number(fixture?.division??stage?.division);
 if(!scoped&&country&&Number.isFinite(division))for(const team of s.teams||[])if(team.country===country&&Number(team.division||1)===division)add(team.id);
}'''

    count = html.count(old)
    if count != 1:
        fail(f"funcao v18301CompetitionClubs inesperada: encontrado {count}")
    html = html.replace(old, new, 1)

    marker = "/* FUTBR_INCREMENTAL_COMPETITION_SCOPE_18302 */"
    insert_at = html.find("/* FUTBR_INCREMENTAL_CLUB_RANKING_18301_END */")
    if insert_at < 0:
        fail("fim do bloco incremental 18.301 ausente")
    html = html[:insert_at] + marker + "\n" + html[insert_at:]

    for required in (
        marker,
        "if(!scoped&&country&&Number.isFinite(division))",
        "Quando a competicao ja delimita seus clubes",
    ):
        if required not in html:
            fail("marcador de escopo ausente: " + required)

    report = {
        "ok": True,
        "version": "18.302",
        "explicitCompetitionScope": True,
        "countryDivisionFallbackOnlyWithoutParticipants": True,
        "worldWideRecalculationPrevented": True,
    }
    (project / "incremental-ranking-18302-install.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    index_path.write_text(html, encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
