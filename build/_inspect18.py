#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Linha a linha da campanha P3-MISTO: valor BRUTO de "Messaging Conversations
Started" por anúncio/dia vs. o que o build.py realmente transforma em lead
(ele arredonda POR LINHA antes de somar). Mostra se há perda por arredondamento."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from build import (fetch_csv, sheet_url, header_index, cell, to_float, parse_date,
                   SPREADSHEET_ID_META, SHEET_META)

ALVO = "P3-MISTO"

rows = fetch_csv(sheet_url(SPREADSHEET_ID_META, SHEET_META))
idx = header_index(
    rows[0],
    {"day": ["day", "data"], "campaign": ["campaign name", "campaign"],
     "ad": ["ad name"], "spent": ["amount spent", "valor gasto"],
     "msg_conv": ["messaging conversations started"]},
    {"day": 0, "campaign": 1, "ad": 3, "spent": 7},
)
print(f"indice msg_conv = {idx['msg_conv']}  (cabecalho: {rows[0][idx['msg_conv']]!r})")

bruto = 0.0
arredondado = 0
print(f"\n{'DATA':<12} {'ANUNCIO':<34} {'CRU':>10} {'round()':>8}")
print("-" * 68)
for r in rows[1:]:
    camp = cell(r, idx["campaign"])
    if ALVO not in camp:
        continue
    raw = cell(r, idx["msg_conv"])
    v = to_float(raw)
    n = round(v)
    bruto += v
    arredondado += max(n, 0)
    print(f"{parse_date(cell(r, idx['day'])) or '?':<12} {cell(r, idx['ad'])[:34]:<34} {raw or '(vazio)':>10} {n:>8}")

print("-" * 68)
print(f"SOMA DOS VALORES BRUTOS DA PLANILHA : {bruto}")
print(f"LEADS QUE O build.py CRIA (round p/ linha, depois soma): {arredondado}")
print(f"DIFERENCA (perda por arredondamento): {bruto - arredondado:.4f}")
