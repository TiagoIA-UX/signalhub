# SignalHub

**Robô inteligente de captação em dados públicos · Alertas no Telegram · Qualificação assistida**

[![License: Business](https://img.shields.io/badge/license-Business-blue.svg)](./LICENSE)
[![Compliance](https://img.shields.io/badge/compliance-dados--publicos-green.svg)](./COMPLIANCE.md)
[![Status](https://img.shields.io/badge/status-commercial-orange.svg)](./PLANOS_E_PRECOS.md)

> Software **proprietário** com **Business License**.  
> Não é open source. Uso em produção exige assinatura comercial.

**Titular:** Tiago Aureliano da Rocha · CNPJ 61.699.939/0001-80 (Lex Rocha)

---

## O que é

O SignalHub é um **robô inteligente** que ajuda a **captar interesse de pessoas na internet** a partir de **informações públicas** — publicações e discussões abertas em que alguém já expressou uma necessidade.

Ele:

1. **Observa** fontes públicas (conforme configuração do operador)  
2. **Classifica** o sinal com IA (relevância / urgência)  
3. **Alerta** o operador no Telegram  
4. **Opcionalmente** registra e qualifica o contato no painel web  

**Sempre com humano no loop:** o software **não** envia mensagens sozinho a desconhecidos. Quem decide contatar — e como — é a pessoa responsável pela operação.

Não é advocacia, não emite parecer jurídico e não substitui profissional habilitado.

---

## Módulos

| Módulo | Função |
|--------|--------|
| **Bot** | Monitoramento de fontes públicas, classificação e alerta no Telegram |
| **Engine** | Motor multi-contexto (regras, palavras-chave, varredura configurável) |
| **Web** | Qualificação assistida de contatos (IA + banco + notificação) |

---

## Licença Business

| | |
|--|--|
| **Modelo** | Assinatura comercial (`LICENSE`) |
| **Avaliação** | Leitura do código + demonstração local (prazo na licença) |
| **Produção** | Somente com plano ativo (`PLANOS_E_PRECOS.md`) |
| **Uso ético** | `COMPLIANCE.md` |

---

## Uso responsável (resumo)

- Apenas **dados públicos** e acessíveis sem autenticação indevida  
- **Revisão humana** antes de qualquer contato  
- Respeito à **LGPD**, ao Marco Civil e aos termos das plataformas  
- Sem promessa de resultado comercial ou jurídico  

Detalhes: [COMPLIANCE.md](./COMPLIANCE.md)

---

## Stack

Python (bot e motor) · Next.js (web) · IA (classificação) · Telegram (alertas) · Supabase (persistência do web)

```powershell
copy .env.example .env
.\INICIAR.ps1 -Instalar
.\INICIAR.ps1
```

Credenciais mestras na raiz (`.env`); sincronização: `scripts/sincronizar-env.ps1`.

Regras operacionais do robô (palavras-chave, varredura, prompts) **não ficam no Git** — só no cofre local da máquina (`E:\01_Projetos\_cofre`). No repositório há apenas `*.example`.

---

## Ecossistema

| Produto | Repositório |
|---------|-------------|
| SignalHub | este repositório |
| Lex Rocha Brasil | [lex-rocha-brasil](https://github.com/TiagoIA-UX/lex-rocha-brasil) |
| Lex Rocha Portugal | [lex-rocha-portugal](https://github.com/TiagoIA-UX/lex-rocha-portugal) |
| Judicial Intelligence (EUA) | [judicial-intelligence](https://github.com/TiagoIA-UX/judicial-intelligence) |

---

## Comercial

- [PLANOS_E_PRECOS.md](./PLANOS_E_PRECOS.md)  
- [LICENSE](./LICENSE)  
- [COMPLIANCE.md](./COMPLIANCE.md)

**© 2026 Tiago Aureliano da Rocha — SignalHub, licença business.**  
Todos os direitos reservados.
