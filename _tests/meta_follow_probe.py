"""Teste ISOLADO e SOMENTE LEITURA (só GET): procura a métrica
"Seguidores do Instagram" do Gerenciador na Insights API. Nunca imprime o token."""
import json, os, sys, urllib.error, urllib.parse, urllib.request
from datetime import date, timedelta

V = "v23.0"
TOKEN = os.environ.get("META_ACCESS_TOKEN", "").strip()
ACT = "act_1189400572310429"
print("token presente:", "SIM" if TOKEN else "NAO")
if not TOKEN:
    sys.exit(0)

def get(path, **params):
    params["access_token"] = TOKEN
    url = f"https://graph.facebook.com/{V}/{path}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=90) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            err = json.loads(body).get("error", {})
            return {"_erro": f"{e.code} code={err.get('code')} {err.get('message')}"}
        except Exception:
            return {"_erro": f"{e.code} {body[:300]}"}

until = date.today(); since = until - timedelta(days=90)
TR = json.dumps({"since": str(since), "until": str(until)})

print("\n===== A. campos candidatos (nível conta, 90 dias)")
for f in ["instagram_follows", "ig_follows", "follows", "instagram_profile_follows",
          "instagram_profile_visits", "profile_visits", "instagram_followers",
          "cost_per_instagram_follow", "page_likes"]:
    r = get(f"{ACT}/insights", time_range=TR, fields=f"spend,{f}")
    print(f"  {f:28s} ->", r.get("_erro") or json.dumps(r.get("data"), ensure_ascii=False)[:300])

def scan(label, **extra):
    r = get(f"{ACT}/insights", time_range=TR, level="campaign", limit=200,
            fields="campaign_name,spend,actions,conversions,cost_per_action_type", **extra)
    print(f"\n===== {label}")
    if "_erro" in r:
        print("  ", r["_erro"]); return
    found = False
    for row in r.get("data", []):
        for key in ("actions", "conversions", "cost_per_action_type"):
            for a in row.get(key, []) or []:
                t = a.get("action_type", "")
                if any(w in t.lower() for w in ("follow", "profile", "instagram", "ig_")):
                    found = True
                    print(f"  [{key}] {row.get('campaign_name')} | {t} = {a.get('value')}")
    if not found:
        print("  nenhuma ação com follow/profile/instagram")

scan("B. por campanha, 90 dias, atribuição padrão")
scan("C. por campanha, 90 dias, atribuição unificada", use_unified_attribution_setting="true")
scan("D. por campanha, 90 dias, action_report_time=mixed", action_report_time="mixed")

print("\n===== E. todos os action_types distintos da conta (90 dias, nível anúncio)")
r = get(f"{ACT}/insights", time_range=TR, level="ad", limit=500, fields="actions")
types = set()
for row in r.get("data", []):
    for a in row.get("actions", []) or []:
        types.add(a["action_type"])
print("  ", r.get("_erro") or sorted(types))
