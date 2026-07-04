# DEPLOY CHECKLIST — Vortexia Web
# Execute na ordem. Não pule etapas.

---

## ⚠️ DOIS PROBLEMAS CRÍTICOS ANTES DE SUBIR

---

### PROBLEMA 1 — Chaves Supabase depreciadas (quebra silenciosa em 2026)

O Supabase está migrando para novo formato de chaves.
Se você criar o projeto agora, as chaves que aparecem no dashboard são:

  NOVO (correto):
    Publishable key → sb_publishable_xxx   (substitui anon key)
    Secret key      → sb_secret_xxx        (substitui service_role key)

  LEGADO (ainda funciona, mas será desativado até fim de 2026):
    service_role key → eyJ...

AÇÃO OBRIGATÓRIA:
  No Supabase Dashboard → Settings → API Keys
  Use a aba "API Keys" (não "Legacy API Keys")
  Copie a "Secret key" (sb_secret_xxx) para SUPABASE_SERVICE_ROLE_KEY

Se o projeto for antigo e só mostrar chaves legacy, use normalmente —
mas anote para migrar quando o Supabase avisar.

---

### PROBLEMA 2 — Variáveis de ambiente sumindo no Vercel (Next.js 15)

Há um bug documentado: variáveis server-side somem em Route Handlers
se não forem marcadas corretamente no painel da Vercel.

CAUSA: ao adicionar variáveis no painel Vercel, você precisa marcar
explicitamente em quais ambientes elas valem:
  ✅ Production
  ✅ Preview
  ✅ Development

Se marcar só "Production", o build de preview quebra silenciosamente.

SOLUÇÃO: ao cadastrar cada variável no painel Vercel, marque os 3 ambientes.

---

## PASSO A PASSO COMPLETO (ordem exata)

---

### ETAPA 1 — Supabase (fazer ANTES do deploy)

1.1 Criar projeto Supabase
    → https://supabase.com/dashboard
    → New project
    → Nome: vortexia-prod
    → Região: South America (São Paulo) — menor latência BR
    → Anote a senha do banco

1.2 Rodar a migration
    → SQL Editor (menu lateral)
    → New query
    → Colar conteúdo de supabase/migration.sql
    → RUN
    → Verificar: Table Editor → tabela "leads" deve aparecer

1.3 Copiar as chaves
    → Settings → API Keys
    → Copiar "Project URL"          → SUPABASE_URL
    → Copiar "Secret key" (sb_secret_xxx OU service_role legacy)
                                    → SUPABASE_SERVICE_ROLE_KEY

1.4 Testar anti-pausa (free tier pausa após 7 dias sem acesso)
    → GitHub Action em .github/workflows/supabase-ping.yml (já incluída no repo)

---

### ETAPA 2 — .env.local (testar local ANTES do Vercel)

Preencher o arquivo vortexia-web/.env.local:

```
GROQ_API_KEY=gsk_...               ← copiar do signalhub/.env
TELEGRAM_BOT_TOKEN=...             ← copiar do signalhub/.env
TELEGRAM_CHAT_ID=...               ← copiar do signalhub/.env
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=sb_secret_xxx (ou eyJ... se legacy)
NEXT_PUBLIC_SITE_URL=http://localhost:3000
```

NUNCA commitar esse arquivo. Confirmar que está no .gitignore.

---

### ETAPA 3 — Teste local completo

```powershell
cd E:\.projetos\000Inteligência_Resolutiva\vortexia-web
npm run dev
```

Abrir http://localhost:3000
Preencher formulário com dados reais (não "teste"):
  - Nome: Empresa Exemplo Ltda
  - Email: seuemail@real.com
  - Mensagem: descrever um problema real de consumidor

Verificar:
  ✅ Página carregou sem erro de hidratação
  ✅ Botão "Enviando..." aparece durante request
  ✅ Mensagem de sucesso aparece após envio
  ✅ Alerta chegou no Telegram com score e resumo
  ✅ Lead apareceu na tabela Supabase (Table Editor → leads)

Se algum falhar → corrigir antes de fazer deploy.

---

### ETAPA 4 — Preparar repositório Git

```powershell
cd E:\.projetos\000Inteligência_Resolutiva\vortexia-web

# Confirmar .gitignore protege o .env
cat .gitignore | findstr env

# Deve mostrar: .env.local (ou .env*)
# Se não mostrar, adicionar manualmente

git init
git add .
git commit -m "feat: vortexia-web MVP inicial"
```

