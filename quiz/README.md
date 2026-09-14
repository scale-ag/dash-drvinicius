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

### 1. Evento `Lead` no Meta Ads não está marcando

**Estado em 14/09/2026: ainda aberto.** O que já foi descartado, com prova:

| Hipótese | Veredito | Como foi testada |
|---|---|---|
| "Não republicaram o HTML depois de trocar Schedule→Lead (10/08)" | ❌ descartada | O view-source do site no ar já tem `CONV_EVENT: "Lead"` |
| "O formulário/Apps Script quebrou" | ❌ descartada | Teste real em 14/09 05:02 gravou a linha na aba Leads normalmente |
| "`fbq.apply(null, arguments)` em `fbq_safe()` mata a chamada" | ❌ descartada | Fluxo completo rodado em Chromium headless com `fbq` instrumentado: as 16 chamadas (init, PageView, 10× QuizStep, Lead com eventID, PreAtendimentoComplete) chegam ao pixel, nas duas versões. O script não roda em strict mode, então `this` vira o objeto global e a chamada é idêntica à direta. |

Ou seja: **o quiz dispara `fbq('track','Lead')` corretamente.** O problema está
entre o navegador e o Events Manager, não no código do formulário.

O fato que ainda não tem explicação: nos Eventos de teste de 14/09 apareceu
**só o `PageView`**, e nenhum dos `trackCustom` (`QuizStep` dispara em toda
troca de tela) nem o `Lead`. Como o disparo está provado, sobra:

1. **`fbevents.js` não carregou** (bloqueador, extensão, DNS, ITP). Sem a
   biblioteca, `fbq` continua sendo o stub e as chamadas ficam presas em
   `fbq.queue` — nada sai do navegador. Não explica o PageView ter chegado,
   a menos que ele tenha vindo de outra origem.
2. **Filtro do painel.** O seletor ao lado de "Limpar atividade" estava em
   "5 opções selecionadas" — pode estar escondendo eventos recebidos.
3. **Defasagem do próprio painel** — o PageView é de 05:02:29 e o lead foi
   gravado às 05:02:56; se a captura de tela saiu nesse intervalo, o Lead
   ainda não teria aparecido.
4. **Configuração de otimização/atribuição** — a campanha otimizando uma
   conversão personalizada antiga em vez do evento padrão `Lead`.

**Instrumento para fechar o diagnóstico:** abrir o quiz com `?fbdebug=1` e o
console do navegador aberto. Cada chamada vira uma linha `[pixel] enviado: …`
e, no momento do Lead, `fbDiag()` imprime **se o `fbevents.js` carregou** e
quantas chamadas estão presas na fila. Isso separa (1) de (2)/(3)/(4) de vez.

Melhoria já aplicada: o `Lead` agora vai com **`eventID`** (`<sid>-lead`), e o
mesmo id é gravado no payload da planilha (`event_id`). Sem isso não dá para
somar a Conversions API depois sem contar o mesmo lead duas vezes — e a CAPI é
o caminho para recuperar o sinal que o navegador perde (ATT/iOS, bloqueadores).

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
