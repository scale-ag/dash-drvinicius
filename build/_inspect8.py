#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inspeção (temporária): reconferir tudo pós Página2, para 2 janelas:
"hoje" (período padrão da dash ao recarregar) e 03/08-01/09 (a janela que
vínhamos comparando). Objetivo: achar se "hoje" bate mal com um Gerenciador
configurado pra ver os últimos N dias (hipótese: refresh resetou o período)."""
import csv
import io
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta

BRT = timezone(timedelta(hours=-3))
TODAY = datetime.now(BRT).strftime("%Y-%m-%d")
WINDOWS = {
    "hoje": (TODAY, TODAY),
    "7d": ((datetime.now(BRT) - timedelta(days=6)).strftime("%Y-%m-%d"), TODAY),
    "30d(03/08-01/09)": ("2026-08-03", "2026-09-01"),
}


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


SID_LEADS = "1tFaH49FCD2egRPjbzKP8_KixwXyyRjhMyOONSiLpR2I"
SID_META = "1L-QoyOYAp-ifK4Db9fbESRKDm2X-CGRurKs_3hADjKQ"
SID_AGENDA = "1cOD2Sa9fp8TPJrBia7RY3br_Htg5pCJc5squzmLY4Dk"

meta = fetch_csv_by_name(SID_META, "Página1")
mh = meta[0]; mi = {h: i for i, h in enumerate(mh)}
p2 = fetch_csv_by_name(SID_META, "Página 2")
p2h = p2[0]; p2i = {h: i for i, h in enumerate(p2h)}
sess = fetch_csv_by_name(SID_LEADS, "Sessões")
sh = sess[0]; si = {h: i for i, h in enumerate(sh)}
ag = fetch_csv_by_name(SID_AGENDA, "Planilha agendamento")
ah = ag[0]; ai = {h: i for i, h in enumerate(ah)}

print(f"TODAY (BRT) = {TODAY}\n")

for label, (start, end) in WINDOWS.items():
    sp = im = cl = pv = 0.0
    for r in meta[1:]:
        if len(r) <= max(mi["Day"], mi["Amount Spent"]):
            continue
        d = r[mi["Day"]]
        if not (start <= d <= end):
            continue
        sp += to_float(r[mi["Amount Spent"]]); im += to_float(r[mi["Impressions"]])
        cl += to_float(r[mi["Link Clicks"]]); pv += to_float(r[mi["Landing Page Views"]])
    sp2 = im2 = 0.0
    for r in p2[1:]:
        if len(r) <= max(p2i["Day"], p2i["Amount Spent"]):
            continue
        d = r[p2i["Day"]]
        if not (start <= d <= end):
            continue
        sp2 += to_float(r[p2i["Amount Spent"]]); im2 += to_float(r[p2i["Impressions"]])
    quiz = mqls = 0
    for r in sess[1:]:
        if len(r) <= max(si["Status"], si["ad_id"]):
            continue
        if r[si["Status"]].strip() != "Enviou":
            continue
        blob = f"{r[si['Origem']]} {r[si['Campanha']]} {r[si['ad_id']]}".lower()
        if "test" in blob:
            continue
        d = parse_date(r[si["Última atividade"]]) or parse_date(r[si["Início"]])
        if not (d and start <= d <= end):
            continue
        quiz += 1
        if to_float(r[si["Pontuação"]]) > 33:
            mqls += 1
    wa = 0.0
    mc = mi.get("Messaging Conversations Started")
    for r in meta[1:]:
        if len(r) <= max(mi["Day"], mi["Campaign Name"]):
            continue
        if "ENGJ" not in r[mi["Campaign Name"]]:
            continue
        d = r[mi["Day"]]
        if not (start <= d <= end):
            continue
        if mc is not None and mc < len(r):
            wa += to_float(r[mc])
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
        if not (start <= d <= end):
            continue
        agd += to_float(r[ai["Agendamentos Confirmados"]])
        vd += to_float(r[ai["Cirurgias Confirmadas"]])
        fat += to_float(r[ai["Valor Total Cirurgias"]])
    leads_total = quiz + wa
    gasto_total = sp + sp2
    print(f"--- {label} [{start}..{end}] ---")
    print(f"  Página1: Gasto=R${sp:,.2f} Impr={im:.0f} Cliques={cl:.0f} PageViews={pv:.0f}")
    print(f"  Página2: Gasto=R${sp2:,.2f} Impr={im2:.0f}")
    print(f"  TOTAL dash: Gasto=R${gasto_total:,.2f} Impr={im+im2:.0f}")
    print(f"  Leads: quiz/LP={quiz} whatsapp={wa:.0f} total={leads_total:.0f}  MQLs={mqls}")
    print(f"  Agendamentos={agd:.0f} Vendas={vd:.0f} Faturamento=R${fat:,.2f}")
    print()
