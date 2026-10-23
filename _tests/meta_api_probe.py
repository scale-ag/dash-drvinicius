"""Teste ISOLADO e SOMENTE LEITURA da API da Meta (só GET).
Não é lido pelo build nem publicado. Nunca imprime o token."""
import json, os, sys, urllib.error, urllib.parse, urllib.request
from datetime import date, timedelta

V = "v23.0"
TOKEN = os.environ.get("META_ACCESS_TOKEN", "").strip()
ACT = "act_10205578707965893"
IG = "17841402980847524"

print("META_ACCESS_TOKEN presente:", "SIM" if TOKEN else "NAO")
if not TOKEN:
    sys.exit(0)

def get(path, **params):
    params["access_token"] = TOKEN
    url = f"https://graph.facebook.com/{V}/{path}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            err = json.loads(body).get("error", {})
            return {"_erro": f"{e.code} {err.get('type')} code={err.get('code')} {err.get('message')}"}
        except Exception:
            return {"_erro": f"{e.code} {body[:300]}"}

def show(title, obj):
    print(f"\n===== {title}")
    print(json.dumps(obj, ensure_ascii=False, indent=1)[:6000])

show("1. dono do token", get("me", fields="id,name"))
perms = get("me/permissions")
show("2. permissões concedidas", [p["permission"] for p in perms.get("data", []) if p.get("status") == "granted"] if "data" in perms else perms)
accs = get("me/adaccounts", fields="name,account_id,account_status,amount_spent", limit=200)
until0 = date.today()
rows = []
for a in accs.get("data", []):
    i = get(f"{a['id']}/insights", time_range=json.dumps({"since": str(until0 - timedelta(days=30)), "until": str(until0)}), fields="spend")
    rows.append({"id": a["id"], "nome": a.get("name"), "status": a.get("account_status"),
                 "gasto_30d": (i.get("data") or [{}])[0].get("spend", "0") if "data" in i else i})
show("2b. contas de anúncio visíveis ao token (+ gasto 30d)", rows if "data" in accs else accs)
show("3. conta de anúncios", get(ACT, fields="name,account_status,currency,timezone_name"))

camps = get(f"{ACT}/campaigns", fields="name,objective,effective_status", limit=200)
show("4. campanhas", [(c.get("name"), c.get("objective"), c.get("effective_status")) for c in camps.get("data", [])] if "data" in camps else camps)

until = date.today(); since = until - timedelta(days=30)
ins = get(f"{ACT}/insights", level="campaign", time_range=json.dumps({"since": str(since), "until": str(until)}),
          fields="campaign_name,objective,spend,impressions,reach,clicks,actions", limit=200)
if "data" in ins:
    out = []
    for r in ins["data"]:
        out.append({"campanha": r.get("campaign_name"), "objetivo": r.get("objective"), "gasto": r.get("spend"),
                    "impr": r.get("impressions"), "alcance": r.get("reach"),
                    "acoes": {a["action_type"]: a["value"] for a in r.get("actions", [])}})
    show("5. insights por campanha (30 dias) + TODAS as ações", out)
else:
    show("5. insights por campanha (30 dias)", ins)

show("6. conta do Instagram", get(IG, fields="username,followers_count,media_count"))
show("7a. IG follower_count diário", get(f"{IG}/insights", metric="follower_count", period="day",
                                        since=str(until - timedelta(days=28)), until=str(until)))
show("7b. IG follows_and_unfollows", get(f"{IG}/insights", metric="follows_and_unfollows", period="day",
                                        metric_type="total_value", breakdown="follow_type",
                                        since=str(until - timedelta(days=28)), until=str(until)))
