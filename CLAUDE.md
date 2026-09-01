# CLAUDE.md — Contexto do projeto (Dashboard Dr. Vinícius, a partir do TEMPLATE High Ticket)

> Este arquivo é lido automaticamente pelo Claude Code ao abrir o repositório.
> Ele carrega TODO o contexto necessário para continuar o trabalho sem depender
> de mensagens anteriores. Mantenha-o atualizado.
>
> **Este repositório já está configurado** para o cliente Dr. Vinícius
> (funil E2-CAP). Para replicar o template (engine) para outro cliente, veja
> `GUIA-REPLICACAO.md` — a lista de arquivos "específico do cliente" que
> mudam a cada replicação está em `AGENTS.md`.

---

## ✅ CHECKLIST DE NOVO CLIENTE (referência para replicar — este repo já está feito)

1. **`build/build.py` — constantes do topo:**
   - `SPREADSHEET_ID_META`/`SHEET_META`, `SPREADSHEET_ID_LEADS`/`SHEET_LEADS`,
     `SPREADSHEET_ID_AGENDA`/`SHEET_AGENDA` — ID + nome da aba de cada planilha
     do cliente (podem ser 1 planilha com várias abas, ou várias planilhas
     separadas como neste cliente — `build.py` busca por NOME da aba via gviz).
   - `CLIENT_NAME`, `MAIN_PRODUCT` — nome do cliente e da oferta principal.
   - `MAIN_PRODUCT_PREFIX` — prefixo comum às campanhas do cliente.
   - `TAX_FACTOR` — fator de imposto/taxa da mídia (1.0 = sem imposto).
2. **`build/build.py` — critério de MQL:** ajuste `is_qualified()` e os aliases
   das colunas em `process()`/`header_index()` ao critério e ao cabeçalho da
   aba de leads do cliente.
3. **`build/app.js`:** revisar os rótulos fixos de UI que citam o critério de MQL
   ("MQLs (...)") e o agrupamento de dimensão de leads (aqui: "Procedimento") —
   o critério de `build.py` não propaga sozinho para esses textos.
4. **`build/template.html`:** preencher `<title>` e o logo (`logo-main`/`logo-sub`)
   com o nome/slogan do cliente. (Opcional: trocar o favicon base64.)
5. **`build/identidade-visual.css`:** ajustar cores se o cliente tiver identidade
   própria (opcional — o default funciona).
6. **`README.md` / `SETUP-CRON.md` / este `CLAUDE.md` / `AGENTS.md`:** owner/repo
   do GitHub, URL do GitHub Pages, nome do cliente, planilhas/abas.
7. **`build/GUIA-RELATORIOS.md`:** preencher o "Contexto do funil" (cliente,
   oferta, critério de MQL).
8. **GitHub Pages + Actions:** confirmar que `build/` + `.github/workflows/deploy.yml`
   estão na `main` (ativa `workflow_dispatch`); rodar o workflow uma vez.
9. **cron-job.org:** seguir `SETUP-CRON.md` — token fine-grained novo (Actions:
   read/write, só neste repo), nunca reaproveitar um token exposto em chat.
10. **Insights de Tráfego (opcional):** `build/relatorios.json` e
    `build/relatorios_dados.json` começam vazios (`{}`). Para ativar os Insights:
    - deixar a Routine do Actions `briefing.yml` rodar (gera `relatorios_dados.json`
      com os números), e
    - criar a **Routine do Claude** (`create_trigger` apontando para este repo)
      que lê os números + os 2 guias e escreve `relatorios.json` na `main`
      (ver "Briefing automático" abaixo). **Não vem pronta neste repo** — não
      foi criada (opcional, a pedir).
11. **Testar local** com CSVs de amostra antes de publicar (3 páginas, tema
    claro/escuro, multi-seleção).

> **Fora do escopo deste template:** não há Cloudflare Worker nem chamada paga à
> API da Anthropic no pipeline. A automação de Insights é feita por Routine
> agendada do Claude Code (item 10). Se o cliente precisar de outra camada, é
> desenvolvimento novo.

---

## O que é

