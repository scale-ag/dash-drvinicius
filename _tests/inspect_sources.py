"""Inspeção SOMENTE LEITURA de todas as planilhas do dashboard. Temporário."""
import sys
sys.path.insert(0, "build")
import build as b
from datetime import datetime

def summarize(label, sid, tab, datecol_names):
    print(f"\n===== {label}  ({sid} / aba '{tab}')")
    try:
        names = b.list_sheet_names(sid)
        print("abas reais:", names)
        if tab not in names:
            print(f"!! a aba '{tab}' NAO existe com esse nome -> gviz devolveria a 1a aba")
    except Exception as e:
        print("erro ao listar abas:", repr(e))
    try:
        rows = b.fetch_csv(b.sheet_url(sid, tab))
    except Exception as e:
        print("ERRO leitura:", repr(e)); return
    print("linhas:", len(rows))
    if not rows: return
    h = rows[0]; print("cabeçalho:", h)
    di = next((i for i, c in enumerate(h) if b.norm(c) in datecol_names), None)
    if di is not None:
        ds = sorted({(b.parse_date(r[di]) or r[di]) for r in rows[1:] if len(r) > di and r[di].strip()})
        print("datas:", ds[:2], "...", ds[-4:], f"({len(ds)} dias)")
    for r in rows[-3:]: print("  ult:", r)

summarize("META Página1", b.SPREADSHEET_ID_META, b.SHEET_META, {"day", "data"})
summarize("META Página 2", b.SPREADSHEET_ID_META_OTHER, b.SHEET_META_OTHER, {"day", "data"})
summarize("LEADS Sessões", b.SPREADSHEET_ID_LEADS, b.SHEET_LEADS, {"inicio"})
summarize("AGENDA", b.SPREADSHEET_ID_AGENDA, b.SHEET_AGENDA, {"data"})

print("\n===== SEGUIDORES", b.SPREADSHEET_ID_SEGUIDORES)
names = b.list_sheet_names(b.SPREADSHEET_ID_SEGUIDORES)
print("abas reais:", names)
mes = datetime.now(b.BRT).month
tab = b.pick_month_sheet(names, mes)
print("aba escolhida p/ mês", mes, "->", repr(tab))
if tab:
    rows = b.fetch_csv(b.sheet_url(b.SPREADSHEET_ID_SEGUIDORES, tab))
    print("linhas:", len(rows), "| colunas na 1a linha:", len(rows[0]) if rows else 0)
    for i, c in enumerate(rows[0][:20] if rows else []): print(f"  col[{i}] = {c[:80]!r}")
    print("-- linhas com data: [1] data | [12] invest | [13] seguid. | [10..15] contexto")
    for r in rows:
        d = b.parse_date_br(r[1]) if len(r) > 1 else None
        if d:
            print(f"  {d} | {r[12] if len(r)>12 else '?'!r} | {r[13] if len(r)>13 else '?'!r} | {r[10:16]}")
