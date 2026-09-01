#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inspeção (temporária): checar se "Página 1"/"Página 2" têm alguma coluna
de resultado/conversa (não só Link Clicks), e somar Link Clicks da campanha
ENGJ no período 03/08-01/09 pra comparar com o "Conversas por mensagem" real
do Meta Ads Manager (186, segundo o cliente)."""
import csv
import io
import sys
import urllib.parse
import urllib.request
import zipfile
import re


def fetch_bytes(url):
    req = urllib.request.Request(url, headers={"User-Agent": "inspect-bot/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def fetch_csv_by_name(sid, sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{sid}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(sheet_name)}"
    raw = fetch_bytes(url).decode("utf-8", errors="replace")
    return list(csv.reader(io.StringIO(raw)))


def list_sheet_names(sid):
    url = f"https://docs.google.com/spreadsheets/d/{sid}/export?format=xlsx"
    raw = fetch_bytes(url)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        xml = z.read("xl/workbook.xml").decode("utf-8", errors="replace")
    return re.findall(r'<sheet[^>]*\bname="([^"]*)"', xml)


SID_META = "1L-QoyOYAp-ifK4Db9fbESRKDm2X-CGRurKs_3hADjKQ"

for name in list_sheet_names(SID_META):
    rows = fetch_csv_by_name(SID_META, name)
    header = rows[0] if rows else []
    print(f"\n=== aba '{name}' — colunas ===")
    for i, h in enumerate(header):
        print(f"  [{i}] {h!r}")

rows = fetch_csv_by_name(SID_META, "Página1")
header = rows[0]
di, ci, cli = header.index("Day"), header.index("Campaign Name"), header.index("Link Clicks")
total_engj_30d = 0.0
total_engj_all = 0.0
for r in rows[1:]:
    if len(r) <= max(di, ci, cli):
        continue
    if "ENGJ" not in r[ci]:
        continue
    try:
        clicks = float((r[cli] or "0").replace(",", "."))
    except ValueError:
        clicks = 0.0
    total_engj_all += clicks
    d = r[di]
    if "2026-08-03" <= d <= "2026-09-01":
        total_engj_30d += clicks

print(f"\nENGJ Link Clicks total (todo período): {total_engj_all:.0f}")
print(f"ENGJ Link Clicks (03/08 a 01/09, mesma janela do Ads Manager): {total_engj_30d:.0f}")
print("Cliente reportou no Ads Manager (mesma janela): 186 'Conversas por mensagem' (resultado real da campanha)")
