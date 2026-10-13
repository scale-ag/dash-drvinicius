#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lista TODAS as campanhas presentes na aba Meta Ads (Página 1) e na Página 2,
com intervalo de datas, gasto e conversas — pra ver se a campanha renomeada
(P3-MISTO) já foi trazida pelo Adveronix pra planilha."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from build import (fetch_csv, sheet_url, header_index, cell, to_float, parse_date,
                   classify_funnel, SPREADSHEET_ID_META, SHEET_META, SHEET_META_OTHER)

for aba in [SHEET_META, SHEET_META_OTHER]:
    print(f"\n{'='*78}\n=== aba {aba!r} ===")
    rows = fetch_csv(sheet_url(SPREADSHEET_ID_META, aba))
    hdr = rows[0]
    idx = header_index(
        hdr,
        {"day": ["day", "data"], "campaign": ["campaign name", "campaign"],
         "spent": ["amount spent", "valor gasto", "gasto"],
         "msg_conv": ["messaging conversations started", "conversas"]},
        {"day": 0, "campaign": 1, "spent": 7},
    )
    print(f"  cabecalho: {hdr}")
    agg = {}
    for r in rows[1:]:
        if not any((c or "").strip() for c in r):
            continue
        camp = cell(r, idx["campaign"])
        if not camp:
            continue
        d = parse_date(cell(r, idx["day"]))
        e = agg.setdefault(camp, {"d0": None, "d1": None, "sp": 0.0, "msg": 0.0, "n": 0})
        e["n"] += 1
        e["sp"] += to_float(cell(r, idx["spent"]))
        e["msg"] += to_float(cell(r, idx["msg_conv"]))
        if d:
            e["d0"] = d if e["d0"] is None or d < e["d0"] else e["d0"]
            e["d1"] = d if e["d1"] is None or d > e["d1"] else e["d1"]
    for camp, e in sorted(agg.items()):
        print(f"\n  {camp!r}")
        print(f"     funil={classify_funnel(camp)}  linhas={e['n']}  datas={e['d0']}..{e['d1']}"
              f"  gasto=R$ {e['sp']:.2f}  conversas={e['msg']:.0f}")
