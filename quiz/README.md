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

### 1. Evento `Lead` no Meta Ads não está marcando direito

O que este fonte **prova** (e portanto elimina como causa): o site no ar já
está com `CONV_EVENT: "Lead"` e chama `fbq('track','Lead')` em `submitLead()`.
A troca de `Schedule` para `Lead` (10/08) **foi publicada**. Não é caso de
"esqueceram de republicar o HTML".

Pontos do código que ainda podem derrubar/subnotificar o evento:

- **`fbq('init', PIXEL_ID, {ph, fn})` é chamado uma segunda vez** dentro de
  `submitLead()`, com o pixel já inicializado no rodapé da página. Meta trata
  re-init do mesmo pixel como "Duplicate Pixel ID". É o caminho documentado
  para advanced matching manual, mas convém confirmar no Events Manager que
  não está sendo descartado.
- **Não há `eventID`** no `track`. Sem chave de deduplicação não dá para somar
  a Conversions API depois, e hoje 100% do sinal depende do navegador —
  ATT/iOS, bloqueador e ITP comem uma fatia que pode ser grande. É a
  explicação mais provável para "a planilha tem mais lead do que o gerenciador".
- **Sem Conversions API.** Só pixel de navegador.

Teste que decide (1 minuto, não precisa mexer em código): Events Manager →
**Testar eventos** → abrir o quiz no navegador → completar o formulário.
- `Lead` aparece → o código está certo; o problema é configuração de
  otimização/atribuição (ex.: a campanha otimizando uma conversão
  personalizada antiga em vez do evento padrão `Lead`).
- `Lead` NÃO aparece → o problema é no disparo, e aí vale mexer no código acima.

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
