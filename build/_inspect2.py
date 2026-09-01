#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inspeção v3 (temporária): enumerar TODAS as abas da planilha 1L-QoyOYAp...
(usada até agora só como Meta Ads) para achar a aba de leads gerais, e conferir
a aba específica (gid=654429203) que o cliente apontou na planilha de
Agendamentos. NÃO faz parte do pipeline definitivo — removido depois.
"""
import csv
import io
import re
import sys
import urllib.parse
import urllib.request
import zipfile

PII_HINTS = ["nome", "telefone", "phone", "email", "e-mail", "celular", "whatsapp", "cpf"]


def fetch_bytes(url):
    req = urllib.request.Request(url, headers={"User-Agent": "inspect-bot/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def fetch_csv_by_name(sid, sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{sid}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(sheet_name)}"
    raw = fetch_bytes(url).decode("utf-8", errors="replace")
    return list(csv.reader(io.StringIO(raw)))


def fetch_csv_by_gid(sid, gid):
    url = f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv&gid={gid}"
    raw = fetch_bytes(url).decode("utf-8", errors="replace")
    return list(csv.reader(io.StringIO(raw)))


def list_sheet_names(sid):
    """Baixa o export XLSX (zip) e lê xl/workbook.xml pra pegar os nomes de TODAS
    as abas, na ordem — sem depender de conhecer os gids de antemão."""
    url = f"https://docs.google.com/spreadsheets/d/{sid}/export?format=xlsx"
    raw = fetch_bytes(url)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        xml = z.read("xl/workbook.xml").decode("utf-8", errors="replace")
    names = re.findall(r'<sheet[^>]*\bname="([^"]*)"', xml)
    return names


def mask_row(header, row):
    out = []
    for i, v in enumerate(row):
        h = (header[i] if i < len(header) else "").lower()
        if any(hint in h for hint in PII_HINTS):
            v = (v[:2] + "***") if v else v
        out.append(v)
    return out


def show(label, rows):
    print(f"\n--- {label} ---")
    if not rows:
        print("  (vazio)")
        return
    header = rows[0]
    print(f"  linhas de dados: {len(rows) - 1}")
    print(f"  colunas ({len(header)}): {header}")
    for r in rows[1:4]:
        print(f"  amostra: {mask_row(header, r)}")


SID_META_ATUAL = "1L-QoyOYAp-ifK4Db9fbESRKDm2X-CGRurKs_3hADjKQ"
SID_LEADS_ATUAL = "1tFaH49FCD2egRPjbzKP8_KixwXyyRjhMyOONSiLpR2I"
SID_AGENDA = "1cOD2Sa9fp8TPJrBia7RY3br_Htg5pCJc5squzmLY4Dk"
AGENDA_GID_APONTADO = "654429203"

print(f"\n=== Abas da planilha de Leads {SID_LEADS_ATUAL} (até agora: 'Leads' + 'Pontuação') ===")
try:
    names0 = list_sheet_names(SID_LEADS_ATUAL)
    print("  abas encontradas:", names0)
    for name in names0:
        if name in ("Leads", "Pontuação"):
            continue  # já inspecionadas antes — só quero as NOVAS
        try:
            rows = fetch_csv_by_name(SID_LEADS_ATUAL, name)
            show(f"aba '{name}'", rows)
        except Exception as e:
            print(f"  ERRO lendo aba '{name}': {e}", file=sys.stderr)
except Exception as e:
    print(f"ERRO ao listar abas: {e}", file=sys.stderr)

print(f"\n=== Abas da planilha {SID_META_ATUAL} (até agora usada só como Meta Ads) ===")
try:
    names = list_sheet_names(SID_META_ATUAL)
    print("  abas encontradas:", names)
    for name in names:
        try:
            rows = fetch_csv_by_name(SID_META_ATUAL, name)
            show(f"aba '{name}'", rows)
        except Exception as e:
            print(f"  ERRO lendo aba '{name}': {e}", file=sys.stderr)
except Exception as e:
    print(f"ERRO ao listar abas: {e}", file=sys.stderr)

print(f"\n\n=== Planilha de Agendamentos {SID_AGENDA} — aba no gid={AGENDA_GID_APONTADO} (apontada pelo cliente) ===")
try:
    rows = fetch_csv_by_gid(SID_AGENDA, AGENDA_GID_APONTADO)
    show(f"gid={AGENDA_GID_APONTADO}", rows)
except Exception as e:
    print(f"ERRO: {e}", file=sys.stderr)

print(f"\n=== Planilha de Agendamentos {SID_AGENDA} — TODAS as abas (nomes) ===")
try:
    names2 = list_sheet_names(SID_AGENDA)
    print("  abas encontradas:", names2)
except Exception as e:
    print(f"ERRO ao listar abas: {e}", file=sys.stderr)

print("\n== fim da inspeção v3 ==")
