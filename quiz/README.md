# Quiz de pré-atendimento — Dr. Vinícius

Fonte do formulário de qualificação que alimenta a dashboard deste repo.

`index.html` partiu de uma **cópia fiel** do que estava no ar em
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

Sobre a cópia: além da cópia fiel (preservada no commit `c9a5761`), o arquivo
hoje traz `eventID` no Lead, o modo `?fbdebug=1` e a **minimização de dado de
saúde** descrita abaixo.

## Minimização de dado de saúde enviado ao pixel (14/09/2026)

Aplicada em resposta ao bloqueio do Meta. Saíram do pixel **todos** os eventos
personalizados que associavam a pessoa a um funil médico:

| Evento removido | Por que | Onde continua medido |
|---|---|---|
| `trackCustom('QuizStep', {step_key})` | `step_key` carrega nomes clínicos (`procedimento`, `plano`) | beacon → aba **Funil** da planilha |
| `trackCustom('PreAtendimentoStart')` | nomeia o funil como pré-atendimento médico | aba **Funil** (etapa 0) |
| `trackCustom('PreAtendimentoComplete')` | idem, no fim do funil | aba **Leads** (a linha existir já é a conclusão) |
| `trackCustom('QuizDisqualify')` | "desqualificado" aqui significa plano de saúde — dado de saúde puro | beacon → aba **Funil** |
| `trackCustom('WhatsAppClick')` | sinal do mesmo funil, sem valor próprio | — |

Sobra no pixel só o essencial: `init`, `PageView` e o `Lead` de conversão.
Verificado em Chromium headless com o fluxo completo: **16 → 4 chamadas ao
pixel**, e as **11 chamadas ao Apps Script intactas** — nenhuma medição nossa
foi perdida, porque o funil por etapa sempre foi da planilha, não do Meta.

Lever ainda disponível, se a revisão do Meta pedir mais: o advanced matching
(`fbq('init', PIXEL_ID, {ph, fn})` em `submitLead`) manda telefone e primeiro
nome. Não é dado clínico, e tirá-lo custa qualidade de correspondência — por
isso ficou. É a próxima coisa a cair se necessário.

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

### Causa raiz confirmada: bloqueio por dado de saúde (não é verificação de domínio)

Events Manager → aba "Ações" (14/09/2026):

> **Alguns dados do site foram bloqueados**
> "Alguns dados do site são bloqueados porque parecem inconsistentes com nossos
> Termos das Ferramentas da Meta para Empresas, pois podem: estar associados a
> **condições médicas, estados de saúde específicos ou relacionamentos entre
> prestador de serviços e paciente**."
>
> Sites bloqueados:
> - `drviniciusdemello.netlify.app`
> - `drviniciusmello.com`
> - `lp.drviniciusmello.com`

**Os TRÊS domínios estão bloqueados — inclusive o domínio próprio do cliente.**
Isso descarta a hipótese anterior (registrada aqui por engano) de que faltava
verificação de domínio e de que um domínio próprio resolveria. Não resolve:
`drviniciusmello.com` já é dele e está na lista.

Não é problema técnico nem de configuração. É **enforcement de política do Meta
sobre dado de saúde**, aplicado ao conjunto de dados inteiro.

Consequências práticas:

- Trocar de hospedagem (Netlify → Pages) **não levanta o bloqueio**. Publicar o
  quiz em `<pages>/quiz/` continua valendo pelo controle do código, mas não
  restaura o evento.
- **Conversions API não é contorno.** A política vale para o conjunto de dados,
  não só para o pixel do navegador — e usar CAPI para driblar um bloqueio ativo
  é violação de termos, com risco para a conta de anúncios inteira.
- **Domínio novo para "resetar" o flag também não é caminho**: o classificador
  avalia o conteúdo, então reclassifica; e fazê-lo com intenção de evadir é
  violação, arriscando a conta.

Caminhos legítimos, em ordem:

1. **"Analisar solução"** no próprio card — é o fluxo de revisão/contestação do
   Meta. Primeiro passo, gratuito.
2. **Minimização real do dado enviado** (conformidade de verdade, não disfarce):
   não mandar ao pixel nada que revele o interesse clínico da pessoa. Hoje o
   quiz não envia as respostas, mas envia `trackCustom('QuizStep', {step_key})`
   com chaves como `procedimento`/`plano`, além de `PreAtendimentoStart` e
   `PreAtendimentoComplete` — sinais que associam a pessoa a um funil médico.
3. **Trocar o mecanismo de conversão** para um que não dependa do pixel do site:
   campanha de Mensagem/WhatsApp (a `ENGJ`, que já roda e já é a maior fonte de
   lead deste cliente) ou Formulário Instantâneo dentro do Facebook/Instagram.

**A dashboard não é afetada.** `build.py` lê os leads direto da planilha
(Sessões/Leads), nunca do Meta — o bloqueio derruba a otimização da campanha,
não o relatório. Leads, MQLs e atribuição por anúncio (via `Origem`/utm_content)
continuam funcionando normalmente.

### 2. Migração para a agência

Ordem obrigatória quando for migrar (regra do próprio padrão de quiz):
1. publicar o **Apps Script novo** (conta Google da agência) como App da Web,
   "executar como Eu", acesso "Qualquer pessoa";
2. **só então** publicar o HTML apontando `CFG.LEAD_ENDPOINT` para o /exec novo;
3. trocar a URL de destino nos anúncios.

O cabeçalho das abas `Leads` e `Sessões` **tem que permanecer idêntico** — é o
que o `build/build.py` lê. Mudou coluna, a dashboard para de contar lead.

Migrar resolve controle do código, **não** o bloqueio do Meta — ver acima.

> `CFG.LEAD_ENDPOINT` é uma URL pública de App da Web (já visível no
> view-source do site no ar). Não é credencial, mas o Apps Script novo deve
> ser publicado sob a conta da agência, não reaproveitado.
