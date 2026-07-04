# SignalHub — Bot

Módulo de monitoramento de **fontes públicas**, classificação com IA e **alerta no Telegram** para aprovação manual.

## Setup

```powershell
# Preferivel: pela raiz do monorepo
cd ..
.\scripts\sincronizar-env.ps1
.\INICIAR.ps1 -Modo bot
```

Ou isolado:

```powershell
cd bot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# credenciais via raiz: ..\.env (sincronizar-env.ps1)
python run_once.py
```

## Testes por camada

```powershell
pytest -v
```

## Ciclo

```powershell
python run_once.py --mock --dry-run --sample
python run_once.py
python -m src.scheduler
```

Uso responsável: ver `../COMPLIANCE.md`. Licença: `../LICENSE`.
