#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Temp inspection: re-check Página 2 header now that the client says they
added ALL metrics (not just Link Clicks) to the extractor."""
import csv, io, urllib.request, urllib.parse

EXPORT_URL = "https://docs.google.com/spreadsheets/d/{sid}/gviz/tq?tqx=out:csv&sheet={sheet}"

def fetch_csv(sid, sheet):
    url = EXPORT_URL.format(sid=sid, sheet=urllib.parse.quote(sheet))
    req = urllib.request.Request(url, headers={"User-Agent": "dash-template-bot/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    return list(csv.reader(io.StringIO(raw)))

SPREADSHEET_ID_META = "1L-QoyOYAp-ifK4Db9fbESRKDm2X-CGRurKs_3hADjKQ"

print("=== Página 2 header (now) ===")
rows2 = fetch_csv(SPREADSHEET_ID_META, "Página 2")
print(rows2[0])
print(f"total rows pagina2: {len(rows2)-1}")
print("últimas 3 linhas de dados pagina2:")
for r in rows2[-3:]:
    print(r)
