#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Temp inspection: reproduce build.py's process() with live data and break
down leads for the window 2026-08-03..2026-09-01 (same window as the user's
Ads Manager screenshot: LEADS campaign=25 'Leads no site', ENGJ campaign=190
'Conversas por mensagem', total 215) vs the dashboard's 220, to find exactly
which leads make up the 5-lead gap."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import build as B

D0, D1 = "2026-08-03", "2026-09-01"

meta_rows = B.load_rows(B.sheet_url(B.SPREADSHEET_ID_META, B.SHEET_META), None)
leads_rows = B.load_rows(B.sheet_url(B.SPREADSHEET_ID_LEADS, B.SHEET_LEADS), None)
agenda_rows = B.load_rows(B.sheet_url(B.SPREADSHEET_ID_AGENDA, B.SHEET_AGENDA), None)
meta_other_rows = B.load_rows(B.sheet_url(B.SPREADSHEET_ID_META, B.SHEET_META_OTHER), None)

data = B.process(leads_rows, meta_rows, agenda_rows, meta_other_rows)
leads = [l for l in data["leads"] if l["d"] and D0 <= l["d"] <= D1]

quiz = [l for l in leads if l["src"] != "whatsapp"]
wa = [l for l in leads if l["src"] == "whatsapp"]
print(f"Total leads na janela {D0}..{D1}: {len(leads)}  (quiz/LP: {len(quiz)}  whatsapp: {len(wa)})")

print()
print("=== quiz/LP por campanha ===")
from collections import Counter
c = Counter(l["camp"] for l in quiz)
for camp, n in c.most_common():
    print(f"  {n:4d}  {camp}")

print()
print("=== whatsapp por campanha ===")
c2 = Counter(l["camp"] for l in wa)
for camp, n in c2.most_common():
    print(f"  {n:4d}  {camp}")

# Detalhe das linhas quiz/LP que não bateram na campanha LEADS| (pra achar os "5")
print()
print("=== quiz/LP SEM campanha == LEADS| (candidatos ao gap) ===")
for l in quiz:
    if "LEADS" not in l["camp"]:
        print(f"  d={l['d']} src={l['src']} camp={l['camp']!r} adset={l['adset']!r} ad={l['ad']!r} q={l['q']}")

# soma bruta de Messaging Conversations Started nas campanhas ENGJ no periodo,
# igual ao Ads Manager faria (== msg_conv por linha, no periodo)
print()
print("=== soma bruta 'Messaging Conversations Started' (Página1, campanhas ENGJ) na janela ===")
mheader = meta_rows[0]
midx = B.header_index(mheader, {
    "day": ["day", "data"], "campaign": ["campaign name", "campaign"],
    "msg_conv": ["messaging conversations started", "conversas por mensagem", "conversas iniciadas"],
}, {})
tot_engj = 0
for row in meta_rows[1:]:
    if not any((c or "").strip() for c in row):
        continue
    camp = B.cell(row, midx["campaign"])
    if B.ENGAJAMENTO_TAG not in camp:
        continue
    d = B.parse_date(B.cell(row, midx["day"]))
    if not d or not (D0 <= d <= D1):
        continue
    tot_engj += round(B.to_float(B.cell(row, midx["msg_conv"])))
print(f"  total: {tot_engj}")
