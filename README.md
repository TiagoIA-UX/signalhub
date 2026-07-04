# SignalHub

Plataforma de **detecção de intenção + alertas Telegram + qualificação de leads**.

| Campo | Valor |
|-------|--------|
| **Pasta local** | `E:\01_Projetos\06-signalhub` |
| **GitHub** | [TiagoIA-UX/signalhub](https://github.com/TiagoIA-UX/signalhub) |
| **Titular** | Tiago Aureliano da Rocha · CNPJ 61.699.939/0001-80 |

## O que é este monorepo

Antes havia três pastas soltas dentro do template Lex Rocha. Elas usavam o **mesmo bot Telegram** e a **mesma chave Groq** — eram o mesmo stack operacional. Agora estão unificadas aqui:

| Pasta | Origem | Função |
|-------|--------|--------|
| `bot/` | antigo `signalhub/` | Bot Python legado — Reddit, classificação Groq, alertas Telegram |
| `engine/` | antigo `signalhub_v2/` | Motor v2 (multi-tenant, dorks, scan) |
| `web/` | antigo `vortexia-web/` | App Next.js — qualificação de leads (Groq + Supabase + Telegram) |

Produtos Lex Rocha (Brasil, Portugal, EUA) têm **bots próprios** nos repositórios de produto. Este repo é o **hub central** (alertas multi-nicho + qualify).

## Credenciais (um único `.env`)

Todas as chaves ficam na **raiz**:

```powershell
copy .env.example .env
# edite .env
.\scripts\sincronizar-env.ps1
```

O script propaga para:

- `bot/.env`
- `web/.env.local`
- `engine/zairyx/.env`

| Grupo | Chaves | Fonte consolidada |
|-------|--------|-------------------|
| Groq | `GROQ_API_KEY`, `GROQ_MODEL` | Uma chave (bot + web iguais) |
| Telegram | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | Um bot (`@tiago_a_rocha_alertas_bot`) |
| Supabase | `SUPABASE_*`, `NEXT_PUBLIC_*` | Projeto do web (qualify) |
| Ops | URLs Lex/Zairyx, poll, limites | Bot legado |

**Não commite** o `.env` (está no `.gitignore`).

## Arranque

```powershell
cd E:\01_Projetos\06-signalhub

# Primeira vez
.\INICIAR.ps1 -Instalar

# Menu
.\INICIAR.ps1

# Direto
.\INICIAR.ps1 -Modo sync
.\INICIAR.ps1 -Modo bot
.\INICIAR.ps1 -Modo web
.\INICIAR.ps1 -Modo engine
```

## Família Lex Rocha (produtos separados)

| Produto | Pasta | GitHub |
|---------|-------|--------|
| EUA | `04-judicial-intelligence` | `judicial-intelligence` |
| **SignalHub** | `06-signalhub` | `signalhub` |
| Template legal tech | `07-lex-rocha-template` | `lex-rocha-template` |
| Portugal | `08-lex-rocha-portugal` | `lex-rocha-portugal` |
| Brasil | `09-lex-rocha-brasil` | `lex-rocha-brasil` |

## Licença

Software proprietário.
