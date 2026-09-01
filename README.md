# Dashboard de Captura de Leads · Dr. Vinícius

Dashboard **100% na nuvem** do Funil de High Ticket de **Dr. Vinícius** que
cruza a aba **Sessões** (quiz/formulário de qualificação) e os cliques das
campanhas de WhatsApp/Engajamento com o investimento de mídia paga
(**Meta Ads**) e com a planilha diária de **Agendamentos** (preenchida pelo
comercial), calcula os **Leads Qualificados (MQLs)** e é publicada no
**GitHub Pages**. Reconstrói sozinha a cada ~30 min, disparada pelo
**cron-job.org** — sem depender de nenhum PC ligado.

**URL pública:** `https://scale-ag.github.io/dash-drvinicius/`

---

## O que ela mostra

- **KPIs**: Gasto Total, Leads Totais, CPL, **MQLs** (Pontuação > 33), CPMQL, Tx-MQL, Impressões, Cliques, CTR, CPC, CPM.
- **Evolução diária**: gasto/dia, leads × MQLs/dia, CPL × CPMQL/dia.
- **Qualificação & origem**: leads por procedimento (qualificado destacado), por origem (mídia paga vs. orgânico), por plataforma.
- **Cruzamento por campanha**: gasto (mídia paga) × leads/MQLs (lista) → CPL, CPMQL e Tx-MQL calculados.
- **Agendamentos/Vendas/Faturamento** (Visão Geral e Relatório): agregado diário da planilha de Agendamentos — sem atribuição por anúncio, por isso não entra na quebra por campanha da aba de mídia paga.
- **Tabela de leads qualificados** (e-mail e telefone **mascarados**, pois a página é pública).
- **Toggle de imposto da mídia paga** (opcional) e **modo claro/escuro**.
- **Aba Relatório**: painel de metas editável + Top Anúncios + Insights de Tráfego (texto, preenchido manualmente ou por automação própria — ver `build/GUIA-RELATORIOS.md`).

## Critério de Lead Qualificado (MQL)

Coluna **"Pontuação"** (aba Sessões) **> 33**. Lógica em `build.py` → `is_qualified`.
Só se aplica aos leads de Quiz/LP — leads de WhatsApp/Engajamento (cliques)
não têm pontuação individual (ver abaixo).

## Fontes de dados (somente leitura)

Três planilhas Google Sheets separadas, lidas por **nome da aba** (via `gviz`,
não depende de gid):

| Planilha | Aba | Uso |
|-----|-----|-----|
| Meta Ads | `Página 1` | gasto, impressões, cliques, page views. Campanhas com **"ENGJ"** no nome = WhatsApp/Engajamento: cada "Messaging Conversations Started" vira 1 lead |
| Meta Ads | `Página 2` | gasto/impressões sem Campaign Name (outro funil/conta) — entra só no total geral (Visão Geral/Relatório), nunca na quebra por campanha |
| Leads | `Sessões` | fonte de leads do Quiz/LP — 1 linha por sessão; só `Status == "Enviou"` vira lead. Traz Pontuação (MQL), Origem (nome do anúncio) |
| Agendamentos | `Planilha agendamento` | agregado **diário** do comercial — Agendamentos Confirmados, Cirurgias Confirmadas, Valor Total Cirurgias (sem telefone/atribuição por anúncio) |

O build lê essas abas via **export CSV público** (`gviz/tq?tqx=out:csv&sheet=...`).
**Nada é escrito de volta** nas planilhas.

> Existe também uma aba **"Leads"** na planilha de Sessões (28 linhas) que,
> apesar do nome, é um registro por **agendamento** (não é lida pelo build —
> ver `CLAUDE.md`).

Atribuição do anúncio de cada lead: a coluna **"Origem"** da aba Sessões traz o
nome do anúncio (igual ao "Ad Name" do Meta Ads) — `build.py` cruza por esse
nome e herda Campanha/Conjunto do Meta (maior gasto, se o anúncio rodou em
mais de um conjunto).

---

## Arquitetura

```
cron-job.org  ──(POST workflow_dispatch a cada 30 min)──▶  GitHub Actions
                                                              │
                          build/build.py  lê os CSVs ◀────────┘
                                 │  cruza dados + calcula MQLs
                                 ▼
                          dist/index.html  ──▶  deploy  ──▶  GitHub Pages (URL pública)
```

- `build/build.py` — baixa os CSVs, cruza os dados, gera `dist/index.html`.
- `build/template.html` — layout/gráficos/tema (Chart.js via CDN).
- `.github/workflows/deploy.yml` — roda o build e publica no Pages.

**Cache-bust:** a página usa `Cache-Control: no-cache`, mostra o horário do último
build, tem botão **Atualizar** e se recarrega sozinha (`?t=timestamp`) ~30 min após
aberta — sempre pegando a versão mais nova.

## Rodar localmente (opcional)

```bash
python build/build.py --out dist/index.html            # busca os CSVs ao vivo
# ou, com arquivos locais para teste:
python build/build.py --leads-file leads.csv --meta-file meta.csv \
  --agenda-file agenda.csv --out dist/index.html
```

---

## Ativação (uma vez) e cron-job.org

O disparo por `workflow_dispatch` só funciona quando o workflow está na branch
**`main`**. Veja **`SETUP-CRON.md`** para o passo a passo e os valores exatos
(URL, headers e body) a colar no cron-job.org.

> ⚠️ **Segurança:** nunca comite tokens no repositório. Gere um token
> *fine-grained*, só com **Actions: read/write** neste repositório, e use-o
> apenas no cron-job.org (ou em GitHub Secrets, se aplicável).

## Como usar este template para um novo cliente

Veja o **CHECKLIST DE NOVO CLIENTE** no topo de `CLAUDE.md` (ou `AGENTS.md`) e
o passo a passo completo em `GUIA-REPLICACAO.md`.
