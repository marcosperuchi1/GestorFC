# FutBR Manager — Android Alpha

Esta ramificação mantém o jogo Windows intacto e empacota o gameplay 18.331
para testes Android, sem publicar nada na Google Play.

## APKs de teste

Abra a aba **Actions** do repositório e escolha um dos fluxos:

- **Build FutBR Manager Android Alpha (APK)**: empacotamento com Tauri 2, ARM64.
- **Build FutBR Android Alpha (WebView APK fallback)**: alternativa WebView, também com base 18.331.

Dentro da execução aprovada, baixe **Artifacts**, extraia o ZIP e transfira o
arquivo .apk para o celular. Android 64-bit (ARM64) é o alvo primário.
O Android poderá solicitar permissão para instalar aplicativos por arquivo.

## Atenção no teste

- Os builds são assinados para desenvolvimento, não para a Play Store.
- Iniciar a carreira, salvar/carregar, login Supabase e avanço de temporada
  ainda precisam de teste em hardware real Android.
- Interface e prancheta priorizam paisagem; podem ter itens pequenos,
  rolagens e sobreposições na primeira versão.
- Saves são mantidos localmente no app. **Desinstalar pode apagar os saves**.
  Eles **não são sincronizados com o instalador Windows**.
- Compras Premium nas lojas e suporte iOS não fazem parte deste APK.
- Não atualize ou substitua o build Windows atual com os arquivos deste branch.

Ao reportar erro, informar modelo do celular, versão Android, tela/ação,
e capturas, especialmente na abertura da base e início da carreira.
