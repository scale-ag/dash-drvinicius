#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inspeção (temporária): recomputar leads (quiz/LP via Sessões/Enviou +
WhatsApp via Messaging Conversations Started) pra varias janelas de data,
comparando com o que o cliente reportou no Ads Manager (25 quiz + 190
whatsapp = 215), pra achar de onde vem a diferença de 5 que ele viu (220 na
dash)."""
import csv
import io
import re
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

BRT = timezone(timedelta(hours=-3))


def fetch_csv_by_name(sid, sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{sid}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(sheet_name)}"
    req = urllib.request.Request(url, headers={"User-Agent": "inspect-bot/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read().decode("utf-8", errors="replace")
    return list(csv.reader(io.StringIO(raw)))


def parse_date(v):
    if not v:
        return None
    s = str(v).strip()
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    s_date = s.split(" ")[0]
    for fmt in ("%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s_date, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


SID_LEADS = "1tFaH49FCD2egRPjbzKP8_KixwXyyRjhMyOONSiLpR2I"
SID_META = "1L-QoyOYAp-ifK4Db9fbESRKDm2X-CGRurKs_3hADjKQ"

sess = fetch_csv_by_name(SID_LEADS, "Sessões")
sh = sess[0]
idx = {h: i for i, h in enumerate(sh)}
quiz_rows = []
for r in sess[1:]:
    if len(r) <= max(idx["Status"], idx["ad_id"], idx["Origem"], idx["Campanha"]):
        continue
    if r[idx["Status"]].strip() != "Enviou":
        continue
    blob = f"{r[idx['Origem']]} {r[idx['Campanha']]} {r[idx['ad_id']]}".lower()
    if "test" in blob:
        continue
    d = parse_date(r[idx["Última atividade"]]) or parse_date(r[idx["Início"]])
    quiz_rows.append((d, r[idx["Origem"]], r[idx["Campanha"]]))

meta = fetch_csv_by_name(SID_META, "Página1")
mh = meta[0]
midx = {h: i for i, h in enumerate(mh)}
wa_rows = []
for r in meta[1:]:
    if len(r) <= max(midx["Campaign Name"], midx["Day"]):
        continue
    if "ENGJ" not in r[midx["Campaign Name"]]:
        continue
    mc = midx.get("Messaging Conversations Started")
    if mc is None or mc >= len(r):
        continue
    try:
        n = float((r[mc] or "0").replace(",", "."))
    except ValueError:
        n = 0.0
    if n <= 0:
        continue
    wa_rows.append((r[midx["Day"]], n))

today = datetime.now(BRT).strftime("%Y-%m-%d")


def in_window(d, start, end):
    return d and start <= d <= end


windows = {
    "hoje": (today, today),
    "7d": ((datetime.now(BRT) - timedelta(days=6)).strftime("%Y-%m-%d"), today),
    "14d": ((datetime.now(BRT) - timedelta(days=13)).strftime("%Y-%m-%d"), today),
    "30d": ((datetime.now(BRT) - timedelta(days=29)).strftime("%Y-%m-%d"), today),
    "este_mes": (today[:8] + "01", today),
    "todo": ("2000-01-01", today),
}

for name, (start, end) in windows.items():
    qz = sum(1 for d, o, c in quiz_rows if in_window(d, start, end))
    wa = sum(n for d, n in wa_rows if in_window(d, start, end))
    print(f"{name:10s} [{start}..{end}]  quiz/LP={qz:3d}  whatsapp={wa:5.0f}  total={qz+wa:5.0f}")

print(f"\ncliente reportou (Ads Manager): quiz=25  whatsapp=190  total=215")
print(f"cliente viu na dash: total=220")

# breakdown de datas das sessões Enviou não atribuídas (org) recentes
print("\nSessões Enviou (não-teste) sem Origem/Campanha (caem em 'org'):")
for d, o, c in quiz_rows:
    if not o and not c:
        print(f"  d={d}")
