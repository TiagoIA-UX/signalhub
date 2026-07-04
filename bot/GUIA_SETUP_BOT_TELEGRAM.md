# Guia — Criar o bot Telegram do SignalHub

Tempo estimado: **15–20 minutos** (celular + PC).

---

## Parte 1 — Criar o bot no Telegram (celular ou desktop)

### Passo 1: Abrir o BotFather

1. Abra o **Telegram**
2. Na busca, digite: `@BotFather`
3. Entre no chat oficial (badge verificado ✓)
4. Toque em **Iniciar** ou envie `/start`

### Passo 2: Criar bot novo

1. Envie o comando:
   ```
   /newbot
   ```
2. BotFather pergunta o **nome de exibição** (pode ser qualquer nome):
   ```
   SignalHub Alertas
   ```
3. BotFather pede o **username** (tem que terminar em `bot`, sem espaços):
   ```
   signalhub_lex_zairyx_bot
   ```
   Se estiver ocupado, tente: `signalhub_tiago_bot`, `lex_zairyx_alerts_bot`, etc.

4. BotFather responde com algo assim:
   ```
   Done! ... Use this token to access the HTTP API:
   7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

5. **Copie o token inteiro** e cole em `CONFIGURACAO_PREENCHER.env`:
   ```
   TELEGRAM_BOT_TOKEN=7123456789:AAHxxxxxxxx...
   ```

> Guarde o token em local seguro. Quem tiver o token controla o bot.

### Passo 3: Configurações opcionais (recomendado)

No chat do @BotFather:

```
/setdescription
```
Selecione seu bot → cole:
```
Alertas de oportunidades Lex Rocha (CDC) e Zairyx (delivery). Uso privado.
```

```
/setcommands
```
Selecione seu bot → cole:
```
start - Ativar alertas
status - Verificar se o bot está ok
```

---

## Parte 2 — Obter seu CHAT_ID (número do seu chat privado)

O SignalHub envia alertas **para você**, não para grupos (na v1).

### Método A — Script automático (PC, mais fácil)

1. Preencha só o `TELEGRAM_BOT_TOKEN` no `.env` (chat_id pode ficar vazio por enquanto)
2. No Telegram, busque seu bot pelo username e envie:
   ```
   /start
   ```
3. No PC, na pasta `signalhub`:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   python scripts/obter_chat_id.py
   ```
4. O script imprime:
   ```
   TELEGRAM_CHAT_ID=987654321
   ```
5. Copie esse número para o `.env`

### Método B — @userinfobot (celular, manual)

1. No Telegram, busque: `@userinfobot`
2. Envie `/start`
3. Ele responde com seu **Id:** `987654321`
4. Cole em:
   ```
   TELEGRAM_CHAT_ID=987654321
   ```

---

## Parte 3 — Conta Groq (IA)

1. Acesse: https://console.groq.com
2. Crie conta (Google ou e-mail)
3. Menu **API Keys** → **Create API Key**
4. Copie a key (começa com `gsk_`)
5. Cole em:
   ```
   GROQ_API_KEY=gsk_...
   ```

---

## Parte 4 — Montar o arquivo .env no PC

1. Abra a pasta:
   ```
   e:\.projetos\000Inteligência_Resolutiva\signalhub\
   ```

2. Copie o template:
   ```powershell
   copy CONFIGURACAO_PREENCHER.env .env
   ```

3. Abra `.env` no Cursor e preencha os 3 campos obrigatórios:
   - `GROQ_API_KEY`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`

4. Salve o arquivo

**Exemplo preenchido (fictício):**
```env
GROQ_API_KEY=gsk_abc123def456
GROQ_MODEL=openai/gpt-oss-120b
TELEGRAM_BOT_TOKEN=7123456789:AAHxxxxxxxxxxxxxxxx
TELEGRAM_CHAT_ID=123456789
LEXROCHA_BASE_URL=https://lexrocha.com.br
ZAIRYX_BASE_URL=https://www.zairyx.com.br
POLL_INTERVAL_MINUTES=5
MIN_SCORE=7
MAX_ALERTS_PER_DAY=30
DEDUP_DB_PATH=data/seen.sqlite
```

---

## Parte 5 — Validar (3 testes em ordem)

### Teste 1 — Sistema sem API externa
```powershell
cd "e:\.projetos\000Inteligência_Resolutiva\signalhub"
.\.venv\Scripts\Activate.ps1
python run_once.py --mock --dry-run --sample
```
Esperado: alerta formatado no terminal com `tenant: lexrocha`

### Teste 2 — Telegram funcionando
```powershell
python scripts/testar_telegram.py
```
Esperado: mensagem **"SignalHub OK"** no seu Telegram

### Teste 3 — Ciclo real (Reddit + Groq + Telegram)
```powershell
python run_once.py
```
Esperado: 0 a alguns alertas no Telegram (depende do que está no Reddit agora)

---

## Parte 6 — Rodar 24/7

```powershell
python -m src.scheduler
```

O sistema consulta Reddit a cada **5 minutos** e manda alerta quando encontrar intenção real (score ≥ 7).

Para parar: `Ctrl + C`

---

## Solução de problemas

| Problema | Causa | Solução |
|----------|-------|---------|
| `Unauthorized` Telegram | Token errado | Recopie token do @BotFather |
| Bot não envia mensagem | Chat ID errado | Rode `obter_chat_id.py` de novo após `/start` |
| `GROQ_API_KEY obrigatório` | .env vazio ou nome errado | Arquivo deve ser `.env` na pasta signalhub |
| Nenhum alerta no ciclo real | Reddit sem posts relevantes | Normal — aguarde ou rode `--sample` |
| `403 Reddit` | Rate limit | Aguarde 5 min; User-Agent já configurado |

---

## Segurança

- Não compartilhe `TELEGRAM_BOT_TOKEN` nem `GROQ_API_KEY`
- Não suba `.env` para GitHub
- O bot **só envia** alertas — **nunca** posta automaticamente em Reddit

---

## Resumo em 6 linhas

```
1. @BotFather → /newbot → copiar TELEGRAM_BOT_TOKEN
2. Enviar /start ao seu bot no Telegram
3. python scripts/obter_chat_id.py → copiar TELEGRAM_CHAT_ID
4. console.groq.com → copiar GROQ_API_KEY
5. Salvar tudo em .env
6. python scripts/testar_telegram.py → python run_once.py
```
