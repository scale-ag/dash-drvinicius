# AGENTS.md — Dashboard de captura de leads (High Ticket) · Dr. Vinícius

> Contexto completo em **`CLAUDE.md`** (mesma pasta) — leia-o antes de mexer no
> projeto. Este arquivo é um resumo para agentes/ferramentas que seguem a
> convenção `AGENTS.md`.
>
> Cliente já configurado (Dr. Vinícius / E2-CAP). Para replicar este template
> em outro cliente, veja `GUIA-REPLICACAO.md` — os pontos que mudam por
> cliente estão listados abaixo, em "Específico do cliente".

## Configuração deste cliente (referência rápida)

1. **`build/build.py` — constantes do topo:** `SPREADSHEET_ID_META`/`SHEET_META`,
   `SPREADSHEET_ID_LEADS`/`SHEET_LEADS`, `SPREADSHEET_ID_AGENDA`/`SHEET_AGENDA`,
   `CLIENT_NAME`, `MAIN_PRODUCT`, `MAIN_PRODUCT_PREFIX`, `TAX_FACTOR`.
2. **Critério de MQL:** `is_qualified()` — coluna "Pontuação" (aba Leads) > 33.
3. **`build/app.js`:** rótulos `'MQLs (Pontuação > 33)'` e agrupamento por
   "Procedimento" (não "especialidade/profissão" — este funil é de paciente,
   não de médico).
4. **`build/template.html`:** `<title>` e logo (`logo-main`="Dr. Vinícius"/`logo-sub`="E2-CAP").
5. **`build/identidade-visual.css`:** paleta padrão (sem identidade própria pedida).
6. **`README.md` / `CLAUDE.md` / `SETUP-CRON.md`:** owner `scale-ag`, repo
   `dash-drvinicius`, URL `https://scale-ag.github.io/dash-drvinicius/`.
7. **`build/GUIA-RELATORIOS.md`:** "Contexto do funil" preenchido.
8. **GitHub Pages + Actions:** `build/` + `.github/workflows/deploy.yml` na
   `main` (ativa `workflow_dispatch`); workflow já rodado.
9. **cron-job.org:** seguir `SETUP-CRON.md` — token fine-grained novo (Actions:
   read/write, só neste repo), nunca reaproveitar um token exposto em chat.
10. **Insights de Tráfego (opcional):** `build/relatorios.json` e
    `build/relatorios_dados.json` começam vazios (`{}`). Ativar: deixar `briefing.yml`
    gerar os números + criar a **Routine do Claude** (`create_trigger` apontando para
    este repo) que redige `relatorios.json` na `main`. **Não vem pronta** — não foi criada.
11. **Testado localmente** com CSVs de amostra antes de publicar.

> **Fora do escopo deste template:** não há Cloudflare Worker nem chamada paga à
> API da Anthropic. A automação de Insights é uma Routine agendada do Claude Code
> (item 10). Qualquer outra camada é desenvolvimento novo.

## Engine (não muda entre clientes)
`build/template.html`, `build/app.js`, `build/estilos.css`,
`.github/workflows/deploy.yml`, `.github/workflows/briefing.yml`,
`build/relatorio_lib.py`, `build/coletar_dados_relatorio.py`,
`build/gerar_relatorios.py`, `build/GUIA-INTERPRETACAO-METRICAS.md`,
`GUIA-REPLICACAO.md` — tabelas, filtros, gráficos, heatmap, tema claro/escuro,
coleta/redação dos Insights. Ver `GUIA-REPLICACAO.md` para os detalhes de
implementação (filtro cruzado, engine de tabela, gráficos Chart.js).

> `template.html` e `app.js` são engine, mas carregam o nome do cliente em pontos
> pontuais (título/logo, rótulos de MQL/procedimento) — já preenchidos para
> este cliente; ao replicar para outro, procure por "Dr. Vinícius"/"E2-CAP"/
> "Pontuação > 33" nesses dois arquivos.

## Específico do cliente (troca a cada replicação)
`build/build.py`, `build/identidade-visual.css` (cores, se aplicável),
`build/relatorios.json` + `build/relatorios_dados.json` (conteúdo — começam vazios),
`build/GUIA-RELATORIOS.md` (contexto do funil), `README.md`, `CLAUDE.md`,
`SETUP-CRON.md`.