Dashboard de **Captura de Leads** — um app de BI estático (HTML/CSS/JS
puro + Chart.js via CDN) publicado no **GitHub Pages**, que cruza a lista de
**Leads** com o gerenciador de mídia paga e se atualiza sozinho a cada ~30 min
(build 100% na nuvem via GitHub Actions, disparado externamente pelo cron-job.org).

- **URL pública:** `https://scale-ag.github.io/dash-drvinicius/`
- **Somente leitura** das planilhas. Nunca escrever de volta.

## Fontes de dados (Google Sheets)

Este cliente usa **3 planilhas SEPARADAS** (não uma central com múltiplas
abas) — `build.py` lê cada uma por **nome da aba**, via endpoint `gviz`
(`.../gviz/tq?tqx=out:csv&sheet=<nome>`), então não depende de gid.

| Planilha | ID | Aba | Colunas usadas |
|-----|-----|-----|----------------|
| **Meta Ads** | `1L-QoyOYAp-ifK4Db9fbESRKDm2X-CGRurKs_3hADjKQ` | `Página 1` | `Day` · `Campaign Name` · `Ad Set Name` · `Ad Name` · `Impressions` · `Link Clicks` · `Landing Page Views` · `Amount Spent` · `Messaging Conversations Started` (leads de WhatsApp/ENGJ — ver abaixo) (sem coluna de Checkout/Add to Cart nem Leads — ficam "-") |
| **Meta Ads — Página 2** | (mesma planilha acima) | `Página 2` | `Day` · `Amount Spent` · `Reach` · `Impressions` — **sem Campaign Name** (outro funil/conta, ex. "E1-DIST"; cliente confirmou não ser o mesmo funil E2-CAP). Vira `DATA.meta_other[]`: entra no Gasto/Impressões da Visão Geral e do Relatório (por pedido do cliente), mas **nunca** na quebra por campanha/conjunto/anúncio da aba "Captura Meta Ads" — sem Campaign Name não dá pra atribuir. |
| **Leads** (fonte única de leads) | `1tFaH49FCD2egRPjbzKP8_KixwXyyRjhMyOONSiLpR2I` | `Sessões` | 1 linha por **sessão** do quiz/formulário de qualificação: `Início`/`Última atividade` · `Status` (`Em andamento`/`Enviou`/`Desqualificado`) · `Pontuação` (escore MQL) · `Origem` (nome do anúncio) · `Campanha` (raramente preenchida). Só linhas com `Status == "Enviou"` viram lead. |
| **Agendamentos** | `1cOD2Sa9fp8TPJrBia7RY3br_Htg5pCJc5squzmLY4Dk` | `Planilha agendamento` | agregado **diário**: `Data` (DD/MM, sem ano) · `Agendamentos Confirmados` · `Cirurgias Confirmadas` · `Valor Total Cirurgias` |

> ⚠️ **Não confundir** com a aba **"Leads"** (28 linhas, mesma planilha de
> Sessões) — apesar do nome, ela é na verdade um registro **por agendamento**
> (Procedimento/Atendimento/Decisão/Investimento, atribuído por anúncio via
> "Origem"), preenchido pelo comercial depois do contato. **Não é lida** pelo
> `build.py` — pode se sobrepor aos totais da planilha diária de Agendamentos
> sem uma chave segura pra cruzar (nem telefone nem data exata em comum
> confirmados), então fica de fora do pipeline por enquanto (nem leads[], nem
> agenda[], pra não contar nada em dobro). Se o cliente quiser uma visão
> "Agendamentos por anúncio" a partir dela, é feature nova a pedir.

