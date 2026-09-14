# Quiz de pré-atendimento — Dr. Vinícius

Fonte do formulário de qualificação que alimenta a dashboard deste repo.

`index.html` é **cópia fiel** do que estava no ar em
`https://drviniciusdemello.netlify.app` em 14/09/2026 (obtida via view-source;
só foram removidos os `<meta>` que a Netlify injeta no HTML servido). Foi
arquivada aqui para a agência ter o código sob controle — hoje o deploy ainda
é na conta Netlify do gestor anterior (Tanuri Marketing).

**Este repo ainda NÃO publica o quiz.** O GitHub Pages daqui serve a dashboard
(`dist/index.html`, gerado por `.github/workflows/deploy.yml`). Migrar o quiz
para o Pages da agência é passo separado — e, quando for feito, exige trocar a
URL de destino nos anúncios do Meta.

## Como ele conversa com a dashboard

```
quiz (index.html) --POST--> Apps Script (/exec) --> planilha 1tFaH49F...
                                                     ├── aba "Leads"   (1 linha por lead enviado)
                                                     ├── aba "Sessões" (1 linha por visitante)  <-- build.py lê ESTA
                                                     └── aba "Funil"   (queda por etapa)
```

- `submitLead()` monta o payload com todas as respostas + `pontuacao` + `origem`.
- `origem` vem de `utm_content` / `ad_id` da URL do anúncio, e é **o nome do
  anúncio** — é essa a chave que `build.py::build_ad_struct()` cruza com o
  `Ad Name` do Meta Ads para atribuir o lead a Campanha/Conjunto/Anúncio.
- `CFG.CORTE_ALTA = 33` é o corte de "Prioridade: Alta", aplicado pelo Apps
  Script. **A dashboard usa o mesmo número** (`CORTE_ALTA` em `build/build.py`):
  MQL = Prioridade Alta. Mudou um, muda o outro.

Pontuação: mínimo real 16, máximo 48 (a pergunta de procedimento tem
`score:false`, não pontua). Quem marca "Outro plano de saúde" cai em
`disqualify()` (`p:-99`) antes da tela de contato — não deixa telefone e
**não dispara o evento de conversão**, de propósito.

## Pendências conhecidas

### 1. Evento `Lead` não marca — CAUSA ENCONTRADA (14/09/2026)

**O Meta está suprimindo o evento de propósito.** Console do navegador no site
no ar, vindo do próprio `fbevents.js`:

```
[Meta Pixel] — You are attempting to send an unverified event.
The event was suppressed. Go to Events Manager to learn more.   fbevents.js:202
```

Não é falha de disparo. O quiz chama `fbq('track','Lead')` corretamente e a
biblioteca do Meta recebe a chamada — ela é que decide não enviar.

Provas de que o código está certo (todas as outras hipóteses caíram):

| Hipótese | Veredito | Prova |
|---|---|---|
| Não republicaram o HTML depois de trocar Schedule→Lead | ❌ | view-source do site no ar já tem `CONV_EVENT: "Lead"` |
| Formulário/Apps Script quebrado | ❌ | teste real de 14/09 gravou a linha na aba Leads |
| `fbq.apply(null, arguments)` mata a chamada | ❌ | fluxo completo em Chromium headless: as 16 chamadas chegam ao pixel nas duas versões (o script não roda em strict mode, `this` vira o objeto global) |
| `fbevents.js` bloqueado / chamadas presas na fila | ❌ | `fbq.queue.length === 0` e o próprio `fbevents.js:202` emitindo o aviso — a biblioteca carregou e está rodando |
| **Meta suprimindo evento não verificado** | ✅ **é esta** | aviso explícito no console + aba "Ações" do Events Manager com alerta pendente |

**Onde resolver:** Events Manager → dataset `1601913367590883` → aba **"Ações"**
(estava com marcador vermelho de pendência já no primeiro print). É lá que o
Meta diz exatamente o que exige.

Causa provável: o funil é de **cirurgia plástica** e o quiz coleta dado de
saúde (procedimento de interesse, plano de atendimento). O Meta trata
categoria sensível com regra mais dura e suprime eventos até o negócio
completar a verificação — normalmente **verificação de domínio** em
Configurações do Negócio → Segurança da Marca → Domínios.

### ⚠️ Impacto no plano de migração: domínio próprio é requisito

`drviniciusdemello.netlify.app` **não é um domínio verificável** no Meta —
`netlify.app` é domínio compartilhado (Public Suffix List), ninguém verifica um
subdomínio dele. **`github.io` tem exatamente o mesmo problema**, então publicar
o quiz em `scale-ag.github.io/dash-drvinicius/quiz/` dá controle à agência mas
**não resolve a supressão**.

Para o evento voltar a marcar, o quiz precisa rodar num **domínio próprio**
(ex.: `quiz.<dominio-do-doutor>.com.br`) que possa ser verificado no Business
Manager. O Pages deste repo aceita domínio customizado — é configurar o CNAME.

### 2. Migração para a agência

Ordem obrigatória quando for migrar (regra do próprio padrão de quiz):
1. publicar o **Apps Script novo** (conta Google da agência) como App da Web,
   "executar como Eu", acesso "Qualquer pessoa";
2. **só então** publicar o HTML apontando `CFG.LEAD_ENDPOINT` para o /exec novo;
3. trocar a URL de destino nos anúncios.

O cabeçalho das abas `Leads` e `Sessões` **tem que permanecer idêntico** — é o
que o `build/build.py` lê. Mudou coluna, a dashboard para de contar lead.

> `CFG.LEAD_ENDPOINT` é uma URL pública de App da Web (já visível no
> view-source do site no ar). Não é credencial, mas o Apps Script novo deve
> ser publicado sob a conta da agência, não reaproveitado.
