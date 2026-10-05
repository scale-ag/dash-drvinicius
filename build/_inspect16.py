#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mostra, célula a célula, a seção META — Seguidores (colunas M=[12] e
N=[13]) das abas 📈 Outubro e 📈 Setembro da planilha nova."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from build import fetch_csv, sheet_url

SID = "1hajaZpK-2cGY4TEpVGTfM7DljZk0M9fiLO6qylC29Gw"
COLS = {1: "B Data", 9: "J Inv.LP", 10: "K LeadsLP",
        12: "M Inv.SEGUIDORES", 13: "N SEGUID.", 14: "O CPS"}

for aba in ["📈 Outubro", "📈 Setembro"]:
    print(f"\n{'='*70}\n=== {aba} ===")
    rows = fetch_csv(sheet_url(SID, aba))
    print("   " + " | ".join(f"{v}" for v in COLS.values()))
    n_seg = 0
    for r in rows[1:]:
        def g(i):
            return (r[i] if i < len(r) else "") or ""
        if not g(1).strip():
            continue
        vals = [g(i).strip() or "(VAZIO)" for i in COLS]
        print("   " + " | ".join(vals))
        if g(13).strip() and g(13).strip() not in ("0", "(VAZIO)"):
            n_seg += 1
    print(f"   --> linhas com SEGUID. preenchido: {n_seg}")