### Regra de Lead Qualificado (MQL) e fontes de Leads
Duas fontes de Leads, mantidas **separadas por `src`** (o gráfico "Leads por
origem" já distingue):
1. **Quiz/LP** (`src="meta"`/`"org"`) — aba **Sessões**, só `Status == "Enviou"`
   (completou o formulário). MQL = coluna **"Pontuação" > 33** (`build.py` →
   `is_qualified`). Linhas de teste (`ad_id`/`Origem`/`Campanha` contendo
   "test", ex. `TEST_AD_123`/`TESTE_AD_VINI`) são descartadas.
2. **WhatsApp/Engajamento** (`src="whatsapp"`) — campanhas do Meta Ads cujo
   `Campaign Name` contém **"ENGJ"** (`ENGAJAMENTO_TAG` em `build.py`) não
   passam pelo quiz: cada **"Messaging Conversations Started"** dessas
   campanhas vira **1 lead sintético** (sem nome/telefone/pontuação — não dá
   pra qualificar uma conversa individual, `q=0` sempre). Campanhas `LEADS|`
   (Quiz/LP) **não** geram lead sintético — esses leads já entram via
   Sessões/Enviou, e contar de novo também duplicaria.
   > **Não usa Link Clicks** — nem todo clique vira conversa de fato:
   > confirmado com o cliente que, no período 03/08–01/09/2026, Link Clicks
   > somava 391 mas o resultado real da campanha no Ads Manager era 186
   > conversas (quase 2× de diferença). O cliente adicionou a coluna
   > "Messaging Conversations Started" na extração automática (app Adveronix,
   > mesmo processo que já preenche `Página 1`) — sem trabalho manual diário.

Como nenhuma das duas fontes atuais traz o procedimento de interesse
(a aba Sessões não tem essa coluna — só a aba "Leads"/Agendamentos, que não
é lida), os campos `prof`/`bucket` ficam fixos em `"Sem resposta"`; os
gráficos "Leads por procedimento" e "Procedimentos mais buscados" (`app.js`)
mostram isso até existir uma fonte com o procedimento por lead.

### Atribuição do anúncio (Sessões → Campanha/Conjunto/Anúncio)
A aba Sessões não traz Campanha/Conjunto prontos por linha (`ad_id`/
`adset_id`/`campaign_id` vêm sempre vazios nos dados reais) — a coluna
**"Origem"** carrega o **nome do anúncio**, idêntico ao `Ad Name` do Meta Ads
(confirmado: ~87% de match nos dados reais). `build_ad_struct()` (`build.py`)
cruza por esse nome e escolhe a combinação (Campanha, Conjunto) de **maior
gasto** no Meta para aquele anúncio (um anúncio pode rodar em mais de um
conjunto). Quando "Origem" está vazia, cai no fallback da coluna "Campanha"
(quando preenchida) ou vira `(sem campanha)`/`src="org"`. Os leads sintéticos
de WhatsApp/Engajamento já vêm com Campanha/Conjunto/Anúncio exatos da
própria linha do Meta Ads — não precisam desse cruzamento.

### Agendamentos & Vendas/Faturamento (agregado diário, sem Compradores)
Não há aba de Compradores/New Subscriptions neste cliente. `build.py` lê a
planilha de **Agendamentos** — um agregado **diário** preenchido pelo
comercial, **sem telefone/nome**, então **sem chave de atribuição por
anúncio**. Vira `DATA.agenda[]` (`{d, agendamentos, vendas, fat}`, onde
`vendas` = "Cirurgias Confirmadas" e `fat` = "Valor Total Cirurgias"). A coluna
"Data" vem sem ano (ex. "09/07") — `build.py` assume o ano corrente do build
e descarta linhas com data futura (linhas em branco pré-criadas para o resto
do ano) e linhas totalmente zeradas.

No navegador, `agendaActive()` (`app.js`) filtra `agenda[]` pela mesma data
ativa dos outros arrays, e **só entra em `totals()`/`daily()`** (Visão Geral
e Relatório — que espelha a Visão Geral) — **nunca em `buildAgg()`**, porque
não há como atribuir a um anúncio. Por isso a aba de mídia paga (página 2) e
o Top Anúncios (Relatório) mostram Agendamentos/Vendas/Faturamento como "-"
(caem de volta ao critério de MQLs).

### Imposto da mídia paga
`TAX_FACTOR = 1.0` em `build.py` (sem imposto informado para este cliente). O
toggle "Imposto Meta" fica **ativo por padrão** (`STATE.tax=true` em
`app.js`); com `TAX_FACTOR = 1.0` o toggle não muda nada. Se o cliente
informar um fator depois, edite a constante (ex. `1.13806` para 13,806%).

### Convenções de campanha (do cliente)
Todas as campanhas observadas usam o prefixo `DR. VINICIUS | E2-CAP`
(`MAIN_PRODUCT_PREFIX`) — só há UMA sigla de funil até agora (`E2-CAP`), com
a etapa de tráfego `P2-FRIO` em todas as campanhas atuais (não incluída no
prefixo, para não excluir futuras etapas P1/P3 se o cliente criar). O build
não filtra por esse prefixo — mantém TODAS as campanhas no dashboard.

## Arquitetura / arquivos

```
build/build.py            # lê os CSVs (read-only) de 3 planilhas separadas, emite REGISTROS BRUTOS (leads[]/meta[]/agenda[]/ad_links); render() COSTURA os 4 arquivos abaixo
build/template.html       # esqueleto HTML. Placeholders __STYLES__, __APP_JS__, __DATA_JSON__, __BUILD_ID__, __GENERATED_BRT__
build/identidade-visual.css  # TODAS as cores (tema claro=padrão / escuro). Mexa AQUI p/ trocar só cor
build/estilos.css         # layout/componentes (sidebar, topbar, period-picker, funil, tabelas, gráficos, aba Relatório)
build/app.js              # lógica + renderização (KPIs, funil, tabelas, filtro cruzado, period-picker, heatmap, Relatório)
build/relatorios.json     # Insights de Tráfego por período (aba Relatório) — VERSIONADO; lido no build, sem API. Vazio no template ({}).
build/relatorios_dados.json      # números brutos por período (insumo p/ a Routine escrever relatorios.json) — não lido pelo site. Vazio no template ({}).
build/relatorio_lib.py           # datas/agregação compartilhadas (gerar_relatorios.py + coletar_dados_relatorio.py)
build/coletar_dados_relatorio.py # gera relatorios_dados.json (só números, sem texto) — roda no briefing.yml, 1x/dia
build/gerar_relatorios.py        # gera relatorios.json determinístico (sem IA) — fallback MANUAL, não roda mais sozinho
build/GUIA-RELATORIOS.md            # formato/estrutura dos Insights da aba Relatório (os 7 blocos) — preencher o contexto do funil
build/GUIA-INTERPRETACAO-METRICAS.md # regras de diagnóstico por métrica (High Ticket) — leitura obrigatória p/ redigir
.github/workflows/deploy.yml    # roda build.py e publica no Pages (workflow_dispatch + schedule + push)
.github/workflows/briefing.yml  # roda coletar_dados_relatorio.py e commita relatorios_dados.json na main (cron 1x/dia)
dist/index.html           # saída gerada (gitignored; o Actions reconstrói)
GUIA-REPLICACAO.md        # como replicar este modelo para outros relatórios/clientes
SETUP-CRON.md             # valores exatos do cron-job.org (com marcadores a preencher)
```

### Aba Relatório
Terceira página (sidebar, entre a de mídia paga e o rodapé). **Espelha a Visão
Geral** (mesmo funil/KPIs/gráficos/tabela diária, via `renderGeralCore(REL_IDS)`)
e, abaixo, acrescenta 3 blocos novos + um painel de metas editável:
- **Metas & parâmetros (painel editável)** — no topo da aba: Meta CPMQL, Meta CAC, Volume
  mínimo amostral (MQLs), N dias p/ corte. Persiste em `localStorage['dm_metas']`, default de
  `build.py` (`META_CPMQL`/`META_CAC`=None → "não definida"; `VOLUME_MIN_AMOSTRAL`/`N_DIAS_CORTE`).
  Editar recolore **CPMQL/CAC** nas tabelas de anúncio (verde ≤ meta · amarelo até +30% ·
  vermelho acima) e ajusta o badge Em observação/Avaliável, **tudo ao vivo**
  (`METAS` + `renderRelAds()` em `app.js`).
- **Top Anúncios** e **Piores Anúncios** — 17 colunas + coluna **Status** (Anúncio · Status ·
  Campanha · Conjunto · Gasto · Impr · CPM · CTR · Leads · CPL · MQLs · Tx‑MQL · CPMQL · ConvMQL ·
  Vendas · CAC · Faturamento · ROAS · **Link**). Anúncio, Status e Link ficam **sticky**.
  Ranking pelo **resultado mais profundo disponível** (Venda→MQL), amostra relevante primeiro;
  sem amostra → badge **"Em observação"**. Limiares em `build.py`: `SAMPLE_MIN_SPEND`,
  `SAMPLE_MIN_MQLS`, `TOP_ADS_N`.
- **Insights de Tráfego** — texto por período redigido pelo **Claude** (linguagem de
  gestor de tráfego), lido de `build/relatorios.json` (sem API no build/navegador —
  o site só exibe o texto já pronto). Formato em **4 quadrantes** por período. Cada
  período compara com o período anterior **correto para aquela janela** (regra em
  `relatorio_lib.previous_period`). Chaves de período fixas
  (`hoje/ontem/3d/7d/14d/30d/mes/mespass/todo`), tags `Escalar/Otimizar/Cortar/Observar`.
  Toda a aritmética é pré-calculada em `build/relatorios_dados.json` — a Routine só
  interpreta, nunca recalcula. Regras completas em `build/GUIA-RELATORIOS.md` +
  `build/GUIA-INTERPRETACAO-METRICAS.md`. `app.js` ainda reconhece o formato antigo
  (`{"html": "…"}`) como fallback.

### Briefing automático do gestor (Routine do Claude, sem chamada à API Anthropic)
`build/relatorios.json` pode ser escrito 1×/dia por uma **Routine do Claude**
(Claude Code Remote — mesma infraestrutura de sessão/agente deste repo, agendada;
não é chamada paga à API). Fluxo em 2 etapas, porque o ambiente da Routine não
alcança `docs.google.com` (só o runner do GitHub Actions alcança):
1. `build/coletar_dados_relatorio.py` (GitHub Actions, `.github/workflows/briefing.yml`,
   1×/dia) agrega **só números** em `build/relatorios_dados.json` e commita na `main`.
2. A Routine do Claude lê esse JSON + `build/GUIA-RELATORIOS.md` +
   `build/GUIA-INTERPRETACAO-METRICAS.md`, redige `build/relatorios.json` e faz
   commit/push direto na `main`, disparando o `deploy.yml`. **Precisa ser criada
   por cliente** (`create_trigger` apontando para o repo novo) — não vem pronta.

`build/gerar_relatorios.py` (gerador determinístico, sem IA) continua no repo só
como **fallback manual**. Limitação conhecida: usa os defaults de `build.py`
(`META_CPMQL`/`META_CAC`/`VOLUME_MIN_AMOSTRAL`/`N_DIAS_CORTE`), não o que o gestor
editou no painel (fica em `localStorage`).

Funil completo: `Impressões → Cliques → Leads → MQLs → Agendamentos → Reuniões
Realizadas → Vendas → Faturamento`. Agendamentos/Vendas/Faturamento já vêm do
agregado diário da planilha de Agendamentos (`DATA.agenda[]`) — acendem na
Visão Geral/Relatório, mas ficam "-" na aba de mídia paga e no Top Anúncios
(sem atribuição por anúncio). Reuniões Realizadas (No‑Show/CPRR) seguem "-" —
a planilha não distingue agendado × comparecido.

### Link do criativo (aba de mídia paga)
`build.py` lê uma coluna opcional de permalink do criativo na aba de mídia →
mapa `ad_links` (anúncio → 1 permalink). Usado no "Link" das tabelas Top/Piores.
Sem a coluna, o link vira "—".

> **Layout modular:** o front-end é separado em `identidade-visual.css` + `estilos.css`
> + `app.js`, costurados por `render()` nos placeholders `__STYLES__`/`__APP_JS__`.
> Página 1 usa **funil vertical de leads** + KPIs secundários. Topbar tem
> **seletor de período em calendário** (default "Este mês"). **Heatmap** = cor FIXA
> por métrica (só opacidade varia): **Gasto=vermelho · Leads=azul · MQLs=ciano ·
> Vendas=verde · ROAS=amarelo** (`--heat-gasto/leads/mqls/vendas/roas`).

O `build.py` **não agrega**: exporta as linhas cruas e TODA a lógica (filtros de
data, filtro cruzado, KPIs, tabelas, gráficos, heatmap, imposto) roda no navegador.

## Rodar/testar local

```bash
python build/build.py --leads-file leads.csv --meta-file meta.csv --agenda-file agenda.csv --out dist/index.html
# (o sandbox do agente NÃO alcança docs.google.com; use CSVs locais para testar.
#  O runner do GitHub Actions tem internet e busca os CSVs ao vivo.)
```

## Especificação funcional (resumo)

Três **páginas separadas** (sidebar):
1. **Visão Geral de Leads** — funil vertical (Gasto → Impressões → Cliques → Leads →
   MQLs → Agendamentos → Vendas/Faturamento) + KPIs secundários; gráfico combinado
   diário + tabela diária com heatmap (todos os leads); barras por origem/procedimento/
   plataforma/procedimentos mais buscados.
2. **Captura mídia paga** — funil em etapas; combinado diário; barras por utm_content;
   tabela diária com heatmap (só mídia paga); 3 tabelas hierárquicas Campanha →
   Conjunto → Anúncio, cada uma com gráfico de linha embaixo.
3. **Relatório** — espelha a Visão Geral + painel de Metas editável + Top/Piores
   Anúncios (17 colunas + Status) + Insights de Tráfego. Ver `build/GUIA-RELATORIOS.md`.

**Ordem das colunas nas tabelas:** `Data · Dia · Gasto · CPM · CTR · ConvForm · Leads ·
CPL · Tx‑MQL · MQLs · CPMQL · ConvMQL · Vendas · CAC · Fat. · Receita · ROAS`. Este
cliente **não tem** coluna de Checkout/Add to Cart no Meta Ads — as colunas
Checkouts/VisCHK foram removidas de `DAILY_COLS` (`app.js`) em vez de aparecerem
sempre como "-".

**Regras obrigatórias das tabelas** (ver `GUIA-REPLICACAO.md`): cabeçalho sticky;
ordenação tri‑state; colunas redimensionáveis (persist localStorage); linha
"Total Geral" fixa; dimensão nunca truncada; seleção com toggle + Ctrl multi;
filtro cruzado bidirecional; tabela diária com último dia no topo; heatmap de cor
fixa por métrica.

## Lacunas de dados
- **Reuniões Realizadas / No‑Show** → a planilha de Agendamentos não distingue
  agendado × comparecido; aparece "-" até vir essa distinção.
- **Agendamentos/Vendas/Faturamento por campanha/anúncio** → a planilha de
  Agendamentos é um agregado diário sem telefone; só entra na Visão Geral/
  Relatório (totais), nunca na quebra por campanha (aba de mídia paga).
- Enquanto não vierem, essas métricas aparecem como "-".

## Publicação — problemas conhecidos
1. **Push:** se a integração GitHub da sessão for somente‑leitura (403), o caminho
   é `git push` direto para `github.com` com o **PAT do usuário**. Nunca gravar o
   token no `.git/config` (usar URL efêmera `https://x-access-token:<TOKEN>@github.com/...`).
2. **cron-job.org só funciona na `main`:** `workflow_dispatch` só existe na branch
   padrão. Levar `build/` + `.github/workflows/deploy.yml` para a `main`.
3. **Pages liga sozinho:** `actions/configure-pages@v5` com `enablement: true`
   (precisa `permissions: pages: write, id-token: write`).
4. **Proxy do sandbox:** o ambiente do agente costuma NÃO alcançar `docs.google.com`,
   `*.github.io` nem a API REST de Actions/Pages — mas o runner do Actions alcança tudo.
5. **Token exposto:** se um token foi colado no chat, **revogar e gerar um novo**.

## Branch / git
- Desenvolvimento na branch designada da sessão; manter sincronizada com `main`.
