# CURSOR PROMPT — VORTEXIA (nome fantasia) · MEI Tiago Aureliano da Rocha
# Nível: Staff Engineer + Product Strategist
# Stack: Next.js 15 · Tailwind CSS · TypeScript · Groq · Supabase · Telegram

---

## IDENTIDADE LEGAL (obrigatório no site)

**Titular MEI:** Tiago Aureliano da Rocha  
**CNPJ:** 61.699.939/0001-80  
**Situação:** MEI ativo desde 11/07/2025  
**Natureza jurídica:** Microempreendedor Individual — **NÃO usar "Ltda" em lugar nenhum**

**Nome fantasia (marca no site):** Vortexia  
**Apresentação ao visitante:** Vortexia — Inteligência de negócios  
**Rodapé obrigatório:** Tiago Aureliano da Rocha · CNPJ 61.699.939/0001-80 · Caraguatatuba/SP

Nunca abreviar publicamente para "SignalHub", "Lex Rocha" ou "Zairyx" na landing.  
Esses nomes são **classificação interna** (niche no Groq) e produtos downstream.

### CNAEs relevantes (CCMEI)

| CNAE | Uso |
|------|-----|
| **7319-0/02** Promoção de vendas | SignalHub, dorking, Reddit, alertas Telegram, landing inbound |
| **8219-9/99** Apoio administrativo / documentos | Lex Rocha, NF de qualificação de demandas, relatórios |
| **8599-6/03** Treinamento em informática | Zairyx onboarding (fase 2) |

**Descrição de serviço na NF e no site:**  
→ *Qualificação de demandas comerciais e apoio à prospecção*  
→ **Nunca:** "plataforma de IA", "SaaS", "software sob encomenda"

---

## ECOSSISTEMA — como tudo se conecta

```
GOOGLE DORKING / REDDIT / GRUPOS PÚBLICOS
        ↓ (detecção de dor pública — posts abertos)
  signalhub/ — CNAE 7319-0/02 ✅
  "Promoção de vendas por internet"
        ↓ (score ≥ 7, red flags filtradas)
  Alerta Telegram → aprovação manual (botões R1/R2/R3)
        ↓
  Resposta manual no post/grupo
        ↓ (lead quente ou curioso)
  vortexia-web/ — CNAE 7319 + 8219 ✅
        ↓ (formulário + /api/qualify)
  Groq → dimensões brutas → computeFinalScore() no código
        ↓
  Supabase → dataset proprietário
        ↓ (final_score ≥ 70)
  Follow-up manual → NF 8219-9/99 ou 7319-0/02
```

