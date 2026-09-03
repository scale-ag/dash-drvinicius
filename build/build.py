#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera a dashboard estatica (index.html) a partir de 3 planilhas Google Sheets
SEPARADAS do cliente Dr. Vinicius:

  - Leads (aba "Sessões"): fonte UNICA de leads — 1 linha por sessao do
    quiz/formulario de qualificacao (nao por lead "fechado"). So contam como
    lead as sessoes com Status == "Enviou" (completaram o formulario). Coluna
    "Pontuacao" (0-100) e o escore de qualificacao; MQL = Pontuacao > 33.
    A aba "Leads" (28 linhas, com Procedimento/Atendimento/Decisao) NAO e
    lida aqui — e na verdade um recorte de agendamentos, nao de leads (ver
    nota abaixo).
  - Meta Ads (aba "Pagina 1"): investimento/impressoes/cliques/page views do
    gerenciador de trafego, com DUAS campanhas/funis dentro do mesmo E2-CAP,
    classificados por `classify_funnel()` (substring no Campaign Name):
      - "quiz" (tag "LEADS"): funil do Quiz/LP — os leads ja vêm via
        Sessões/Enviou, NAO gera lead sintetico.
      - "whatsapp" (tag "ENGJ"): clique abre conversa direto, sem passar
        pelo quiz — cada "Messaging Conversations Started" dessas campanhas
        vira 1 lead sintetico (sem nome/pontuacao, src="whatsapp"). NAO usa
        Link Clicks — nem todo clique vira conversa de fato (confirmado com
        o cliente: clique superestima em quase 2x o resultado real do Ads
        Manager).
    Cada funil tem sua PROPRIA aba na dashboard ("Funil Quiz"/"Funil
    WhatsApp/Engajamento") — nunca misturados na mesma tabela/gráfico.
  - Agendamentos (aba "Planilha agendamento"): agregado DIARIO (nao por lead,
    sem telefone/nome) preenchido pelo comercial — Agendamentos Confirmados,
    Cirurgias Confirmadas e Valor Total Cirurgias. Sem chave de atribuicao por
    anuncio, entao so alimenta a Visao Geral/Relatorio (totals/daily), nunca a
    quebra por campanha/conjunto/anuncio de nenhum funil.
  - Meta Ads, aba "Página 2" (mesma planilha do Meta Ads, gid 0/segunda aba):
    3º funil, "Visitas ao Perfil" (E1-DIST, Alcance/Engajamento — o cliente
    confirmou nao ser o mesmo funil E2-CAP deste dashboard). Traz Day/
    Campaign Name/Ad Set Name/Ad Name/Impressions/Landing Page Views/Amount
    Spent/Link Clicks/Reach — ja atribuivel por campanha/anuncio, tem sua
    PROPRIA aba ("Funil Visitas ao Perfil") com quebra por campanha/conjunto/
    anuncio, igual aos outros 2 funis. Gasto/Impressões/Cliques/Landing Page
    Views tambem entram no total geral da Visão Geral/Relatório (mesmo
    padrão do agenda[] — só totals()/daily() no app.js). Sem Messaging
    Conversations Started nem Pontuação — nao gera leads/MQL (é um funil de
    Alcance/Engajamento de topo, nao de captura, entao fica fora de
    leads[]/da aba de leads qualificados).

Nota sobre a aba "Leads" (28 linhas) da planilha de Leads: e' na verdade um
registro POR AGENDAMENTO (Procedimento/Atendimento/Decisao/Investimento,
atribuido por anuncio via "Origem") — nao e' o volume bruto de leads. Como
pode se sobrepor aos totais da planilha diaria de Agendamentos sem uma chave
segura pra cruzar (nao ha telefone/data exata em comum confirmados), ela
fica de fora do pipeline por enquanto — nao e' somada a leads[] nem a
agenda[], pra nao contar nada em dobro.

Atribuicao do anuncio de cada lead (Sessões): a coluna "Origem" carrega o
NOME DO ANUNCIO (igual ao "Ad Name" do Meta Ads). build_ad_struct() cruza por
nome de anuncio -> escolhe a combinacao (Campanha, Conjunto) de maior gasto
no Meta para aquele anuncio.

Nao ha aba de Compradores/New Subscriptions neste cliente — Vendas/Faturamento
vêm do agregado diario de Agendamentos (Cirurgias Confirmadas = vendas), não
de cruzamento por telefone.

Este script apenas LE as planilhas (export CSV publico, via gviz por NOME da
aba — nao depende de gid) e emite os REGISTROS BRUTOS (leads[], meta[],
agenda[], meta_other[]) dentro do HTML. Todos os filtros, agregacoes, KPIs,
tabelas e graficos sao calculados no navegador (client-side). Nunca escreve
nada de volta nas planilhas.

Teste local: --leads-file / --meta-file / --agenda-file / --meta-other-file
apontando para CSVs baixados (o sandbox do agente nao alcanca
docs.google.com; o runner do GitHub Actions alcanca).
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sys
import unicodedata
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta

SPREADSHEET_ID_META = "1L-QoyOYAp-ifK4Db9fbESRKDm2X-CGRurKs_3hADjKQ"
SHEET_META = "Página 1"
# 2ª aba da mesma planilha de Meta Ads — sem Campaign Name (outro funil/conta,
# não atribuível). Gasto/Impressões entram no total geral, nunca na quebra
# por campanha (ver nota no topo do arquivo).
SHEET_META_OTHER = "Página 2"
SPREADSHEET_ID_LEADS = "1tFaH49FCD2egRPjbzKP8_KixwXyyRjhMyOONSiLpR2I"
SHEET_LEADS = "Sessões"
# Campanhas de Engajamento/WhatsApp (clique abre conversa direto, sem quiz) —
# identificadas pela substring abaixo no Campaign Name do Meta Ads.
ENGAJAMENTO_TAG = "ENGJ"
# Campanhas de Quiz/LP (funil E2-CAP) — identificadas pela substring abaixo.
QUIZ_TAG = "LEADS"
SPREADSHEET_ID_AGENDA = "1cOD2Sa9fp8TPJrBia7RY3br_Htg5pCJc5squzmLY4Dk"
SHEET_AGENDA = "Planilha agendamento"
# gviz por NOME da aba (nao pelo gid) — funciona independente de qual posicao
# a aba ocupa na planilha, so exige que a planilha esteja "qualquer um com o
# link pode ver".
EXPORT_URL = "https://docs.google.com/spreadsheets/d/{sid}/gviz/tq?tqx=out:csv&sheet={sheet}"

# Identificação do cliente/conta (usada só em textos/relatórios — não afeta o cruzamento de dados).
CLIENT_NAME = "Dr. Vinícius"
MAIN_PRODUCT = "Captação de Leads"
# Prefixo comum a TODAS as campanhas da conta (usado para agrupar/documentar
# campanhas no dashboard — hoje o build não filtra por ele, mantém tudo).
MAIN_PRODUCT_PREFIX = "DR. VINICIUS | E2-CAP"

BRT = timezone(timedelta(hours=-3))   # horario de Brasilia (exibicao)
TAX_FACTOR = 1.1385   # imposto da mídia paga informado pelo cliente (13,85%)

# --------------------------------------------------------------------------- #
# Regras da aba Relatório (Top/Piores anúncios)
# --------------------------------------------------------------------------- #
SAMPLE_MIN_SPEND = 100.0   # gasto mínimo (R$) para amostra relevante
SAMPLE_MIN_MQLS = 3        # MQLs mínimos para julgar qualidade profunda
TOP_ADS_N = 10             # nº de linhas em Top / Piores anúncios

# Metas & parâmetros da conta (DEFAULTS do painel editável da aba Relatório).
META_CPMQL = None          # meta de CPMQL (R$/MQL); None = não definida
META_CAC = None            # meta de CAC (R$/venda); None = não definida
VOLUME_MIN_AMOSTRAL = SAMPLE_MIN_MQLS  # conversões (MQLs) mínimas p/ amostra confiável
N_DIAS_CORTE = 5           # dias consecutivos acima do teto p/ considerar corte


# --------------------------------------------------------------------------- #
# Leitura
# --------------------------------------------------------------------------- #
def fetch_csv(url: str) -> list[list[str]]:
    req = urllib.request.Request(url, headers={"User-Agent": "dash-template-bot/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    return list(csv.reader(io.StringIO(raw)))


def read_csv_file(path: str) -> list[list[str]]:
    with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
        return list(csv.reader(f))


def load_rows(url: str, local: str | None) -> list[list[str]]:
    return read_csv_file(local) if local else fetch_csv(url)


def sheet_url(spreadsheet_id: str, sheet_name: str) -> str:
    return EXPORT_URL.format(sid=spreadsheet_id, sheet=urllib.parse.quote(sheet_name))


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def norm(s: str | None) -> str:
    return strip_accents((s or "").strip().lower())


def to_float(v) -> float:
    if v is None:
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = re.sub(r"[^\d,.\-]", "", str(v).strip())
    if not s:
        return 0.0
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def parse_date(v: str) -> str | None:
    if not v:
        return None
    s = str(v).strip()
    if not s:
        return None
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    # aba Sessões traz "Início"/"Última atividade" com hora (ex. "8/11/2026 14:57:19") — descarta a hora
    s_date = s.split(" ")[0]
    for fmt in ("%m/%d/%Y", "%d/%m/%Y", "%d/%m/%y", "%b %d, %Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s_date, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def is_qualified(v: str | None) -> bool:
    """Critério de MQL deste cliente: coluna "Pontuação" (aba Sessões) > 33."""
    return to_float(v) > 33


def valid_utm(campaign: str) -> bool:
    c = norm(campaign)
    return bool(c) and c not in ("-", "—", "nao encontrado")


# --------------------------------------------------------------------------- #
# Indexacao das colunas
# --------------------------------------------------------------------------- #
def header_index(header, wanted, fallback):
    idx = {}
    hn = [norm(h) for h in header]
    for key, aliases in wanted.items():
        found = None
        for a in aliases:
            a = norm(a)
            for i, h in enumerate(hn):
                if h == a or (a and a in h):
                    found = i
                    break
            if found is not None:
                break
        idx[key] = found if found is not None else fallback.get(key)
    return idx


def cell(row, i):
    if i is None or i < 0 or i >= len(row):
        return ""
    return (row[i] or "").strip()


# --------------------------------------------------------------------------- #
# Anúncio -> (campanha, conjunto) dominante por gasto (Meta Ads)
# --------------------------------------------------------------------------- #
def build_ad_struct(meta_rows, midx):
    """A aba Sessões não traz Campanha/Conjunto prontos por linha — só o nome do
    anúncio (coluna "Origem", que bate com o "Ad Name" do Meta). Aqui cruzamos
    por nome de anúncio e escolhemos a combinação (Campanha, Conjunto) de MAIOR
    GASTO no Meta para aquele anúncio (um anúncio pode rodar em mais de um
    conjunto ao longo do período)."""
    acc: dict[str, dict[tuple[str, str], float]] = {}
    for row in meta_rows[1:]:
        ad = cell(row, midx["ad"])
        if not ad:
            continue
        camp = cell(row, midx["campaign"]) or "(sem campanha)"
        adset = cell(row, midx["adset"]) or "(sem conjunto)"
        sp = to_float(cell(row, midx["spent"]))
        combos = acc.setdefault(ad, {})
        key = (camp, adset)
        combos[key] = combos.get(key, 0.0) + sp
    out = {}
    for ad, combos in acc.items():
        best_key = max(combos, key=combos.get)
        out[ad] = {"camp": best_key[0], "adset": best_key[1]}
    return out


def classify_funnel(campaign: str) -> str:
    """Funil de cada linha de mídia paga, pelo Campaign Name — usado pra
    separar as 3 abas "Funil ..." (Quiz/LP, WhatsApp/Engajamento, Visitas ao
    Perfil) sem misturar dados de um funil no outro. "outros" é fallback pra
    campanha fora da convenção (não aparece em nenhuma das 3 abas — só entra
    no total geral da Visão Geral/Relatório)."""
    if ENGAJAMENTO_TAG in campaign:
        return "whatsapp"
    if QUIZ_TAG in campaign:
        return "quiz"
    return "outros"


# --------------------------------------------------------------------------- #
# Processamento -> registros brutos
# --------------------------------------------------------------------------- #
def process(leads_rows, meta_rows, agenda_rows, meta_other_rows):
    mheader = meta_rows[0] if meta_rows else []
    midx = header_index(
        mheader,
        {"day": ["day", "data"], "campaign": ["campaign name", "campaign"], "adset": ["ad set name", "adset"],
         "ad": ["ad name"], "spent": ["amount spent", "valor gasto", "gasto"], "impr": ["impressions", "impress"],
         "clicks": ["link clicks", "clicks", "cliques"], "leads": ["leads"],
         "pv": ["landing page views", "page views", "pageviews"],
         # Este cliente não tem coluna de Checkout/Add to Cart no Meta Ads —
         # fica None (a UI mostra "-").
         "chk": ["adds to cart", "add to cart", "initiate checkout", "checkouts iniciados", "checkouts"],
         # Resultado real das campanhas de Engajamento/WhatsApp (adicionada
         # pelo cliente no extrator) — usado no lugar de Link Clicks pra não
         # superestimar (nem todo clique vira conversa de fato).
         "msg_conv": ["messaging conversations started", "conversas por mensagem", "conversas iniciadas"],
         "link": ["creative instagram permalink", "instagram permalink", "permalink",
                  "creative link", "link do anuncio", "link do criativo"]},
        {"day": 0, "campaign": 1, "adset": 2, "ad": 3, "impr": 4, "clicks": 5, "pv": 6, "spent": 7},
    )
    ad_struct = build_ad_struct(meta_rows, midx)

    meta = []
    ad_links = {}
    for row in meta_rows[1:]:
        if not any((c or "").strip() for c in row):
            continue
        ad = cell(row, midx["ad"]) or "(sem anúncio)"
        link = cell(row, midx["link"])
        if link and ad not in ad_links:
            ad_links[ad] = link
        camp = cell(row, midx["campaign"]) or "(sem campanha)"
        meta.append({
            "d": parse_date(cell(row, midx["day"])),
            "camp": camp,
            "adset": cell(row, midx["adset"]) or "(sem conjunto)",
            "ad": ad,
            "sp": round(to_float(cell(row, midx["spent"])), 4),
            "im": to_float(cell(row, midx["impr"])),
            "cl": to_float(cell(row, midx["clicks"])),
            "pv": to_float(cell(row, midx["pv"])),
            "ck": to_float(cell(row, midx["chk"])),
            "ml": to_float(cell(row, midx["leads"])),
            # funil (Quiz/LP, WhatsApp/Engajamento, ou "outros" fora da
            # convenção) — separa as abas "Funil ..." sem misturar dados.
            "funnel": classify_funnel(camp),
        })

    # "Página 2" — funil "Visitas ao Perfil" (E1-DIST, Alcance/Engajamento),
    # não o E2-CAP deste dashboard. Traz Campaign Name/Ad Set Name/Ad Name
    # (atribuível por anúncio, igual à Página 1) — vira sua PRÓPRIA aba
    # "Funil Visitas ao Perfil", nunca misturada na quebra por campanha do
    # E2-CAP (aba "Funil Quiz"/"Funil WhatsApp"). Sem "Messaging Conversations
    # Started" nem Pontuação — não gera leads/MQL (funil de topo, não de
    # captura), então não entra em leads[].
    mo_header = meta_other_rows[0] if meta_other_rows else []
    mo_idx = header_index(
        mo_header,
        {"day": ["day", "data"], "campaign": ["campaign name", "campaign"],
         "adset": ["ad set name", "adset"], "ad": ["ad name"],
         "spent": ["amount spent", "valor gasto", "gasto"],
         "impr": ["impressions", "impress"],
         "clicks": ["link clicks", "clicks", "cliques"],
         "pv": ["landing page views", "page views", "pageviews"]},
        {"day": 0, "spent": 1, "impr": 3},
    )
    meta_other = []
    for row in meta_other_rows[1:]:
        if not any((c or "").strip() for c in row):
            continue
        d = parse_date(cell(row, mo_idx["day"]))
        if not d:
            continue
        meta_other.append({
            "d": d,
            "camp": cell(row, mo_idx["campaign"]) or "(sem campanha)",
            "adset": cell(row, mo_idx["adset"]) or "(sem conjunto)",
            "ad": cell(row, mo_idx["ad"]) or "(sem anúncio)",
            "sp": round(to_float(cell(row, mo_idx["spent"])), 4),
            "im": to_float(cell(row, mo_idx["impr"])),
            "cl": to_float(cell(row, mo_idx["clicks"])),
            "pv": to_float(cell(row, mo_idx["pv"])),
            "funnel": "perfil",
        })

    # Leads = 2 fontes distintas, mantidas separáveis por "src" (o gráfico
    # "Leads por origem" do app.js já separa por esse campo):
    #   1) aba "Sessões" (quiz/LP) — só Status == "Enviou" (completou o
    #      formulário); é aí que mora a Pontuação (MQL).
    #   2) campanhas de Engajamento/WhatsApp (Campaign Name contém "ENGJ") —
    #      não passam pelo quiz; cada "Messaging Conversations Started" vira
    #      1 lead sintético (sem pontuação — não dá pra qualificar 1 a 1).
    lheader = leads_rows[0] if leads_rows else []
    lidx = header_index(
        lheader,
        {"start": ["início", "inicio"], "last": ["última atividade", "ultima atividade"],
         "status": ["status"], "score": ["pontuação", "pontuacao"],
         "campanha": ["campanha"], "origem": ["origem"], "ad_id": ["ad_id"]},
        {"start": 1, "last": 2, "status": 5, "score": 7, "origem": 11, "campanha": 12, "ad_id": 8},
    )

    def is_test_session(origem, campanha, ad_id):
        blob = f"{origem} {campanha} {ad_id}".lower()
        return "test" in blob

    leads = []
    for row in leads_rows[1:]:
        if not any((c or "").strip() for c in row):
            continue
        if cell(row, lidx["status"]) != "Enviou":
            continue
        origem = cell(row, lidx["origem"])
        campanha_col = cell(row, lidx["campanha"])
        ad_id = cell(row, lidx["ad_id"])
        if is_test_session(origem, campanha_col, ad_id):
            continue
        struct = ad_struct.get(origem) if origem else None
        if struct:
            camp, adset, ad, src = struct["camp"], struct["adset"], origem, "meta"
        elif valid_utm(campanha_col):
            camp, adset, ad, src = campanha_col, "(sem conjunto)", (origem or "(sem anúncio)"), "meta"
        else:
            # Sessão sem Origem/Campanha reconhecida (orgânico/direto, sem
            # clique de anúncio pra atribuir) — cliente pediu que o total de
            # Leads bata com o Ads Manager (que só enxerga o que veio de
            # clique), então essas sessões NÃO entram em leads[] (nem no
            # total, nem no funil, nem nas MQLs).
            continue
        leads.append({
            "d": parse_date(cell(row, lidx["last"]) or cell(row, lidx["start"])),
            "src": src,
            "plat": "ig" if src == "meta" else "—",
            "camp": camp,
            "adset": adset,
            "ad": ad,
            "prof": "Sem resposta",
            "bucket": "Sem resposta",
            "q": 1 if is_qualified(cell(row, lidx["score"])) else 0,
            "utm": 1 if src == "meta" else 0,
            "nm": "—",
            "em": "—",
            "ph": "—",
        })

    # Leads de Engajamento/WhatsApp: 1 lead sintético por conversa iniciada
    # ("Messaging Conversations Started", coluna adicionada pelo cliente no
    # extrator), só nas campanhas de Engajamento (não duplica quem já entra
    # via Sessões/Enviou, pois essas pessoas não passam pelo quiz). NÃO usa
    # Link Clicks — nem todo clique vira conversa de fato (confirmado: no
    # período 03/08–01/09/2026, Link Clicks somava 391 mas o resultado real
    # da campanha no Ads Manager era 186 conversas — quase 2× de diferença).
    for row in meta_rows[1:]:
        if not any((c or "").strip() for c in row):
            continue
        camp = cell(row, midx["campaign"])
        if ENGAJAMENTO_TAG not in camp:
            continue
        n_leads = round(to_float(cell(row, midx["msg_conv"])))
        if n_leads <= 0:
            continue
        d = parse_date(cell(row, midx["day"]))
        adset = cell(row, midx["adset"]) or "(sem conjunto)"
        ad = cell(row, midx["ad"]) or "(sem anúncio)"
        for _ in range(n_leads):
            leads.append({
                "d": d, "src": "whatsapp", "plat": "ig",
                "camp": camp, "adset": adset, "ad": ad,
                "prof": "Sem resposta", "bucket": "Sem resposta",
                "q": 0, "utm": 1, "nm": "—", "em": "—", "ph": "—",
            })

    # Agendamentos: agregado DIÁRIO preenchido pelo comercial (sem telefone/nome,
    # sem atribuição por anúncio) — só entra em totals()/daily() no app.js
    # (Visão Geral/Relatório), nunca na quebra por campanha/conjunto/anúncio.
    # "Data" vem sem ano (ex. "09/07") — assume o ano corrente do build; datas
    # futuras (linhas em branco pré-criadas p/ o resto do ano) são descartadas.
    aheader = agenda_rows[0] if agenda_rows else []
    aidx = header_index(
        aheader,
        {"date": ["data"], "agendamentos": ["agendamentos confirmados"],
         "cirurgias": ["cirurgias confirmadas"], "fat_cirurgia": ["valor total cirurgias"]},
        {"date": 0, "agendamentos": 1, "cirurgias": 4, "fat_cirurgia": 6},
    )
    now_brt = datetime.now(BRT)
    today_str = now_brt.strftime("%Y-%m-%d")
    year_ref = now_brt.year
    agenda = []
    for row in agenda_rows[1:]:
        if not any((c or "").strip() for c in row):
            continue
        m = re.match(r"^(\d{1,2})/(\d{1,2})$", cell(row, aidx["date"]))
        if not m:
            continue
        dd, mm = int(m.group(1)), int(m.group(2))
        if not (1 <= mm <= 12 and 1 <= dd <= 31):
            continue
        d = f"{year_ref:04d}-{mm:02d}-{dd:02d}"
        if d > today_str:
            continue
        agendamentos = to_float(cell(row, aidx["agendamentos"]))
        cirurgias = to_float(cell(row, aidx["cirurgias"]))
        fat = to_float(cell(row, aidx["fat_cirurgia"]))
        if agendamentos == 0 and cirurgias == 0 and fat == 0:
            continue
        agenda.append({"d": d, "agendamentos": agendamentos, "vendas": cirurgias, "fat": round(fat, 2)})

    dates = sorted({d for d in (
        [l["d"] for l in leads if l["d"]] + [m["d"] for m in meta if m["d"]] + [a["d"] for a in agenda if a["d"]]
        + [m["d"] for m in meta_other if m["d"]]
    )})
    return {
        "build": {
            "generated_at_brt": now_brt.strftime("%d/%m/%Y %H:%M"),
            "build_id": datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"),
            "today": today_str,
            "date_min": dates[0] if dates else None,
            "date_max": dates[-1] if dates else None,
            "tax_factor": TAX_FACTOR,
            "sample_min_spend": SAMPLE_MIN_SPEND,
            "sample_min_mqls": SAMPLE_MIN_MQLS,
            "top_ads_n": TOP_ADS_N,
            "meta_cpmql": META_CPMQL,
            "meta_cac": META_CAC,
            "volume_min_amostral": VOLUME_MIN_AMOSTRAL,
            "n_dias_corte": N_DIAS_CORTE,
        },
        "leads": leads,
        "meta": meta,
        "sales": [],   # sem aba de Compradores neste cliente — vendas vêm de agenda[]
        "agenda": agenda,
        "meta_other": meta_other,   # "Página 2" — só totals()/daily(), nunca buildAgg()
        "ad_links": ad_links,
        # Insights de Tráfego (texto pré-escrito, lido de relatorios.json). Preenchido
        # em main() via load_briefings(); fica {} se relatorios.json não existir.
        "briefings": {},
    }


# --------------------------------------------------------------------------- #
# Insights de Tráfego (aba Relatório)
# --------------------------------------------------------------------------- #
def load_briefings(path: str) -> dict:
    """Lê build/relatorios.json. Estrutura:
        {"generated_at": "...", "periodos": {"<preset>": {"html": "..."}, ...}}
    Retorna o dict inteiro (ou {} se o arquivo não existir/for inválido).
    A geração NÃO acontece aqui — este build só lê o texto já pronto, sem
    chamar nenhuma API (custo zero no build/no navegador)."""
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            obj = json.load(f)
        return obj if isinstance(obj, dict) else {}
    except (ValueError, OSError):
        return {}


# --------------------------------------------------------------------------- #
# Render
# --------------------------------------------------------------------------- #
def render(data, template_path):
    # A dashboard e montada a partir de arquivos separados (visual x logica):
    #   template.html          -> esqueleto HTML (placeholders __STYLES__/__APP_JS__)
    #   identidade-visual.css  -> TODAS as cores (edite aqui p/ mexer so em cor)
    #   estilos.css            -> layout/componentes
    #   app.js                 -> logica + renderizacao
    # Esta funcao so COSTURA os arquivos e injeta os dados; nao altera nada deles.
    base = os.path.dirname(os.path.abspath(template_path))

    def readf(name):
        with open(os.path.join(base, name), "r", encoding="utf-8") as f:
            return f.read()

    with open(template_path, "r", encoding="utf-8") as f:
        tpl = f.read()
    styles = readf("identidade-visual.css") + "\n" + readf("estilos.css")
    tpl = tpl.replace("__STYLES__", styles)
    tpl = tpl.replace("__APP_JS__", readf("app.js"))
    tpl = tpl.replace("__DATA_JSON__", json.dumps(data, ensure_ascii=False))
    tpl = tpl.replace("__BUILD_ID__", data["build"]["build_id"])
    tpl = tpl.replace("__GENERATED_BRT__", data["build"]["generated_at_brt"])
    return tpl


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--leads-file", help="CSV local da aba Sessões (fonte única de leads via quiz/LP)")
    ap.add_argument("--meta-file", help="CSV local da aba Meta Ads (Página 1)")
    ap.add_argument("--agenda-file", help="CSV local da aba Planilha agendamento")
    ap.add_argument("--meta-other-file", help="CSV local da aba Página 2 (gasto/impressões sem atribuição de campanha)")
    ap.add_argument("--template", default="build/template.html")
    ap.add_argument("--out", default="dist/index.html")
    args = ap.parse_args()

    meta_rows = load_rows(sheet_url(SPREADSHEET_ID_META, SHEET_META), args.meta_file)
    leads_rows = load_rows(sheet_url(SPREADSHEET_ID_LEADS, SHEET_LEADS), args.leads_file)
    agenda_rows = load_rows(sheet_url(SPREADSHEET_ID_AGENDA, SHEET_AGENDA), args.agenda_file)
    meta_other_rows = load_rows(sheet_url(SPREADSHEET_ID_META, SHEET_META_OTHER), args.meta_other_file)

    data = process(leads_rows, meta_rows, agenda_rows, meta_other_rows)

    # Insights de Tráfego (texto pré-escrito) — lidos do arquivo versionado ao
    # lado do template. Sem chamada de API no build.
    briefings_path = os.path.join(os.path.dirname(os.path.abspath(args.template)), "relatorios.json")
    data["briefings"] = load_briefings(briefings_path)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(render(data, args.template))

    b = data["build"]
    q = sum(l["q"] for l in data["leads"])
    n_quiz = sum(1 for l in data["leads"] if l["src"] != "whatsapp")
    n_wa = sum(1 for l in data["leads"] if l["src"] == "whatsapp")
    vd = sum(a["vendas"] for a in data["agenda"])
    fat = sum(a["fat"] for a in data["agenda"])
    print("== build ok ==", file=sys.stderr)
    print(f"  periodo   : {b['date_min']} -> {b['date_max']}", file=sys.stderr)
    print(f"  leads     : {len(data['leads'])} (quiz/LP: {n_quiz}  whatsapp: {n_wa})  MQLs (Pontuação > 33): {q}", file=sys.stderr)
    print(f"  agenda    : {len(data['agenda'])} dias com dado  vendas: {vd}  faturamento: R$ {fat:,.2f}", file=sys.stderr)
    n_fq = sum(1 for m in data["meta"] if m["funnel"] == "quiz")
    n_fw = sum(1 for m in data["meta"] if m["funnel"] == "whatsapp")
    n_fo = sum(1 for m in data["meta"] if m["funnel"] == "outros")
    print(f"  meta      : {len(data['meta'])} linhas (quiz: {n_fq}  whatsapp: {n_fw}  outros: {n_fo})", file=sys.stderr)
    mo_sp = sum(m["sp"] for m in data["meta_other"])
    print(f"  meta_other: {len(data['meta_other'])} linhas (funil Visitas ao Perfil)  gasto: R$ {mo_sp:,.2f}", file=sys.stderr)
    print(f"  out       : {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
