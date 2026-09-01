#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inspeção (temporária): checar se a coluna "Messaging Conversations Started"
já apareceu preenchida na aba "Página1", e comparar com Link Clicks pra ver se
os números batem melhor com o que o cliente reportou (186 no período 03/08-01/09)."""
import csv
import io
import urllib.parse
import urllib.request


def fetch_csv_by_name(sid, sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{sid}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(sheet_name)}"
    req = urllib.request.Request(url, headers={"User-Agent": "inspect-bot/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read().decode("utf-8", errors="replace")
    return list(csv.reader(io.StringIO(raw)))


SID_META = "1L-QoyOYAp-ifK4Db9fbESRKDm2X-CGRurKs_3hADjKQ"
rows = fetch_csv_by_name(SID_META, "Página1")
header = rows[0]
print("colunas atuais:", header)

if "Messaging Conversations Started" not in header:
    print("\nA coluna AINDA NÃO aparece na planilha (relatório não foi atualizado/rodado ainda).")
else:
    ci = header.index("Campaign Name")
    di = header.index("Day")
    mi = header.index("Messaging Conversations Started")
    cli = header.index("Link Clicks")
    total_30d_msg = 0.0
    total_30d_clicks = 0.0
    nonempty = 0
    for r in rows[1:]:
        if len(r) <= max(ci, di, mi, cli):
            continue
        if "ENGJ" not in r[ci]:
            continue
        if (r[mi] or "").strip():
            nonempty += 1
        try:
            msg = float((r[mi] or "0").replace(",", "."))
        except ValueError:
            msg = 0.0
        try:
            clk = float((r[cli] or "0").replace(",", "."))
        except ValueError:
            clk = 0.0
        d = r[di]
        if "2026-08-03" <= d <= "2026-09-01":
            total_30d_msg += msg
            total_30d_clicks += clk
    print(f"\nlinhas ENGJ com 'Messaging Conversations Started' preenchido: {nonempty}")
    print(f"soma Messaging Conversations Started (03/08-01/09): {total_30d_msg:.0f}")
    print(f"soma Link Clicks (03/08-01/09, pra comparar): {total_30d_clicks:.0f}")
    print("cliente reportou no Ads Manager (mesmo período): 186")
