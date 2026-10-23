"""Inspeção SOMENTE LEITURA (temporária) da planilha de Meta Ads."""
import sys
sys.path.insert(0, "build")
import build as b
sid = b.SPREADSHEET_ID_META
names = b.list_sheet_names(sid)
print("abas reais:", names)
for tab in names:
    rows = b.fetch_csv(b.sheet_url(sid, tab))
    print(f"\n===== aba {tab!r}: {len(rows)} linhas")
    if not rows: continue
    print("cabeçalho:", rows[0])
    for r in rows[1:4]: print("  ", r)
    print("  ...")
    for r in rows[-3:]: print("  ", r)
    h = [b.norm(c) for c in rows[0]]
    if "day" in h:
        di = h.index("day")
        ds = sorted({r[di] for r in rows[1:] if len(r) > di and r[di].strip()})
        print("datas:", ds[:1], "->", ds[-1:], f"({len(ds)} dias)")
    if "campaign name" in h:
        ci = h.index("campaign name")
        print("campanhas:", sorted({r[ci] for r in rows[1:] if len(r) > ci and r[ci]}))
    for col in ("amount spent", "impressions", "link clicks"):
        if col in h:
            i = h.index(col); tot = 0.0
            for r in rows[1:]:
                try: tot += float((r[i] or "0").replace(".", "").replace(",", ".")) if "," in (r[i] or "") else float(r[i] or 0)
                except Exception: pass
            print(f"soma {col}: {tot:,.2f}")
