# SignalHub Engine

Motor do robô inteligente (multi-contexto).

| Contexto | Pasta | Papel |
|----------|-------|--------|
| `zairyx/` | bot local neste repo | Operação padrão do hub (credenciais do `.env` mestre) |
| `lex/` | ponte | Produto Brasil (`09-lex-rocha-brasil`) |
| `portugal/` | ponte | Produto Portugal (`08-lex-rocha-portugal`) |
| `usa/` | ponte | Produto EUA (`04-judicial-intelligence`) |

Credenciais: edite `../.env` e rode `../scripts/sincronizar-env.ps1`.

```powershell
cd engine
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python zairyx/bot.py
```
