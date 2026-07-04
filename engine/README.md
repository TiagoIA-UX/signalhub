# SignalHub Engine (v2)

Motor multi-tenant de detecção e alertas.

| Tenant | Pasta | Papel |
|--------|-------|--------|
| `zairyx/` | bot local neste repo | Delivery / alertas do hub (credenciais do `.env` mestre) |
| `lex/` | shim | Aponta para `09-lex-rocha-brasil/signalhub-br` |
| `portugal/` | shim | Aponta para `08-lex-rocha-portugal/signalhub/portugal` |
| `usa/` | shim | Aponta para `04-judicial-intelligence/signalhub/usa` |

Credenciais: edite `../.env` e rode `../scripts/sincronizar-env.ps1`.

```powershell
cd engine
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python zairyx/bot.py detectar
```
