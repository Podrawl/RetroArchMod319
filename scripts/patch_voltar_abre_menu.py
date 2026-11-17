#!/usr/bin/env python3
"""Botao Voltar / gesto de voltar (do sistema Android) abre o menu rapido do jogo,
quando ha jogo rodando e o menu esta fechado. Com o menu aberto, Voltar funciona como sempre.
Ignora botoes de controle fisico (gamepad/joystick). Sai do modo editor de overlay, se ativo.
Uso: patch_voltar_abre_menu.py <pasta_do_RetroArch>
"""
import sys

raiz = sys.argv[1]
arq = "input/drivers/android_input.c"
caminho = f"{raiz}/{arq}"
s = open(caminho, encoding="utf-8").read()

ANCORA = (
    "static INLINE void android_input_poll_event_type_key(int port,\n"
    "      const android_input_fields_t *key, int *handled)\n"
    "{\n"
    "   int action  = key->action;\n"
    "   int keycode = key->keycode;\n"
)
antigo = ANCORA
novo = ANCORA + (
    "\n"
    "   /* MOD: Voltar do sistema (botao ou gesto) abre o menu rapido do jogo.\n"
    "    * Cada tecla chega duas vezes (e uma vez por funcao que le o evento);\n"
    "    * event_time evita abrir e fechar na mesma tecla.\n"
    "    * Mascara: GAMEPAD e KEYBOARD compartilham bits; comparar o valor todo. */\n"
    "   if (     keycode == AKEYCODE_BACK\n"
    "         && action  == AKEY_EVENT_ACTION_DOWN\n"
    "         && (key->source & AINPUT_SOURCE_GAMEPAD)  != AINPUT_SOURCE_GAMEPAD\n"
    "         && (key->source & AINPUT_SOURCE_JOYSTICK) != AINPUT_SOURCE_JOYSTICK)\n"
    "   {\n"
    "      static int64_t mod_ultimo_voltar = -1;\n"
    "      if ((int64_t)key->event_time != mod_ultimo_voltar)\n"
    "      {\n"
    "         mod_ultimo_voltar = (int64_t)key->event_time;\n"
    "         if (   (runloop_get_flags() & RUNLOOP_FLAG_CORE_RUNNING)\n"
    "             && !(menu_state_get_ptr()->flags & MENU_ST_FLAG_ALIVE))\n"
    "         {\n"
    "            extern void input_overlay_editor_exit(void);\n"
    "            input_overlay_editor_exit();\n"
    "            command_event(CMD_EVENT_MENU_TOGGLE, NULL);\n"
    "            *handled = 1;\n"
    "            return;\n"
    "         }\n"
    "      }\n"
    "   }\n"
)
n = s.count(antigo)
if n != 1:
    sys.exit(f"ERRO: trecho aparece {n} vezes (esperado 1)")
open(caminho, "w", encoding="utf-8").write(s.replace(antigo, novo))
print("ok:", arq)
