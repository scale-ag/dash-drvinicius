"""Inspeção SOMENTE LEITURA (temporária) da aba Seguidores da planilha de Meta."""
import sys
sys.path.insert(0, "build")
import build as b
from collections import defaultdict
rows = b.fetch_csv(b.sheet_url(b.SPREADSHEET_ID_META, "Seguidores"))
print("abas:", b.list_sheet_names(b.SPREADSHEET_ID_META))
print("linhas:", len(rows)); print("cabeçalho:", rows[0])
h = [b.norm(c) for c in rows[0]]
ci, di, si = h.index("campaign name"), h.index("day"), h.index("amount spent")
agg = defaultdict(lambda: [0, 0.0, set()])
for r in rows[1:]:
    if len(r) <= max(ci, di, si) or not r[di].strip(): continue
    a = agg[r[ci]]; a[0] += 1; a[1] += b.to_float(r[si]); a[2].add(r[di])
for c, (n, sp, ds) in agg.items():
    print(f"  {c!r}: {n} linhas, gasto {sp:,.2f}, {min(ds)} -> {max(ds)}, E1-DIST? {b.DIST_TAG in c}")
for r in rows[1:4]: print("  ", r)
