import sys, csv, io, urllib.parse, urllib.request
sys.path.insert(0, "build")
import build as b
NEW = "11Q6o75wcfhRYVcMU_F0eraL_roaRibqKuguCYMouNp8"
OLD = b.SPREADSHEET_ID_META
for label, sid in (("NOVA", NEW), ("ATUAL", OLD)):
    print("=====", label, sid)
    try:
        print("abas:", b.list_sheet_names(sid))
    except Exception as e:
        print("ERRO abas:", repr(e)); continue
    for tab in ("Página 1", "Página 2"):
        try:
            rows = b.fetch_csv(b.sheet_url(sid, tab))
        except Exception as e:
            print(tab, "ERRO", repr(e)); continue
        print(f"-- {tab}: {len(rows)} linhas")
        print("header:", rows[0] if rows else None)
        for r in rows[1:4]: print("  ", r)
        if rows:
            h = rows[0]
            def col(n):
                return h.index(n) if n in h else None
            di, ci, si = col("Day"), col("Campaign Name"), col("Amount Spent")
            days = sorted({r[di] for r in rows[1:] if di is not None and len(r) > di and r[di]})
            print("dias:", days[:1], "->", days[-1:], "n=", len(days))
            if ci is not None:
                print("campanhas:", sorted({r[ci] for r in rows[1:] if len(r) > ci and r[ci]}))
            if si is not None:
                tot = 0.0
                for r in rows[1:]:
                    try: tot += float(r[si].replace(",", ""))
                    except Exception: pass
                print("gasto total:", round(tot, 2))
