#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Temp inspection: dump Página 2 header + a few rows, to check if it has a
Link Clicks column we're not reading. Also sums Página1 clicks for 'hoje' and
'últimos 30 dias' windows, for comparison against Ads Manager screenshots."""
import csv, io, sys, urllib.request, urllib.parse
from datetime import datetime, timezone, timedelta

EXPORT_URL = "https://docs.google.com/spreadsheets/d/{sid}/gviz/tq?tqx=out:csv&sheet={sheet}"

def fetch_csv(sid, sheet):
    url = EXPORT_URL.format(sid=sid, sheet=urllib.parse.quote(sheet))
    req = urllib.request.Request(url, headers={"User-Agent": "dash-template-bot/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    return list(csv.reader(io.StringIO(raw)))

SPREADSHEET_ID_META = "1L-QoyOYAp-ifK4Db9fbESRKDm2X-CGRurKs_3hADjKQ"

print("=== Página 1 header ===")
rows1 = fetch_csv(SPREADSHEET_ID_META, "Página 1")
print(rows1[0])
print(f"total rows pagina1: {len(rows1)-1}")

print()
print("=== Página 2 header ===")
rows2 = fetch_csv(SPREADSHEET_ID_META, "Página 2")
print(rows2[0])
print(f"total rows pagina2: {len(rows2)-1}")
print("primeiras 3 linhas de dados pagina2:")
for r in rows2[1:4]:
    print(r)

BRT = timezone(timedelta(hours=-3))
now = datetime.now(BRT)
print()
print(f"now BRT: {now.isoformat()}")
