#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inspeção final (temporária): linhas REAIS (não-teste) com Status='Enviou' da
aba Sessões — conferir preenchimento de Origem/Campanha/ad_id, e confirmar
quais Campaign Name existem no Meta Ads (ENGJ vs LEADS) com soma de cliques."""
import csv
import io
import sys
import urllib.parse
import urllib.request


def fetch_csv_by_name(sid, sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{sid}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(sheet_name)}"
    req = urllib.request.Request(url, headers={"User-Agent": "inspect-bot/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read().decode("utf-8", errors="replace")
    return list(csv.reader(io.StringIO(raw)))


SID_LEADS = "1tFaH49FCD2egRPjbzKP8_KixwXyyRjhMyOONSiLpR2I"
SID_META = "1L-QoyOYAp-ifK4Db9fbESRKDm2X-CGRurKs_3hADjKQ"

rows = fetch_csv_by_name(SID_LEADS, "Sessões")
header = rows[0]
idx = {h: i for i, h in enumerate(header)}
si, statusI = idx["SID"], idx["Status"]
origemI, campI, adidI = idx["Origem"], idx["Campanha"], idx["ad_id"]
pontI = idx["Pontuação"]

enviou = [r for r in rows[1:] if len(r) > statusI and r[statusI].strip() == "Enviou"]
real = [r for r in enviou if not (r[adidI] or "").upper().startswith("TEST_")]
print(f"Enviou total: {len(enviou)}  (não-teste: {len(real)})")
for r in real[:15]:
    print(f"  ad_id={r[adidI]!r} Origem={r[origemI]!r} Campanha={r[campI]!r} Pontuacao={r[pontI]!r}")

nonempty_origem = sum(1 for r in real if (r[origemI] or "").strip())
nonempty_camp = sum(1 for r in real if (r[campI] or "").strip())
nonempty_adid = sum(1 for r in real if (r[adidI] or "").strip())
print(f"\npreenchidos: Origem {nonempty_origem}/{len(real)}  Campanha {nonempty_camp}/{len(real)}  ad_id {nonempty_adid}/{len(real)}")

print("\n=== Meta Ads Página1: Campaign Name únicos + soma Link Clicks ===")
meta_rows = fetch_csv_by_name(SID_META, "Página1")
mh = meta_rows[0]
ci, cli = mh.index("Campaign Name"), mh.index("Link Clicks")
from collections import defaultdict
sums = defaultdict(float)
for r in meta_rows[1:]:
    if len(r) <= max(ci, cli):
        continue
    try:
        sums[r[ci]] += float((r[cli] or "0").replace(",", "."))
    except ValueError:
        pass
for camp, total in sorted(sums.items(), key=lambda x: -x[1]):
    print(f"  {total:>8.0f} cliques  |  {camp!r}")
