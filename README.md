# FutBR Manager - ultimo build de teste

Build Ranking incremental 18.301 · workflow #12.

- `FutBR-Manager-Desktop-RC1-INSTALADOR.exe`: instalador Windows.
- `FutBR-Manager-Desktop-RC1-PORTATIL.zip`: versao portatil.
- O aviso incorreto de salvamento web foi removido do executavel desktop.
- Mensagens tecnicas com tempo da virada de temporada nao sao exibidas ao usuario.
- O Ranking de Clubes passa a manter uma base persistente dentro do save.
- A primeira migracao calcula a base uma vez; depois somente clubes de competicoes afetadas e novos campeoes sao atualizados.
- J/V/E/D sao mantidos incrementalmente a cada novo resultado.
- A virada de temporada reutiliza a classificacao existente e nao reconstrói os 5.628 clubes.
- A metodologia original de pontuacao 6.33 foi preservada.
- As otimizacoes de base externa, saves fragmentados, SQLite e memoria de carreira longa permanecem ativas.

Esta branch e substituida integralmente a cada novo build aprovado.