Criar repositório PRIVADO no GitHub:
→ https://github.com/new
→ Nome: vortexia-web
→ Privado (obrigatório — contém estrutura do projeto)
→ NÃO inicializar com README

```powershell
git remote add origin https://github.com/SEU_USUARIO/vortexia-web.git
git push -u origin main
```

---

### ETAPA 5 — Deploy Vercel

OPÇÃO A — via CLI (mais rápido):
```powershell
npx vercel
```
Seguir prompts:
  → Link to existing project? N
  → Project name: vortexia-web
  → Directory: ./
  → Override settings? N

OPÇÃO B — via painel (mais seguro para variáveis):
→ https://vercel.com/new
→ Import Git Repository → vortexia-web
→ Framework: Next.js (detectado automaticamente)
→ Root Directory: ./
→ NÃO deploy ainda — ir para Environment Variables primeiro

---

### ETAPA 6 — Variáveis no painel Vercel (CRÍTICO)

→ Vercel Dashboard → projeto vortexia-web → Settings → Environment Variables
→ Adicionar CADA variável abaixo, marcando os 3 ambientes:
   ✅ Production  ✅ Preview  ✅ Development

Variáveis a adicionar:
  GROQ_API_KEY
  TELEGRAM_BOT_TOKEN
  TELEGRAM_CHAT_ID
  SUPABASE_URL
  SUPABASE_SERVICE_ROLE_KEY
  NEXT_PUBLIC_SITE_URL        → https://vortexiatiagoarocha-team-zairyx.vercel.app

→ Após adicionar todas → Deployments → Redeploy (obrigatório após adicionar vars)

---

### ETAPA 7 — Verificar deploy em produção

Abrir https://vortexiatiagoarocha-team-zairyx.vercel.app
Repetir teste do formulário com dado real
Verificar Telegram + Supabase

Se der erro 500 no /api/qualify:
  → Vercel Dashboard → projeto → Functions → qualify → Logs
  → Procurar qual variável está undefined

---

### ETAPA 8 — Anti-pausa Supabase (free tier)

Arquivo: `.github/workflows/supabase-ping.yml` (incluído no repositório)

→ GitHub → repositório vortexia-web → Settings → Secrets → Actions
→ Adicionar:
    SUPABASE_URL         (mesma do .env)
    SUPABASE_ANON_KEY    (publishable/anon key — NÃO a secret/service role)

---

## ERROS COMUNS E SOLUÇÕES RÁPIDAS

| Erro | Causa | Solução |
|------|-------|---------|
| `SUPABASE_SERVICE_ROLE_KEY is not defined` | Variável não marcada em Production | Vercel → Settings → Env Vars → marcar 3 ambientes → Redeploy |
| `relation "leads" does not exist` | Migration não rodou | Supabase SQL Editor → rodar migration.sql |
| `Error: Groq API key not found` | GROQ_API_KEY vazia | Verificar .env.local local / Vercel env vars |
| Telegram não recebe alerta | CHAT_ID errado | `python ../signalhub/scripts/obter_chat_id.py` |
| Score sempre 50/50/50 | Fallback do Groq ativando | Ver logs Vercel Functions → Groq retornando erro |
| Build falha com `Module not found` | Dependência faltando | `npm install` → `npm run build` local |
| Formulário trava em "Enviando..." | Route Handler com erro silencioso | DevTools → Network → resposta do POST /api/qualify |

---

## DEPOIS DO DEPLOY — próximos passos

Semana 1:
  → Compartilhar URL no WhatsApp, grupos relevantes, Reddit
  → Meta: 10 submissões reais
  → Acompanhar leads no Supabase Table Editor

Quando chegar primeiro lead com final_score >= 70:
  → Responder manualmente em até 2h (janela de ouro)
  → Registrar resultado em leads.status ('contatado' → 'convertido')
  → Lembrete: Vercel Pro ($20) + Supabase Pro ($25) quando monetizar

SignalHub outbound:
  → Rodar em paralelo: `pm2 start ../signalhub/ecosystem.config.js`
  → Os dois sistemas alimentam o mesmo Telegram — inbound + outbound

---

## RESUMO EM 5 MINUTOS

1. Supabase → criar projeto → rodar migration.sql → copiar chaves
2. .env.local → preencher → testar local → formulário → checar Telegram
3. GitHub → repo privado → push
4. Vercel → importar → adicionar variáveis (3 ambientes) → deploy
5. Testar URL pública → lead real → Supabase + Telegram confirmam
