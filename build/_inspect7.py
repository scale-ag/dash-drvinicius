#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inspeção (temporária): conferir as OUTRAS métricas do dashboard contra a
fonte, mesma janela 03/08-01/09: Gasto/Impressões/Cliques/Page Views (Página1
+ checar se Página2 tem algo relevante no período), Agendamentos/Vendas/
Faturamento (Planilha agendamento), e MQLs (Sessões/Enviou, Pontuação>33)."""
import csv
import io
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta

BRT = timezone(timedelta(hours=-3))
START, END = "2026-08-03", "2026-09-01"


def fetch_csv_by_name(sid, sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{sid}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(sheet_name)}"
    req = urllib.request.Request(url, headers={"User-Agent": "inspect-bot/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read().decode("utf-8", errors="replace")
    return list(csv.reader(io.StringIO(raw)))


def to_float(v):
    if not v:
        return 0.0
    s = re.sub(r"[^\d,.\-]", "", str(v))
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


SID_LEADS = "1tFaH49FCD2egRPjbzKP8_KixwXyyRjhMyOONSiLpR2I"
SID_META = "1L-QoyOYAp-ifK4Db9fbESRKDm2X-CGRurKs_3hADjKQ"
SID_AGENDA = "1cOD2Sa9fp8TPJrBia7RY3br_Htg5pCJc5squzmLY4Dk"

# --- Página1: Gasto/Impressões/Cliques/PageViews no período ---
meta = fetch_csv_by_name(SID_META, "Página1")
mh = meta[0]
mi = {h: i for i, h in enumerate(mh)}
sp = im = cl = pv = 0.0
for r in meta[1:]:
    if len(r) <= max(mi["Day"], mi["Amount Spent"]):
        continue
    d = r[mi["Day"]]
    if not (START <= d <= END):
        continue
    sp += to_float(r[mi["Amount Spent"]])
    im += to_float(r[mi["Impressions"]])
    cl += to_float(r[mi["Link Clicks"]])
    pv += to_float(r[mi["Landing Page Views"]])
print(f"Página1 ({START}..{END}): Gasto=R${sp:,.2f}  Impr={im:.0f}  Cliques={cl:.0f}  PageViews={pv:.0f}")

# --- Página2: tem algo relevante no período? ---
p2 = fetch_csv_by_name(SID_META, "Página 2")
p2h = p2[0]
p2i = {h: i for i, h in enumerate(p2h)}
sp2 = im2 = 0.0
rows_in_window = 0
for r in p2[1:]:
    if len(r) <= max(p2i.get("Day", 0), p2i.get("Amount Spent", 0)):
        continue
    d = r[p2i["Day"]]
    if not (START <= d <= END):
        continue
    rows_in_window += 1
    sp2 += to_float(r[p2i["Amount Spent"]])
    im2 += to_float(r[p2i["Impressions"]])
print(f"Página 2 ({START}..{END}): {rows_in_window} linhas  Gasto=R${sp2:,.2f}  Impr={im2:.0f}  (NÃO lida pelo build.py)")

# --- Agendamentos/Vendas/Faturamento no período ---
ag = fetch_csv_by_name(SID_AGENDA, "Planilha agendamento")
ah = ag[0]
ai = {h: i for i, h in enumerate(ah)}
agd = vd = fat = 0.0
year = 2026
for r in ag[1:]:
    if len(r) <= max(ai["Data"], ai["Agendamentos Confirmados"]):
        continue
    m = re.match(r"^(\d{1,2})/(\d{1,2})$", (r[ai["Data"]] or "").strip())
    if not m:
        continue
    dd, mm = int(m.group(1)), int(m.group(2))
    d = f"{year:04d}-{mm:02d}-{dd:02d}"
    if not (START <= d <= END):
        continue
    agd += to_float(r[ai["Agendamentos Confirmados"]])
    vd += to_float(r[ai["Cirurgias Confirmadas"]])
    fat += to_float(r[ai["Valor Total Cirurgias"]])
print(f"Agendamentos ({START}..{END}): Agendamentos={agd:.0f}  Vendas={vd:.0f}  Faturamento=R${fat:,.2f}")

# --- MQLs no período (Sessões/Enviou, não-teste, Pontuação>33) ---
sess = fetch_csv_by_name(SID_LEADS, "Sessões")
sh = sess[0]
si = {h: i for i, h in enumerate(sh)}


def parse_date(v):
    if not v:
        return None
    s = str(v).strip().split(" ")[0]
    for fmt in ("%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


leads_n = mqls_n = 0
for r in sess[1:]:
    if len(r) <= max(si["Status"], si["ad_id"]):
        continue
    if r[si["Status"]].strip() != "Enviou":
        continue
    blob = f"{r[si['Origem']]} {r[si['Campanha']]} {r[si['ad_id']]}".lower()
    if "test" in blob:
        continue
    d = parse_date(r[si["Última atividade"]]) or parse_date(r[si["Início"]])
    if not (d and START <= d <= END):
        continue
    leads_n += 1
    if to_float(r[si["Pontuação"]]) > 33:
        mqls_n += 1
print(f"Quiz/LP leads={leads_n}  MQLs={mqls_n} (Pontuação>33) no período")
