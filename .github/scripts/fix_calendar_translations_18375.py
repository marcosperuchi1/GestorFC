"""Complete the existing multilingual dictionary for the live calendar and common settings."""
from pathlib import Path
import hashlib,json,sys

MARK='FUTBR_CALENDAR_TRANSLATIONS_18375'
ROWS=r'''/* FUTBR_CALENDAR_TRANSLATIONS_18375 */
const extraCalendarTranslations18375=[
 ['Calendário de jogos','Match calendar','Calendario de partidos','Calendário de jogos'],
 ['Calendário {0}','Calendar {0}','Calendario {0}','Calendário {0}'],
 ['Data esportiva','Match date','Fecha deportiva','Data desportiva'],
 ['Seu confronto','Your fixture','Tu enfrentamiento','O seu encontro'],
 ['Seu adversário','Your opponent','Tu rival','O seu adversário'],
 ['Seu clube e o andamento global','Your club and the wider season','Tu club y el calendario mundial','O seu clube e a época global'],
 ['Temporada inteira','Full season','Temporada completa','Época completa'],
 ['Próximos jogos','Upcoming fixtures','Próximos partidos','Próximos jogos'],
 ['Próximas partidas','Upcoming matches','Próximos partidos','Próximos jogos'],
 ['Aguardando esta data e os classificados.','Waiting for this date and qualified teams.','Esperando esta fecha y los clasificados.','A aguardar esta data e as equipas apuradas.'],
 ['Sem jogos nesta fase; clubes entram nas fases seguintes.','No matches in this stage; teams enter in later rounds.','No hay partidos en esta fase; los clubes entran en rondas posteriores.','Sem jogos nesta fase; os clubes entram nas rondas seguintes.'],
 ['Sem partida do seu clube nesta data.','Your club has no match on this date.','Tu club no tiene partido en esta fecha.','O seu clube não joga nesta data.'],
 ['Mandante','Home','Local','Em casa'],
 ['Visitante','Away','Visitante','Visitante'],
 ['Local do jogo','Venue','Sede del partido','Local do jogo'],
 ['Competição','Competition','Competición','Competição'],
 ['Jornada','Matchday','Jornada','Jornada'],
 ['Mando','Venue','Localía','Casa/fora'],
 ['Adversário','Opponent','Rival','Adversário'],
 ['Resultado','Result','Resultado','Resultado'],
 ['Primeira fase','First round','Primera fase','Primeira fase'],
 ['Quartas de final','Quarter-finals','Cuartos de final','Quartos de final'],
 ['Semifinal','Semi-final','Semifinal','Meia-final'],
 ['Oitavas','Round of 16','Octavos','Oitavos de final'],
 ['Quadrangular','Four-team group','Cuadrangular','Grupo de quatro equipas'],
 ['Rodada {0}','Round {0}','Jornada {0}','Jornada {0}'],
 ['Jornada {0}','Matchday {0}','Jornada {0}','Jornada {0}'],
 ['Aguardando definição','To be confirmed','Por definir','Por definir'],
 ['Aguardando os classificados','Waiting for qualified clubs','Esperando los clasificados','A aguardar os apurados'],
 ['Configurações gerais','General settings','Ajustes generales','Definições gerais'],
 ['Tamanho dos textos e controles','Text and control size','Tamaño de textos y controles','Tamanho dos textos e controlos'],
 ['Tela cheia','Full screen','Pantalla completa','Ecrã inteiro'],
 ['Modo janela','Windowed mode','Modo ventana','Modo janela']
];
for(const row of ROWS.concat(extraCalendarTranslations18375))add(row);'''
def main():
 root=Path(sys.argv[1]).resolve();path=root/'src/index.html';s=path.read_text(encoding='utf-8')
 if MARK in s:raise RuntimeError('Already installed')
 anchor='for(const row of ROWS)add(row);'
 if s.count(anchor)!=1:raise RuntimeError('Could not locate original translator exact dictionary')
 s=s.replace(anchor,ROWS,1)
 path.write_text(s,encoding='utf-8')
 (root/'calendar-translations-18375-install.json').write_text(json.dumps({'ok':True,'sourceSha256':hashlib.sha256(s.encode()).hexdigest(),'addedLocales':['en','es','pt-PT']},indent=2),encoding='utf-8')
if __name__=='__main__':main()
