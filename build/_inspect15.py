#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inspeção temporária: nova planilha de Seguidores do Dr. Vinícius
("Controle de tráfego - 2026"), aba "📈 Outubro", seção META — Seguidores.
Confirma: nomes reais das abas, se o gviz aceita o nome com emoji, e em quais
POSIÇÕES de coluna ficam Data / Invest. / Seguidores."""
import io, re, sys, os, urllib.parse, zipfile
sys.path.insert(0, os.path.dirname(__file__))
from build import fetch_csv, sheet_url
import urllib.request

SID = "1hajaZpK-2cGY4TEpVGTfM7DljZk0M9fiLO6qylC29Gw"

# ---- 1. enumerar nomes reais das abas (via xlsx) ----
print("=== 1. Abas da planilha ===")
try:
    url = f"https://docs.google.com/spreadsheets/d/{SID}/export?format=xlsx"
    req = urllib.request.Request(url, headers={"User-Agent": "dash-template-bot/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        wb = z.read("xl/workbook.xml").decode("utf-8", errors="replace")
    names = re.findall(r'<sheet[^>]*\bname="([^"]*)"', wb)
    for n in names:
        print(f"  {n!r}")
except Exception as e:
    print(f"  ERRO ao enumerar abas: {type(e).__name__}: {e}")
    names = []

# ---- 2. tentar ler a aba de outubro por gviz ----
for candidate in ["📈 Outubro", "Outubro", "📈 Out"]:
    print(f"\n=== 2. gviz com nome de aba {candidate!r} ===")
    try:
        rows = fetch_csv(sheet_url(SID, candidate))
        print(f"  OK — {len(rows)} linhas")
        for i, r in enumerate(rows[:9]):
            cells = [f"[{j}]{c!r}" for j, c in enumerate(r) if (c or '').strip()]
            print(f"   linha {i}: {' '.join(cells)[:400]}")
    except Exception as e:
        print(f"  ERRO: {type(e).__name__}: {e}")
