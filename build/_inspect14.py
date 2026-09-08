#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Investigação temporária: por que o total de Leads do Funil Quiz/LP no
dashboard (04/09-07/09/2026) não bate com "Leads no site" do Ads Manager
para a mesma janela. Roda a MESMA lógica de build.py (header_index,
build_ad_struct, atribuição) sobre os dados AO VIVO e imprime o detalhe de
cada sessão que caiu no período, pra comparar caso a caso."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from build import (
    sheet_url, load_rows, header_index, cell, to_float, parse_date,
    build_ad_struct, classify_funnel, is_qualified, valid_utm,
    SPREADSHEET_ID_META, SHEET_META, SPREADSHEET_ID_LEADS, SHEET_LEADS,
)

D0, D1 = "2026-09-04", "2026-09-07"

meta_rows = load_rows(sheet_url(SPREADSHEET_ID_META, SHEET_META), None)
leads_rows = load_rows(sheet_url(SPREADSHEET_ID_LEADS, SHEET_LEADS), None)

mheader = meta_rows[0]
midx = header_index(
    mheader,
    {"day": ["day", "data"], "campaign": ["campaign name", "campaign"], "adset": ["ad set name", "adset"],
     "ad": ["ad name"], "spent": ["amount spent", "valor gasto", "gasto"], "impr": ["impressions", "impress"],
     "clicks": ["link clicks", "clicks", "cliques"], "leads": ["leads"],
     "pv": ["landing page views", "page views", "pageviews"],
     "chk": ["adds to cart", "add to cart", "initiate checkout", "checkouts iniciados", "checkouts"],
     "msg_conv": ["messaging conversations started", "conversas por mensagem", "conversas iniciadas"],
     "link": ["creative instagram permalink", "instagram permalink", "permalink", "creative link", "link do anuncio", "link do criativo"]},
    {"day": 0, "campaign": 1, "adset": 2, "ad": 3, "impr": 4, "clicks": 5, "pv": 6, "spent": 7},
)
ad_struct = build_ad_struct(meta_rows, midx)

print(f"=== Header Meta (Página 1): {mheader}")
print(f"=== midx: {midx}")

# quais campanhas "quiz" existem no Meta e quantas linhas/qual spend no periodo
camp_period = {}
for row in meta_rows[1:]:
    if not any((c or "").strip() for c in row):
        continue
    d = parse_date(cell(row, midx["day"]))
    camp = cell(row, midx["campaign"]) or "(sem campanha)"
    if classify_funnel(camp) != "quiz":
        continue
    if d and D0 <= d <= D1:
        e = camp_period.setdefault(camp, {"sp": 0.0, "cl": 0.0, "rows": 0})
        e["sp"] += to_float(cell(row, midx["spent"]))
        e["cl"] += to_float(cell(row, midx["clicks"]))
        e["rows"] += 1
print(f"\n=== Campanhas 'quiz' no Meta com dado em {D0}..{D1}:")
for camp, e in camp_period.items():
    print(f"  {camp!r}: gasto={e['sp']:.2f} cliques={e['cl']:.0f} linhas={e['rows']}")

lheader = leads_rows[0]
lidx = header_index(
    lheader,
    {"start": ["início", "inicio"], "last": ["última atividade", "ultima atividade"],
     "status": ["status"], "score": ["pontuação", "pontuacao"],
     "campanha": ["campanha"], "origem": ["origem"], "ad_id": ["ad_id"]},
    {"start": 1, "last": 2, "status": 5, "score": 7, "origem": 11, "campanha": 12, "ad_id": 8},
)
print(f"\n=== Header Sessões: {lheader}")
print(f"=== lidx: {lidx}")

def is_test_session(origem, campanha, ad_id):
    blob = f"{origem} {campanha} {ad_id}".lower()
    return "test" in blob

total_enviou = 0
in_period_quiz = []
all_enviou_dates = []
for row in leads_rows[1:]:
    if not any((c or "").strip() for c in row):
        continue
    if cell(row, lidx["status"]) != "Enviou":
        continue
    total_enviou += 1
    origem = cell(row, lidx["origem"])
    campanha_col = cell(row, lidx["campanha"])
    ad_id = cell(row, lidx["ad_id"])
    inicio_raw = cell(row, lidx["start"])
    last_raw = cell(row, lidx["last"])
    d = parse_date(last_raw or inicio_raw)
    all_enviou_dates.append(d)
    if is_test_session(origem, campanha_col, ad_id):
        continue
    struct = ad_struct.get(origem) if origem else None
    if struct:
        camp, adset, ad, src = struct["camp"], struct["adset"], origem, "meta"
    elif valid_utm(campanha_col):
        camp, adset, ad, src = campanha_col, "(sem conjunto)", (origem or "(sem anúncio)"), "meta"
    else:
        continue
    if classify_funnel(camp) != "quiz":
        continue
    if d and D0 <= d <= D1:
        in_period_quiz.append({
            "d": d, "inicio_raw": inicio_raw, "last_raw": last_raw,
            "origem": origem, "campanha_col": campanha_col,
            "matched_via": "ad_struct" if struct else "campanha_col",
            "camp": camp, "score": cell(row, lidx["score"]),
        })

print(f"\n=== Total sessões Status=='Enviou' na planilha inteira: {total_enviou}")
print(f"=== Sessões 'Enviou' com data (Última ativ. || Início) em {D0}..{D1} E atribuídas ao funil 'quiz': {len(in_period_quiz)}")
for r in in_period_quiz:
    print(f"  d={r['d']}  origem={r['origem']!r}  campanha_col={r['campanha_col']!r}  via={r['matched_via']}  -> camp={r['camp']!r}  score={r['score']!r}  (inicio_raw={r['inicio_raw']!r} last_raw={r['last_raw']!r})")

# quantas dessas sessoes tem origem que NAO aparece em nenhuma linha do Meta na campanha "quiz" DENTRO do periodo (ou seja, o nome do anuncio nao rodou nessas datas, so em outras datas historicas)
ads_active_in_period = set()
for row in meta_rows[1:]:
    if not any((c or "").strip() for c in row):
        continue
    d = parse_date(cell(row, midx["day"]))
    camp = cell(row, midx["campaign"]) or ""
    if classify_funnel(camp) == "quiz" and d and D0 <= d <= D1:
        ads_active_in_period.add(cell(row, midx["ad"]))
print(f"\n=== Anúncios 'quiz' com linha no Meta em {D0}..{D1}: {sorted(ads_active_in_period)}")
for r in in_period_quiz:
    flag = "OK (anuncio rodou nessas datas)" if r["origem"] in ads_active_in_period else "!! ad_struct usou spend de OUTRAS datas / anuncio nao aparece no periodo"
    print(f"  origem={r['origem']!r} -> {flag}")
