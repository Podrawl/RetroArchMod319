#!/usr/bin/env python3
"""Botao Voltar / gesto de voltar (do sistema Android) abre o menu rapido do jogo,
quando ha jogo rodando e o menu esta fechado. Com o menu aberto, Voltar funciona como sempre.
Ignora botoes de controle fisico (gamepad/joystick).
Uso: patch_voltar_abre_menu.py <pasta_do_RetroArch>
"""
import sys

raiz = sys.argv[1]
arq = "input/drivers/android_input.c"
caminho = f"{raiz}/{arq}"
s = open(caminho, encoding="utf-8").read()

antigo = (
    "   int action  = key->action;\n"
    "   int keycode = key->keycode;\n"
    "\n"
    "   /* android_key_state[] has one row per pad slot plus the\n"
)
novo = (
    "   int action  = key->action;\n"
    "   int keycode = key->keycode;\n"
    "\n"
    "   /* MOD: Voltar do sistema (botao ou gesto) abre o menu rapido do jogo.\n"
    "    * Cada tecla chega duas vezes (e uma vez por funcao que le o evento);\n"
    "    * event_time evita abrir e fechar na mesma tecla. */\n"
    "   if (     keycode == AKEYCODE_BACK\n"
    "         && action  == AKEY_EVENT_ACTION_DOWN\n"
    "         && (key->source & AINPUT_SOURCE_GAMEPAD)  != AINPUT_SOURCE_GAMEPAD\n"
    "         && (key->source & AINPUT_SOURCE_JOYSTICK) != AINPUT_SOURCE_JOYSTICK)\n"
    "   {\n"
    "      static int64_t mod_ultimo_voltar = -1;\n"
    "      if ((int64_t)key->event_time != mod_ultimo_voltar)\n"
    "      {\n"
    "         char mod_dbg[96];\n"
    "         int  mod_n = snprintf(mod_dbg, sizeof(mod_dbg),\n"
    "               \"DIAG Voltar: fonte=0x%x jogo=%d menu=%d\",\n"
    "               (unsigned)key->source,\n"
    "               (runloop_get_flags() & RUNLOOP_FLAG_CORE_RUNNING) ? 1 : 0,\n"
    "               (menu_state_get_ptr()->flags & MENU_ST_FLAG_ALIVE) ? 1 : 0);\n"
    "         runloop_msg_queue_push(mod_dbg, (size_t)mod_n, 1, 120, true, NULL,\n"
    "               MESSAGE_QUEUE_ICON_DEFAULT, MESSAGE_QUEUE_CATEGORY_INFO);\n"
    "      }\n"
    "      if ((int64_t)key->event_time != mod_ultimo_voltar)\n"
    "      {\n"
    "         mod_ultimo_voltar = (int64_t)key->event_time;\n"
    "         if (   (runloop_get_flags() & RUNLOOP_FLAG_CORE_RUNNING)\n"
    "             && !(menu_state_get_ptr()->flags & MENU_ST_FLAG_ALIVE))\n"
    "         {\n"
    "            command_event(CMD_EVENT_MENU_TOGGLE, NULL);\n"
    "            *handled = 1;\n"
    "            return;\n"
    "         }\n"
    "      }\n"
    "   }\n"
    "\n"
    "   /* android_key_state[] has one row per pad slot plus the\n"
)
n = s.count(antigo)
if n != 1:
    sys.exit(f"ERRO: trecho aparece {n} vezes (esperado 1)")
open(caminho, "w", encoding="utf-8").write(s.replace(antigo, novo))
print("ok:", arq)
