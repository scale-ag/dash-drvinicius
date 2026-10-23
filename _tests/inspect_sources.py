"""Inspeção SOMENTE LEITURA (temporária): abas extras de seguidores."""
import sys
sys.path.insert(0, "build")
import build as b

for tab in ("📈 Out", "📈 Outubro"):
    rows = b.fetch_csv(b.sheet_url(b.SPREADSHEET_ID_SEGUIDORES, tab))
    print(f"\n===== SEGUIDORES aba {tab!r}: {len(rows)} linhas | col1[:60]={rows[0][1][:60]!r}")
    print("  col[12]/[13] cab:", rows[0][12:14] if rows else None)
    for r in rows:
        d = b.parse_date_br(r[1]) if len(r) > 1 else None
        if d and (len(r) > 13 and (r[12].strip() or r[13].strip())):
            print(f"  {d} | inv={r[12]!r} | seg={r[13]!r}")

rows = b.fetch_csv(b.sheet_url(b.SPREADSHEET_ID_META, "Seguidores"))
names = b.list_sheet_names(b.SPREADSHEET_ID_META)
print(f"\n===== META aba 'Seguidores' (abas: {names}): {len(rows)} linhas")
if rows:
    print("cabeçalho:", rows[0])
    for r in rows[1:6]: print("  ", r)
    print("  ...")
    for r in rows[-5:]: print("  ", r)