**SignalHub** (`../signalhub/`) já existe — Python, Groq, Telegram, PM2.  
**vortexia-web/** é o MVP inbound — criar ao lado de `signalhub/`.

---

## OBJETIVO DO MVP (7 dias)

Landing corporativa neutra + formulário de captação de demanda.  
Nenhum produto, nicho ou tecnologia mencionados publicamente.

Fluxo:

```
Visitante → formulário → POST /api/qualify → Groq → computeFinalScore() → Supabase → Telegram
```

Sem dashboard. Sem auth. Sem Stripe. Sem menu.  
Uma página. Um formulário. Um endpoint. Um alerta.

---

## STACK EXATA

```
Framework:   Next.js 15 (App Router)
Estilo:      Tailwind CSS (inputs nativos — shadcn opcional, não obrigatório)
Linguagem:   TypeScript strict
IA:          groq-sdk (openai/gpt-oss-120b)
Banco:       @supabase/supabase-js (server-side, service role key)
Deploy:      Vercel (Free tier ok no MVP)
Node:        >= 18.17
```

---

## ESTRUTURA DE PASTAS

```
vortexia-web/
├── app/
│   ├── page.tsx                  ← landing + formulário
│   ├── layout.tsx                ← meta, fonte, robots noindex
│   ├── globals.css
│   └── api/
│       └── qualify/
│           └── route.ts          ← POST handler completo
├── lib/
│   ├── groq.ts                   ← shim web + cliente Groq
│   ├── supabase.ts               ← service role (server-only)
│   └── score.ts                  ← computeFinalScore() — NUNCA Groq aqui
├── supabase/
│   └── migration.sql             ← schema leads (não executar automaticamente)
├── .env.local.example
├── .gitignore
├── package.json
├── tailwind.config.ts
└── tsconfig.json
```

---

## ARQUIVO: lib/groq.ts

```typescript
import 'groq-sdk/shims/web'
import Groq from 'groq-sdk'

export const groq = new Groq({
  apiKey: process.env.GROQ_API_KEY!,
})
```

---

## ARQUIVO: lib/score.ts

```typescript
export interface GroqDimensions {
  buying_intent: number
  urgency: number
  problem_severity: number
  niche: 'lexrocha' | 'zairyx' | 'outro'
  intent_summary: string
  red_flags: string[]
}

const WEIGHTS = {
  buying_intent: 0.40,
  urgency: 0.35,
  problem_severity: 0.25,
} as const

const RED_FLAG_PATTERN =
  /advogado|advogada|processo aberto|só pesquisando|apenas curiosidade|sem orçamento/i

function clamp(n: number): number {
  return Math.max(0, Math.min(100, Math.round(n)))
}

export function computeFinalScore(dims: GroqDimensions): number {
  let score =
    clamp(dims.buying_intent) * WEIGHTS.buying_intent +
    clamp(dims.urgency) * WEIGHTS.urgency +
    clamp(dims.problem_severity) * WEIGHTS.problem_severity

  if (dims.red_flags?.some((f) => RED_FLAG_PATTERN.test(f))) {
    score *= 0.7
  }

  return Math.round(score)
}

export const SCORE_WEIGHTS = WEIGHTS
```

---

## ARQUIVO: lib/supabase.ts

```typescript
import { createClient } from '@supabase/supabase-js'

export const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)
```

---

## ARQUIVO: app/api/qualify/route.ts

```typescript
import { NextResponse } from 'next/server'
import { groq } from '@/lib/groq'
import { supabase } from '@/lib/supabase'
import { computeFinalScore, SCORE_WEIGHTS, type GroqDimensions } from '@/lib/score'

const GROQ_SYSTEM = `Você qualifica demandas comerciais brasileiras para apoio à prospecção.
Retorne SOMENTE JSON válido, sem markdown.

{
  "buying_intent": 0-100,
  "urgency": 0-100,
  "problem_severity": 0-100,
  "niche": "lexrocha" | "zairyx" | "outro",
  "intent_summary": "frase única até 120 caracteres",
  "red_flags": []
}

Regras:
- buying_intent >= 70 SOMENTE se há intenção real de contratar ou resolver pagando
- urgency = urgência declarada ou implícita
- problem_severity = gravidade do PROBLEMA, não capacidade financeira da pessoa
- niche: lexrocha = CDC/consumidor; zairyx = delivery/restaurante; outro = demais
- red_flags: ex. ["já tem advogado", "só pesquisando"]
- NUNCA inferir financial_capacity — não existe neste schema
- Sem informação suficiente → pontue 50`

type LeadInput = {
  nome_ou_razao: string
  email: string
  telefone?: string
  mensagem: string
  source?: string
  website?: string // honeypot — se preenchido, rejeitar silenciosamente
}

export async function POST(req: Request) {
  let body: LeadInput
  try {
    body = await req.json()
  } catch {
    return NextResponse.json({ error: 'JSON inválido' }, { status: 400 })
  }

  if (body.website?.trim()) {
    return NextResponse.json({ ok: true, mensagem: 'Recebemos sua mensagem.' })
  }

  const { nome_ou_razao, email, mensagem, telefone, source } = body

  if (!nome_ou_razao?.trim() || !email?.trim() || !mensagem?.trim()) {
    return NextResponse.json(
      { error: 'nome_ou_razao, email e mensagem são obrigatórios' },
      { status: 400 }
    )
  }

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return NextResponse.json({ error: 'E-mail inválido' }, { status: 400 })
  }

  let dims: GroqDimensions
  try {
    const completion = await groq.chat.completions.create({
      model: 'openai/gpt-oss-120b',
      max_tokens: 300,
      temperature: 0.1,
      response_format: { type: 'json_object' },
      messages: [
        { role: 'system', content: GROQ_SYSTEM },
        {
          role: 'user',
          content: [
            `Nome ou razão social: ${nome_ou_razao}`,
            `E-mail: ${email}`,
            telefone ? `Telefone: ${telefone}` : null,
            `Mensagem: ${mensagem}`,
          ]
            .filter(Boolean)
            .join('\n'),
        },
      ],
    })
    dims = JSON.parse(completion.choices[0].message.content ?? '{}') as GroqDimensions
  } catch (err) {
    console.error('[qualify] Groq erro:', err)
    dims = {
      buying_intent: 50,
      urgency: 50,
      problem_severity: 50,
      niche: 'outro',
      intent_summary: 'Erro na classificação — revisar manualmente',
      red_flags: ['groq_error'],
    }
  }

  const final_score = computeFinalScore(dims)

  const { data: lead, error: dbError } = await supabase
    .from('leads')
    .insert({
      nome_ou_razao,
      email,
      telefone: telefone ?? null,
      mensagem,
      source: source ?? 'landing',
      niche: dims.niche,
      buying_intent: dims.buying_intent,
      urgency_score: dims.urgency,
      problem_severity: dims.problem_severity,
      intent_summary: dims.intent_summary,
      red_flags: dims.red_flags,
      final_score,
      score_weights: SCORE_WEIGHTS,
      status: 'novo',
      telegram_sent: false,
    })
    .select('id, final_score, niche, intent_summary')
    .single()

  if (dbError || !lead) {
    console.error('[qualify] Supabase erro:', dbError)
    return NextResponse.json({ error: 'Erro ao salvar lead' }, { status: 500 })
  }

  const urgenciaLabel =
    dims.urgency >= 80 ? 'Alta' : dims.urgency >= 60 ? 'Média' : 'Baixa'
  const nicheLabel = { lexrocha: 'CDC', zairyx: 'Delivery', outro: 'Outro' }[dims.niche]
  const flagsTexto =
    dims.red_flags.length > 0 ? `Red flags: ${dims.red_flags.join(', ')}` : ''

  const mensagemTelegram = [
    `Lead: ${nome_ou_razao}`,
    `Score: ${final_score}/100 | ${nicheLabel} | Urgência: ${urgenciaLabel}`,
    `${email}${telefone ? ` | ${telefone}` : ''}`,
    '',
    dims.intent_summary,
    flagsTexto,
    '',
    'Mensagem:',
    mensagem.slice(0, 300) + (mensagem.length > 300 ? '...' : ''),
    '',
    `ID: ${lead.id}`,
  ]
    .filter(Boolean)
    .join('\n')

  try {
    const tgRes = await fetch(
      `https://api.telegram.org/bot${process.env.TELEGRAM_BOT_TOKEN}/sendMessage`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chat_id: process.env.TELEGRAM_CHAT_ID,
          text: mensagemTelegram,
          disable_web_page_preview: true,
        }),
      }
    )
    if (tgRes.ok) {
      await supabase.from('leads').update({ telegram_sent: true }).eq('id', lead.id)
    }
  } catch (err) {
    console.error('[qualify] Telegram erro:', err)
  }

  return NextResponse.json({
    ok: true,
    leadId: lead.id,
    mensagem: 'Recebemos sua mensagem. Em breve entraremos em contato.',
  })
}
```

---

## ARQUIVO: app/page.tsx (trechos-chave)

```tsx
'use client'

const MARCA = 'Vortexia'
const TITULAR = 'Tiago Aureliano da Rocha'
const CNPJ = '61.699.939/0001-80'

// Estado do form:
// nome_ou_razao, email, telefone, mensagem, website (honeypot hidden)

// Label do campo principal:
// "Nome ou razão social" — placeholder: "João Silva ou Empresa Exemplo Ltda"

// Usar <form onSubmit={handleSubmit}> — NÃO onClick solto no botão

// Rodapé:
// © {ano} {MARCA} · {TITULAR} · CNPJ {CNPJ} · Caraguatatuba/SP
// Serviços de qualificação de demandas comerciais e apoio à prospecção.
```

---

## ARQUIVO: app/layout.tsx

```tsx
export const metadata = {
  title: 'Vortexia — Inteligência de negócios',
  description:
    'Qualificação de demandas comerciais para empresas e profissionais brasileiros.',
  robots: 'noindex, nofollow',
}
```

---

## MIGRATION SQL — SUPABASE

```sql
create table if not exists leads (
  id                uuid primary key default gen_random_uuid(),
  created_at        timestamptz not null default now(),

  nome_ou_razao     text not null,
  email             text not null,
  telefone          text,
  mensagem          text not null,
  source            text default 'landing',

  niche             text check (niche in ('lexrocha','zairyx','outro')),
  buying_intent     int  check (buying_intent between 0 and 100),
  urgency_score     int  check (urgency_score between 0 and 100),
  problem_severity  int  check (problem_severity between 0 and 100),
  intent_summary    text,
  red_flags         text[] default '{}',

  final_score       int  not null check (final_score between 0 and 100),
  score_weights     jsonb default '{"buying_intent":0.4,"urgency":0.35,"problem_severity":0.25}',

  status            text not null default 'novo'
                    check (status in ('novo','contatado','convertido','descartado')),
  telegram_sent     boolean default false,
  notas             text
);

create index leads_created_at_idx  on leads (created_at desc);
create index leads_final_score_idx on leads (final_score desc);
create index leads_status_idx      on leads (status);
create index leads_niche_idx       on leads (niche);

alter table leads enable row level security;
grant usage on schema public to anon, authenticated, service_role;
grant all on leads to service_role;
```

---

## VARIÁVEIS (.env.local.example)

```bash
GROQ_API_KEY=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
NEXT_PUBLIC_SITE_URL=http://localhost:3000
```

Reutilizar credenciais Groq/Telegram de `../signalhub/.env` (mesmo bot @tiago_a_rocha_alertas_bot).

---

## REGRAS ABSOLUTAS

1. **Nunca** `financial_capacity` no prompt Groq
2. **Nunca** `final_score` vindo do Groq — só `computeFinalScore()` em `score.ts`
3. **Nunca** "Ltda", "plataforma de IA" ou "SaaS" no site ou NF
4. **Sempre** CNPJ + titular MEI no rodapé
5. Campo **nome_ou_razao** — PF (Lex/dorking) e PJ
6. `import 'groq-sdk/shims/web'` antes do Groq
7. `<form onSubmit>` — acessibilidade e Enter para enviar
8. Telegram **sem** parse_mode Markdown (texto plano)
9. Honeypot `website` anti-spam
10. `robots: noindex` até validar conversão
11. Descrição NF tipo: *Qualificação de demandas comerciais* (7319) ou *Apoio administrativo* (8219)

---

## MÉTRICAS — SEMANA 1

| Métrica | Meta | Decisão |
|---------|------|---------|
| Leads landing | ≥ 10 | Demanda inbound? |
| Alertas SignalHub úteis | ≥ 5 | Dorking funciona? |
| `final_score` ≥ 70 | ≥ 3 | Qualidade inbound? |
| Concordância com score | ≥ 60% | Ajustar prompt? |
| Nicho dominante | lexrocha vs zairyx | Foco comercial |
| 1ª venda Lex Rocha | ≥ 1 | Monetização 8219? |

---

## COMANDO PARA O CURSOR

```
Leia CURSOR_PROMPT_VORTEXIA.md inteiro.
Crie vortexia-web/ ao lado de signalhub/ com Next.js 15, Tailwind, TypeScript strict.
Implemente na ordem: package.json → lib/score.ts → lib/groq.ts → lib/supabase.ts
→ app/api/qualify/route.ts → app/page.tsx → app/layout.tsx → globals.css
→ supabase/migration.sql → .env.local.example
Identidade: marca Vortexia, rodapé MEI Tiago Aureliano da Rocha CNPJ 61.699.939/0001-80.
Não criar dashboard, auth, Stripe ou páginas extras.
```

---

## O QUE NÃO FAZER AGORA

- Dashboard, Stripe, white-label, multiusuário
- Migrar SignalHub para dentro do Next.js
- Vender Zairyx como licença de software no MEI
- Indexar no Google antes de 30 dias de validação
