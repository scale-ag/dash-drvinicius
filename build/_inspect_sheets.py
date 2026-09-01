#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inspeção única (temporária) das 3 planilhas do cliente Dr Vinícius — v2,
com estatísticas extra (datas min/max, preenchimento de colunas, overlap
Origem x Ad Name). Roda no runner do GitHub Actions (tem internet); imprime
estrutura nos logs. NÃO faz parte do pipeline definitivo — removido depois.
"""
import csv
import io
import re
import sys
import urllib.parse
import urllib.request

SOURCES = [
    ("meta_pagina1", "Meta Ads - Página 1", "1L-QoyOYAp-ifK4Db9fbESRKDm2X-CGRurKs_3hADjKQ", "Página 1"),
    ("leads_leads", "Leads - aba Leads", "1tFaH49FCD2egRPjbzKP8_KixwXyyRjhMyOONSiLpR2I", "Leads"),
    ("leads_pontuacao", "Leads - aba Pontuação", "1tFaH49FCD2egRPjbzKP8_KixwXyyRjhMyOONSiLpR2I", "Pontuação"),
    ("agenda", "Agendamentos - Planilha agendamento", "1cOD2Sa9fp8TPJrBia7RY3br_Htg5pCJc5squzmLY4Dk", "Planilha agendamento"),
]

PII_HINTS = ["nome", "telefone", "phone", "email", "e-mail", "celular", "whatsapp", "cpf", "endereco", "endereço", "zip", "cep"]


def fetch(sid, sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{sid}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(sheet_name)}"
    req = urllib.request.Request(url, headers={"User-Agent": "inspect-bot/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read().decode("utf-8", errors="replace")
    return list(csv.reader(io.StringIO(raw)))


def mask_row(header, row):
    out = []
    for i, v in enumerate(row):
        h = (header[i] if i < len(header) else "").lower()
        if any(hint in h for hint in PII_HINTS):
            v = (v[:2] + "***") if v else v
        out.append(v)
    return out


all_rows = {}
for key, label, sid, sheet in SOURCES:
    try:
        all_rows[key] = fetch(sid, sheet)
        print(f"OK  {label}: {len(all_rows[key])-1} linhas", file=sys.stderr)
    except Exception as e:
        print(f"ERRO {label}: {e}", file=sys.stderr)
        all_rows[key] = []

leads = all_rows.get("leads_leads") or []
meta = all_rows.get("meta_pagina1") or []
agenda = all_rows.get("agenda") or []

# ---- Leads: preenchimento por coluna + range de datas + valores de Pontuação
if leads:
    header = leads[0]
    rows = leads[1:]
    print("\n=== Leads: preenchimento por coluna (não-vazias / total) ===")
    for i, h in enumerate(header):
        nonempty = sum(1 for r in rows if len(r) > i and (r[i] or "").strip())
        print(f"  [{i}] {h!r}: {nonempty}/{len(rows)}")
    di = header.index("Data/Hora") if "Data/Hora" in header else 0
    dates = sorted(r[di] for r in rows if len(r) > di and r[di])
    print(f"  Data/Hora min: {dates[0] if dates else '-'}  max: {dates[-1] if dates else '-'}")
    pi = header.index("Pontuação") if "Pontuação" in header else 4
    scores = [r[pi] for r in rows if len(r) > pi and r[pi]]
    print(f"  Pontuação amostra (todas): {scores}")
    oi = header.index("Origem") if "Origem" in header else None
    if oi is not None:
        origins = sorted({r[oi] for r in rows if len(r) > oi and r[oi]})
        print(f"\n  Origem — valores únicos ({len(origins)}):")
        for o in origins:
            print(f"    {o!r}")
    ci = header.index("Campanha") if "Campanha" in header else None
    if ci is not None:
        camps = sorted({r[ci] for r in rows if len(r) > ci and r[ci]})
        print(f"  Campanha (coluna) — valores únicos não-vazios: {camps}")

# ---- Meta: range de datas + Ad Set Name / Ad Name únicos
if meta:
    header = meta[0]
    rows = meta[1:]
    di = header.index("Day") if "Day" in header else 0
    dates = sorted(r[di] for r in rows if len(r) > di and r[di])
    print(f"\n=== Meta Ads: Day min: {dates[0] if dates else '-'}  max: {dates[-1] if dates else '-'} ===")
    ani = header.index("Ad Name") if "Ad Name" in header else None
    asni = header.index("Ad Set Name") if "Ad Set Name" in header else None
    if ani is not None:
        ad_names = sorted({r[ani] for r in rows if len(r) > ani and r[ani]})
        print(f"  Ad Name — valores únicos ({len(ad_names)}):")
        for a in ad_names:
            print(f"    {a!r}")
    if asni is not None:
        adset_names = sorted({r[asni] for r in rows if len(r) > asni and r[asni]})
        print(f"  Ad Set Name — valores únicos ({len(adset_names)}):")
        for a in adset_names:
            print(f"    {a!r}")
    # overlap Origem (Leads) x Ad Name (Meta)
    if leads and oi is not None and ani is not None:
        origins_set = {r[oi] for r in leads[1:] if len(r) > oi and r[oi]}
        adnames_set = {r[ani] for r in rows if len(r) > ani and r[ani]}
        print(f"\n  Overlap Origem(Leads) x Ad Name(Meta): {len(origins_set & adnames_set)} / {len(origins_set)} origens batem")
        print(f"  Origens SEM match: {sorted(origins_set - adnames_set)}")

# ---- Agendamentos: range de datas, preenchimento, linhas com cirurgia>0
if agenda:
    header = agenda[0]
    rows = agenda[1:]
    print(f"\n=== Agendamentos: preenchimento por coluna ({len(rows)} linhas) ===")
    for i, h in enumerate(header):
        nonempty = sum(1 for r in rows if len(r) > i and (r[i] or "").strip())
        print(f"  [{i}] {h!r}: {nonempty}/{len(rows)}")
    dts = [r[0] for r in rows if r and r[0]]
    print(f"  Data primeira linha: {dts[0] if dts else '-'}   última linha: {dts[-1] if dts else '-'}")
    ci = header.index("Cirurgias Confirmadas") if "Cirurgias Confirmadas" in header else 4
    vi = header.index("Valor Total Cirurgias") if "Valor Total Cirurgias" in header else 6
    pi2 = header.index("Pacientes") if "Pacientes" in header else 8
    nonzero = [(r[0], r[ci], r[vi]) for r in rows if len(r) > ci and re.sub(r"[^\d]", "", r[ci] or "") not in ("", "0")]
    print(f"  Linhas com Cirurgias Confirmadas > 0: {len(nonzero)}")
    for d, c, v in nonzero[:8]:
        print(f"    {d}: cirurgias={c!r} valor_total={v!r}")
    pac = [r[pi2] for r in rows if len(r) > pi2 and (r[pi2] or "").strip()]
    print(f"  'Pacientes' preenchido em {len(pac)} linha(s); amostra mascarada: {[p[:2]+'***' for p in pac[:5]]}")

print("\n== fim da inspeção v2 ==")
