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

# Limite circular: mantem o angulo do dedo quando passa do maximo
trocar(
    "   out->analog[base + 0] = clamp_float(x_val_sat, -1.0f, 1.0f) * 32767.0f;\n"
    "   out->analog[base + 1] = clamp_float(y_val_sat, -1.0f, 1.0f) * 32767.0f;\n",
    "   {\n"
    "      /* MOD: limite circular (mantem a direcao do dedo) */\n"
    "      float mod_mag = sqrt(x_val_sat * x_val_sat + y_val_sat * y_val_sat);\n"
    "      if (mod_mag > 1.0f)\n"
    "      {\n"
    "         x_val_sat /= mod_mag;\n"
    "         y_val_sat /= mod_mag;\n"
    "      }\n"
    "   }\n"
    "   out->analog[base + 0] = clamp_float(x_val_sat, -1.0f, 1.0f) * 32767.0f;\n"
    "   out->analog[base + 1] = clamp_float(y_val_sat, -1.0f, 1.0f) * 32767.0f;\n",
)
trocar(
    "         desc->delta_x = clamp_float(x_dist, -desc->range_x, desc->range_x)\n"
    "            * ol->active->mod_w;\n"
    "         desc->delta_y = clamp_float(y_dist, -desc->range_y, desc->range_y)\n"
    "            * ol->active->mod_h;\n",
    "         float mod_nx = x_dist / desc->range_x;\n"
    "         float mod_ny = y_dist / desc->range_y;\n"
    "         float mod_r  = sqrt(mod_nx * mod_nx + mod_ny * mod_ny);\n"
    "         if (mod_r > 1.0f)\n"
    "         {\n"
    "            x_dist /= mod_r;\n"
    "            y_dist /= mod_r;\n"
    "         }\n"
    "         desc->delta_x = clamp_float(x_dist, -desc->range_x, desc->range_x)\n"
    "            * ol->active->mod_w;\n"
    "         desc->delta_y = clamp_float(y_dist, -desc->range_y, desc->range_y)\n"
    "            * ol->active->mod_h;\n",
)
open(arq, "w", encoding="utf-8").write(s)
print("patch_analogico aplicado")
