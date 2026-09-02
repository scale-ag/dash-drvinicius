#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Temp inspection: for the window 2026-09-01..2026-09-02 ("Este mês" no
dashboard), break down funnel='quiz' (LEADS campaigns) per Campaign Name —
o usuário reportou que os números da dash não batem com o Ads Manager pra
essa aba, comparando contra 1 linha de campanha só."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import build as B
from collections import Counter, defaultdict

D0, D1 = "2026-09-01", "2026-09-02"

meta_rows = B.load_rows(B.sheet_url(B.SPREADSHEET_ID_META, B.SHEET_META), None)
leads_rows = B.load_rows(B.sheet_url(B.SPREADSHEET_ID_LEADS, B.SHEET_LEADS), None)
agenda_rows = B.load_rows(B.sheet_url(B.SPREADSHEET_ID_AGENDA, B.SHEET_AGENDA), None)
meta_other_rows = B.load_rows(B.sheet_url(B.SPREADSHEET_ID_META, B.SHEET_META_OTHER), None)

data = B.process(leads_rows, meta_rows, agenda_rows, meta_other_rows)

quiz_rows = [m for m in data["meta"] if m["funnel"] == "quiz" and m["d"] and D0 <= m["d"] <= D1]
print(f"=== meta rows funnel=quiz, janela {D0}..{D1}: {len(quiz_rows)} linhas ===")
by_camp = defaultdict(lambda: {"sp":0.0,"im":0.0,"cl":0.0,"n":0})
for m in quiz_rows:
    c = by_camp[m["camp"]]
    c["sp"] += m["sp"]; c["im"] += m["im"]; c["cl"] += m["cl"]; c["n"] += 1
for camp, c in sorted(by_camp.items(), key=lambda x: -x[1]["sp"]):
    print(f"  camp={camp!r}\n    linhas={c['n']} gasto=R$ {c['sp']:.2f} impr={c['im']:.0f} clicks={c['cl']:.0f}")

print()
tot_sp = sum(c["sp"] for c in by_camp.values())
tot_im = sum(c["im"] for c in by_camp.values())
tot_cl = sum(c["cl"] for c in by_camp.values())
print(f"TOTAL funil quiz na janela: gasto=R$ {tot_sp:.2f} impr={tot_im:.0f} clicks={tot_cl:.0f}")

leads_quiz = [l for l in data["leads"] if l["src"] == "meta" and l["d"] and D0 <= l["d"] <= D1]
print(f"\nleads quiz na janela: {len(leads_quiz)}")
by_camp_leads = Counter(l["camp"] for l in leads_quiz)
for camp, n in by_camp_leads.most_common():
    print(f"  {n:3d}  {camp}")

print()
print("=== TODAS as campanhas distintas na aba Página 1 que contêm 'LEADS' (qualquer janela) ===")
all_camps_leads_tag = sorted({m["camp"] for m in data["meta"] if "LEADS" in m["camp"]})
for c in all_camps_leads_tag:
    print(" ", c)
