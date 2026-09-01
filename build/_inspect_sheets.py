#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inspeção única (temporária) das 3 planilhas do cliente Dr Vinícius.
Roda no runner do GitHub Actions (tem internet); imprime estrutura nos logs
e salva os CSVs brutos em build/_inspect_out/ para virarem artifact.
NÃO faz parte do pipeline definitivo — arquivo/workflow removidos depois.
"""
import csv
import io
import os
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
    return list(csv.reader(io.StringIO(raw))), raw


def mask_row(header, row):
    out = []
    for i, v in enumerate(row):
        h = (header[i] if i < len(header) else "").lower()
        if any(hint in h for hint in PII_HINTS):
            v = (v[:2] + "***") if v else v
        out.append(v)
    return out


def show(label, key, rows):
    print(f"\n=== {label} ===")
    if not rows:
        print("  (vazio ou aba não encontrada)")
        return
    header = rows[0]
    print(f"  linhas de dados: {len(rows) - 1}")
    print(f"  colunas ({len(header)}):")
    for i, h in enumerate(header):
        print(f"    [{i}] {h!r}")
    for r in rows[1:4]:
        print(f"  amostra: {mask_row(header, r)}")


os.makedirs("build/_inspect_out", exist_ok=True)

all_rows = {}
for key, label, sid, sheet in SOURCES:
    try:
        rows, raw = fetch(sid, sheet)
        all_rows[key] = rows
        show(label, key, rows)
        with open(f"build/_inspect_out/{key}.csv", "w", encoding="utf-8") as f:
            f.write(raw)
    except Exception as e:
        print(f"\n=== {label} === ERRO: {e}", file=sys.stderr)
        all_rows[key] = []

# Campaign Name únicos (Meta Ads) -> candidatos a sigla do funil
meta_rows = all_rows.get("meta_pagina1") or []
if meta_rows:
    header = meta_rows[0]
    idx = None
    for i, h in enumerate(header):
        hn = h.strip().lower()
        if hn == "campaign name" or ("campaign" in hn and "name" in hn):
            idx = i
            break
    if idx is not None:
        names = sorted({r[idx] for r in meta_rows[1:] if len(r) > idx and r[idx]})
        print(f"\n=== Campaign Name únicos ({len(names)}) ===")
        for n in names:
            print(f"  {n!r}")
        # tenta extrair prefixo comum (primeiro token separado por espaço/-/_/|)
        prefixes = {}
        for n in names:
            m = re.match(r"^([A-Za-z0-9]+(?:[-_][A-Za-z0-9]+)?)", n)
            if m:
                prefixes.setdefault(m.group(1), 0)
                prefixes[m.group(1)] += 1
        print("\n=== Prefixos candidatos (1º token) ===")
        for p, c in sorted(prefixes.items(), key=lambda x: -x[1]):
            print(f"  {p!r}: {c} campanha(s)")
    else:
        print("\n=== Campaign Name: coluna não encontrada ===")

print("\n== fim da inspeção ==")
