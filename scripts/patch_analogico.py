#!/usr/bin/env python3
"""Analogico do overlay: o dedo que comecou no analogico fica preso nele ate soltar,
mesmo que saia da area desenhada (o valor fica no maximo na direcao). Enquanto preso,
bloqueia os outros botoes (o polegar nao aperta A/B sem querer).
Uso: patch_analogico.py <pasta_do_RetroArch>
"""
import sys

arq = f"{sys.argv[1]}/input/input_driver.c"
s = open(arq, encoding="utf-8").read()


def trocar(antigo, novo):
    global s
    n = s.count(antigo)
    if n != 1:
        sys.exit(f"ERRO: trecho aparece {n} vezes: {antigo[:60]!r}")
    s = s.replace(antigo, novo)


trocar(
    "      unsigned int desc_prio    = 0;\n"
    "      struct overlay_desc *desc = &descs[i];\n"
    "\n"
    "      /* Use range_mod if this touch pointer contributed\n"
    "       * to desc's touch_mask in the previous poll */\n"
    "      use_range_mod = (old_touch_idx != -1)\n"
    "            && BIT32_GET(desc->old_touch_mask, old_touch_idx);\n"
    "\n"
    "      if (!input_overlay_coords_inside_hitbox(desc, x, y, use_range_mod))\n"
    "         continue;\n",
    "      unsigned int desc_prio    = 0;\n"
    "      struct overlay_desc *desc = &descs[i];\n"
    "      bool mod_analog_preso;\n"
    "\n"
    "      /* Use range_mod if this touch pointer contributed\n"
    "       * to desc's touch_mask in the previous poll */\n"
    "      use_range_mod = (old_touch_idx != -1)\n"
    "            && BIT32_GET(desc->old_touch_mask, old_touch_idx);\n"
    "\n"
    "      /* MOD: dedo que ja estava no analogico continua preso a ele */\n"
    "      mod_analog_preso = use_range_mod\n"
    "            && (desc->type == OVERLAY_TYPE_ANALOG_LEFT\n"
    "             || desc->type == OVERLAY_TYPE_ANALOG_RIGHT);\n"
    "\n"
    "      if (!mod_analog_preso\n"
    "            && !input_overlay_coords_inside_hitbox(desc, x, y, use_range_mod))\n"
    "         continue;\n",
)
trocar(
    "      if (use_range_mod && (desc->flags & OVERLAY_DESC_RANGE_MOD_EXCLUSIVE))\n"
    "         desc_prio = 2;\n",
    "      if (mod_analog_preso)\n"
    "         desc_prio = 2;\n"
    "      else if (use_range_mod && (desc->flags & OVERLAY_DESC_RANGE_MOD_EXCLUSIVE))\n"
    "         desc_prio = 2;\n",
)
open(arq, "w", encoding="utf-8").write(s)
print("patch_analogico aplicado")
