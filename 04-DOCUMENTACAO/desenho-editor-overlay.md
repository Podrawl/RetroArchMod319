# Desenho do editor de overlay (RASCUNHO, nada implementado)

Base: RetroArch master (commit lido em 01-ANALISE/overlay-viewport*/00-commit.txt).

## Comportamento
- Entrada de menu: Configurações > Tela e Overlay > "Editar layout do overlay" (mesmas listas que as outras opções).
- Pausa o jogo, mostra overlay ativo + caixa da tela do jogo. Arrastar botões, arrastar/redimensionar a caixa da tela. Salvar / Cancelar.
- Ao salvar, pergunta: "Só este jogo" ou "Todos os jogos deste sistema (núcleo)".
- Salva COPIA ao lado do .cfg original (ex.: psx.cfg -> psx-meu.cfg), mantendo caminhos das imagens. Original nunca é alterado.
- "Global de verdade" (todos os consoles) NAO é oferecido: aplicaria layout de PS1 no GBA.

## Confirmado no código (01-ANALISE)
- Escolha do overlay: settings->paths.path_overlay (`input_overlay`), com preset manual; auto-escolha em gamepads/Named_Overlays só se opção ligada e sem preset.
- Overrides (núcleo/jogo) existem: config_load_override / config_save_overrides em configuration.c.
- Página de overlay tem viewport próprio (struct overlay.viewport, flag OVERLAY_HAS_VIEWPORT, chave `overlayN_viewport` em tasks/task_overlay.c). Vídeo lê isso em video_driver.c (set_overlay_viewport).
- Funções de escala/recalculo: input_overlay_scale, input_overlay_set_scale_factor, input_overlay_update_desc_geom (input/input_driver.c).

## Hipóteses (verificar antes de codar)
- Nome/forma exata do modo "fill" do viewport no .cfg.
- Como interceptar o toque no android_input.c sem acionar botões do jogo.
- Como adicionar entrada nova nos menus Ozone / MaterialUI / XMB / RGUI.
- Comportamento de salvar override por núcleo vs por jogo para `input_overlay`.

## Etapas propostas (cada uma gera APK de teste)
0. Build de teste com nome de pacote próprio (instala ao lado do seu RetroArch).
1. Entrada de menu + tela de edição que só mostra caixas (sem salvar).
2. Arrastar/redimensionar botões e viewport (só na memória).
3. Salvar cópia .cfg + escolha jogo/núcleo.
4. Acabamento (grade, desfazer, várias páginas, retrato/paisagem).
