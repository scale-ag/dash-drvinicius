#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Temp inspection: dump the new "planilha de seguidores" the client shared
(https://docs.google.com/spreadsheets/d/1P8ge3MO5jOZ415ObL_-noCy0G8-U8v7C-TV14aT6RGs)
- enumerate its tabs (via xlsx export, like earlier sessions did) and dump
the header + a few rows of each tab, to figure out columns/date format
before wiring it into build.py for the Funil Visitas ao Perfil page."""
import csv, io, sys, urllib.request, urllib.parse, zipfile, re

SID = "1P8ge3MO5jOZ415ObL_-noCy0G8-U8v7C-TV14aT6RGs"

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "dash-template-bot/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()

print("=== abas da planilha (via xlsx export) ===")
xlsx_url = f"https://docs.google.com/spreadsheets/d/{SID}/export?format=xlsx"
try:
    raw = fetch(xlsx_url)
    zf = zipfile.ZipFile(io.BytesIO(raw))
    wb = zf.read("xl/workbook.xml").decode("utf-8", errors="replace")
    names = re.findall(r'<sheet[^>]*\bname="([^"]*)"', wb)
    print(names)
except Exception as e:
    print("ERRO ao listar abas:", e)
    names = []

def fetch_csv(sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{SID}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(sheet_name)}"
    raw = fetch(url).decode("utf-8", errors="replace")
    return list(csv.reader(io.StringIO(raw)))

for name in names:
    print()
    print(f"=== aba: {name!r} ===")
    try:
        rows = fetch_csv(name)
    except Exception as e:
        print("ERRO:", e)
        continue
    print(f"total linhas: {len(rows)}")
    if rows:
        print("header:", rows[0])
        for r in rows[1:6]:
            print(" ", r)
        if len(rows) > 6:
            print(" ...")
            for r in rows[-3:]:
                print(" ", r)

# fallback: se a planilha default (gid=0, sem nome de aba) tiver algo diferente
print()
print("=== fallback: gviz sem nome de aba (primeira aba / default) ===")
try:
    rows = fetch_csv("")
    print(f"total linhas: {len(rows)}")
    if rows:
        print("header:", rows[0])
        for r in rows[1:6]:
            print(" ", r)
except Exception as e:
    print("ERRO:", e)
