#!/usr/bin/env python3
"""Ao sair do app (Home/gesto) e voltar, abre o menu rapido do jogo (com Continuar).
Uso: patch_menu_ao_voltar.py <pasta_do_RetroArch>
"""
import sys

raiz = sys.argv[1]
arq = "input/drivers/android_input.c"
caminho = f"{raiz}/{arq}"
s = open(caminho, encoding="utf-8").read()


def trocar(antigo, novo):
    global s
    n = s.count(antigo)
    if n != 1:
        sys.exit(f"ERRO: trecho aparece {n} vezes (esperado 1):\n{antigo}")
    s = s.replace(antigo, novo)


# 1) variavel de aviso "o app foi para segundo plano"
trocar(
    "/* Set by the APP_CMD_PAUSE and APP_CMD_STOP handlers, consumed by",
    "/* MOD: o app foi para segundo plano; ao voltar, abrir o menu do jogo */\n"
    "static bool mod_menu_ao_voltar = false;\n\n"
    "/* Set by the APP_CMD_PAUSE and APP_CMD_STOP handlers, consumed by",
)

# 2) marca ao sair
trocar(
    "            if (hold_ack)\n"
    "               android_state_ack_cmd    = APP_CMD_PAUSE;\n"
    "         }\n"
    "         else\n",
    "            if (hold_ack)\n"
    "               android_state_ack_cmd    = APP_CMD_PAUSE;\n"
    "            mod_menu_ao_voltar = true;\n"
    "         }\n"
    "         else\n",
)

# 3) ao voltar (janela com foco), abre o menu uma unica vez, so se ha jogo rodando
trocar(
    "      case APP_CMD_GAINED_FOCUS:\n"
    "      case APP_CMD_LOST_FOCUS:\n"
    "         android_focus_activity(&android_app->focus,\n"
    "               cmd == APP_CMD_GAINED_FOCUS);\n"
    "         break;\n",
    "      case APP_CMD_GAINED_FOCUS:\n"
    "      case APP_CMD_LOST_FOCUS:\n"
    "         android_focus_activity(&android_app->focus,\n"
    "               cmd == APP_CMD_GAINED_FOCUS);\n"
    "         if (cmd == APP_CMD_GAINED_FOCUS && mod_menu_ao_voltar)\n"
    "         {\n"
    "            mod_menu_ao_voltar = false;\n"
    "            if (   (runloop_get_flags() & RUNLOOP_FLAG_CORE_RUNNING)\n"
    "                && !(menu_state_get_ptr()->flags & MENU_ST_FLAG_ALIVE))\n"
    "               command_event(CMD_EVENT_MENU_TOGGLE, NULL);\n"
    "         }\n"
    "         break;\n",
)

open(caminho, "w", encoding="utf-8").write(s)
print("ok:", arq)
