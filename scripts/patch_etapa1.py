#!/usr/bin/env python3
"""Etapa 1 do editor de overlay: SO a entrada de menu + entrar em modo de edicao
(fecha o menu, pausa o jogo, mostra aviso). Nao salva nada, nao move nada.
Uso: patch_etapa1.py <pasta_do_RetroArch>
Cada troca exige que o trecho exista EXATAMENTE uma vez; senao falha (nada de chute).
"""
import sys

raiz = sys.argv[1]


def trocar(arquivo, antigo, novo):
    caminho = f"{raiz}/{arquivo}"
    with open(caminho, encoding="utf-8") as f:
        s = f.read()
    n = s.count(antigo)
    if n != 1:
        sys.exit(f"ERRO: em {arquivo} o trecho aparece {n} vezes (esperado 1):\n{antigo}")
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(s.replace(antigo, novo))
    print(f"ok: {arquivo}")


# 1) Define a nova linha de menu (texto + enum gerados pelo sistema de X-macros).
trocar(
    "settings/settings_def_menu_main_lists_4.h",
    '''S_ACTION_EX(OVERLAY_MOUSE_SETTINGS,
      "overlay_mouse_settings", SD_FLAG_LAKKA_ADVANCED, NULL, NULL, 0,
      "Overlay Mouse",
      "Configure mouse input sent from the overlay. Note: 1-, 2-, and 3-finger taps send left, right, and middle button clicks.")
#endif
''',
    '''S_ACTION_EX(OVERLAY_MOUSE_SETTINGS,
      "overlay_mouse_settings", SD_FLAG_LAKKA_ADVANCED, NULL, NULL, 0,
      "Overlay Mouse",
      "Configure mouse input sent from the overlay. Note: 1-, 2-, and 3-finger taps send left, right, and middle button clicks.")
#endif
/* MOD: editor de overlay (etapa 1) */
#if defined(HAVE_OVERLAY) || defined(SETTINGS_DEF_STRINGS_PASS)
S_ACTION_EX(OVERLAY_EDITOR,
      "overlay_editor", SD_FLAG_LAKKA_ADVANCED, NULL, NULL, 0,
      "Edit Overlay Layout",
      "Move and resize the on-screen buttons and the game screen. Work in progress.")
#endif
''',
)

# 2) Coloca a linha na lista de opcoes do overlay (visivel quando o overlay esta ligado).
trocar(
    "menu/menu_displaylist.c",
    "               {MENU_ENUM_LABEL_OVERLAY_MOUSE_SETTINGS,                    PARSE_ACTION,     false },\n",
    "               {MENU_ENUM_LABEL_OVERLAY_MOUSE_SETTINGS,                    PARSE_ACTION,     false },\n"
    "               {MENU_ENUM_LABEL_OVERLAY_EDITOR,                            PARSE_ACTION,     false },\n",
)
trocar(
    "menu/menu_displaylist.c",
    "                  case MENU_ENUM_LABEL_OSK_OVERLAY_SETTINGS:\n"
    "                     build_list[i].checked = input_overlay_enable;\n",
    "                  case MENU_ENUM_LABEL_OVERLAY_EDITOR:\n"
    "                  case MENU_ENUM_LABEL_OSK_OVERLAY_SETTINGS:\n"
    "                     build_list[i].checked = input_overlay_enable;\n",
)

# 3) Acao ao tocar na linha.
trocar(
    "menu/cbs/menu_cbs_ok.c",
    "STATIC_DEFAULT_ACTION_OK_CMD_FUNC(action_ok_resume_content,           CMD_EVENT_RESUME)\n",
    "STATIC_DEFAULT_ACTION_OK_CMD_FUNC(action_ok_resume_content,           CMD_EVENT_RESUME)\n"
    "#ifdef HAVE_OVERLAY\n"
    "/* MOD: editor de overlay (etapa 1); definido em input/input_driver.c */\n"
    "void input_overlay_editor_enter(void);\n"
    "static int action_ok_overlay_editor(const char *path,\n"
    "      const char *label, unsigned type, size_t idx, size_t entry_idx)\n"
    "{\n"
    "   input_overlay_editor_enter();\n"
    "   return 0;\n"
    "}\n"
    "#endif\n",
)
trocar(
    "menu/cbs/menu_cbs_ok.c",
    "         {MENU_ENUM_LABEL_RESUME_CONTENT,                      action_ok_resume_content},\n",
    "         {MENU_ENUM_LABEL_RESUME_CONTENT,                      action_ok_resume_content},\n"
    "#ifdef HAVE_OVERLAY\n"
    "         {MENU_ENUM_LABEL_OVERLAY_EDITOR,                      action_ok_overlay_editor},\n"
    "#endif\n",
)

# 4) O que o "modo editor" faz nesta etapa: fecha o menu, pausa e avisa.
caminho = f"{raiz}/input/input_driver.c"
with open(caminho, "a", encoding="utf-8") as f:
    f.write(
        '''
#ifdef HAVE_OVERLAY
/* MOD: editor de overlay (etapa 1). So entra no modo: fecha o menu,
 * pausa o jogo e avisa. Mover/salvar vem nas proximas etapas. */
void input_overlay_editor_enter(void)
{
   static const char msg[] =
         "Editor de overlay (teste): jogo pausado. Abra o menu para sair.";
   command_event(CMD_EVENT_RESUME, NULL);
   command_event(CMD_EVENT_PAUSE, NULL);
   runloop_msg_queue_push(msg, sizeof(msg) - 1, 1, 180, true, NULL,
         MESSAGE_QUEUE_ICON_DEFAULT, MESSAGE_QUEUE_CATEGORY_INFO);
}
#endif
'''
    )
print("ok: input/input_driver.c (fim do arquivo)")
