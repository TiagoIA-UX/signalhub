# SignalHub — Detecção de Intenção + Alertas Telegram

Monitora Reddit (BR), filtra por keywords CDC/delivery, classifica via Groq, envia alerta no Telegram para **aprovação manual**.

## Setup (30 min)

```powershell
cd signalhub
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# Preencha GROQ_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
```

## Testes por camada

```powershell
# Todos os testes (mock — sem API externa)
pytest -v

# Camada 1 — config + dedup + keywords
pytest tests/test_layer1_config_dedup_prefilter.py -v

# Camada 2 — classifier
pytest tests/test_layer2_classifier.py -v

# Camada 3 — responder + telegram format
pytest tests/test_layer3_responder_telegram.py -v

# Camada 4 — reddit + pipeline
pytest tests/test_layer4_reddit_pipeline.py -v
```

## Teste manual (post simulado)

```powershell
python run_once.py --mock --dry-run --sample
```

## Ciclo real (Reddit + Groq + Telegram)

```powershell
python run_once.py
```

## Rodar 24/7 (poll 5 min)

```powershell
python -m src.scheduler
```

## Rodar 24/7 com PM2 (restart automático)

```powershell
npm install -g pm2
pm2 start ecosystem.config.js
pm2 save
pm2 startup   # opcional — inicia com o Windows
pm2 logs signalhub
```

## Tenants

| Tenant | Produto | URL |
|--------|---------|-----|
| lexrocha | Pesquisa documental CDC | lexrocha.com.br |
| zairyx | Cardápio digital delivery | zairyx.com.br |

## Regras

- **Nunca** auto-posta — operador copia e cola manualmente (botões R1/R2/R3 enviam resposta pronta no Telegram)
- Score mínimo: 7/10
- Máx. 30 alertas/dia
- PII removido antes do Groq
