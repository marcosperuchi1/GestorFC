from __future__ import annotations
import sys
from pathlib import Path

def fail(msg):
    raise RuntimeError(msg)

def function_end(text: str, start: int) -> int:
    brace = text.find('{', start)
    if brace < 0:
        fail('Abertura da funcao helpPage nao encontrada.')
    depth = 0
    quote = None
    escape = False
    i = brace
    while i < len(text):
        ch = text[i]
        if quote:
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == quote:
                quote = None
        else:
            if ch in ("'", '"'):
                quote = ch
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return i + 1
        i += 1
    fail('Fim da funcao helpPage nao encontrado.')

def main():
    if len(sys.argv) != 2:
        raise SystemExit('usage: finalize_how_to_play.py <project-dir>')
    project = Path(sys.argv[1]).resolve()
    path = project / 'src' / 'index.html'
    html = path.read_text(encoding='utf-8')

    marker = 'function helpPage(){'

    replacement = r'''function helpPage(){
 const sections=[
  ["Seu objetivo","Assuma a carreira de treinador e construa sua trajetória no futebol. Administre o dia a dia, dispute títulos, desenvolva sua reputação e aproveite as oportunidades que surgirem ao longo das temporadas. Você pode comandar clubes e, quando disponível para sua carreira, seleções nacionais."],
  ["Elenco e táticas","Use Elenco e Táticas para escolher titulares, reservas, formação e instruções. A qualidade dos jogadores, o encaixe nas posições, o condicionamento e as decisões táticas influenciam o desempenho. Arraste atletas para reorganizar a equipe e adapte o time ao adversário e ao momento da partida. Não existe formação que garanta vitória."],
  ["Partidas","Você pode acompanhar os jogos e intervir durante a partida, alterando formação, instruções e fazendo substituições. O resultado considera a força real das equipes, escalações, tática, desgaste, mando quando aplicável e a variação natural do futebol. Favoritos têm vantagem, mas zebras continuam possíveis."],
  ["Competições e mundo","A carreira acontece em um mundo de futebol conectado, com ligas, copas, competições continentais e intercontinentais, além do futebol de seleções e seus torneios. Resultados em outros países continuam sendo simulados enquanto sua carreira avança."],
  ["Mercado e contratos","No Mercado você pode contratar, vender e negociar jogadores. Observe valor, salário, duração de contrato e necessidades do elenco antes de decidir. Clubes controlados pela IA também negociam e reorganizam seus grupos ao longo das temporadas."],
  ["Finanças e estrutura","O desempenho esportivo precisa caminhar junto com a gestão financeira. Acompanhe caixa, salários e receitas e invista na estrutura do clube quando fizer sentido. Decisões financeiras ruins podem limitar suas opções no mercado e aumentar a pressão sobre o treinador."],
  ["Base e evolução","As categorias de base ajudam a renovar o elenco com jovens. Jogadores evoluem de acordo com idade, potencial e desenvolvimento, enquanto veteranos podem perder rendimento e se aposentar. O mundo se renova continuamente entre as temporadas."],
  ["Carreira do treinador","Resultados, títulos e desempenho constroem sua reputação. Você pode receber propostas, trocar de clube, ser demitido e seguir a carreira em outro trabalho. As férias permitem avançar períodos automaticamente e podem ser interrompidas quando houver acontecimentos importantes."],
  ["Salvar e continuar","A carreira é salva pelo próprio jogo. Use também as opções de backup e exportação quando quiser manter uma cópia adicional dos seus dados. Antes de substituir arquivos, limpar dados do aplicativo ou trocar de computador, mantenha um backup da carreira que deseja preservar."]
 ];
 return pageHeading("Como jogar","Um resumo do FutBR Manager e dos principais caminhos para construir sua carreira.")+
  '<div class="help-grid">'+sections.map(([title,text])=>'<section class="help-section"><h3>'+title+'</h3><p>'+text+'</p></section>').join('')+'</div>';
}'''

    starts = []
    pos = 0
    while True:
        start = html.find(marker, pos)
        if start < 0:
            break
        starts.append(start)
        pos = start + len(marker)
    if not starts:
        fail('Nenhuma implementacao de helpPage encontrada.')

    # Ha mais de uma camada historica do jogo que redefine helpPage.
    # Todas precisam receber o mesmo conteudo final; alterar apenas a ultima
    # pode deixar uma implementacao anterior ativa em outro escopo.
    ranges = [(start, function_end(html, start)) for start in starts]
    for start, end in reversed(ranges):
        html = html[:start] + replacement + html[end:]

    # Validacao forte: nenhuma implementacao de helpPage pode manter
    # changelog, migracao ou texto de edicoes antigas.
    check_pos = 0
    checked = 0
    while True:
        start = html.find(marker, check_pos)
        if start < 0:
            break
        end = function_end(html, start)
        body = html[start:end]
        for old in ['Edição 5.0. Seu mundo continua presente.','Migrar a carreira','O que permanece','Importe o JSON 4.0.','O que esta edição inclui','O que esta edicao inclui']:
            if old in body:
                fail('Texto historico ainda presente em helpPage: ' + old)
        for item in ['Seu objetivo','Elenco e táticas','Partidas','Competições e mundo','Mercado e contratos','Carreira do treinador','Salvar e continuar']:
            if item not in body:
                fail('Secao obrigatoria ausente de helpPage: ' + item)
        checked += 1
        check_pos = end

    path.write_text(html, encoding='utf-8')
    print(f'Como jogar finalizado em {checked} implementacao(oes), sem historico de versoes.')

if __name__ == '__main__':
    main()
