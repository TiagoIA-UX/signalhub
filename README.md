# SignalHub

**Detecção assistida de intenção · Alertas no Telegram · Qualificação de leads**

[![License: Business](https://img.shields.io/badge/license-Business-blue.svg)](./LICENSE)
[![Compliance](https://img.shields.io/badge/compliance-human--in--the--loop-green.svg)](./COMPLIANCE.md)
[![Status](https://img.shields.io/badge/status-commercial-orange.svg)](./PLANOS_E_PRECOS.md)

> Software **proprietário** com **Business License**.  
> Código pode ser público para transparência técnica — **uso em produção exige assinatura**.  
> Não é open source.

**Titular:** Tiago Aureliano da Rocha · CNPJ 61.699.939/0001-80 (Lex Rocha)

---

## Por que existe

Equipes comerciais e legal techs perdem tempo vasculhando redes e fóruns à mão. O SignalHub **monitora sinais públicos**, classifica intenção com IA e **alerta no Telegram** para um humano decidir o próximo passo — com opcional **qualificação estruturada** de leads.

Ideal para quem vende:

- serviços de direitos do consumidor / legal tech  
- soluções para delivery e operações locais  
- prospecção ética baseada em **demanda expressa**, não em spam

---

## O que entrega

| Módulo | Função |
|--------|--------|
| **Bot** | Monitoramento (ex.: Reddit), filtros, score, alerta Telegram |
| **Engine** | Motor multi-tenant (dorks, keywords, scan) |
| **Web** | Qualificação de leads (IA + banco + notificação) |

**Humano no loop:** nada de disparo automático de mensagem a desconhecidos. O operador aprova.

---

## Licença Business (ético e transparente)

| | |
|--|--|
| **Modelo** | Assinatura comercial (`LICENSE`) |
| **Avaliação** | Leitura do código + demo local até 14 dias |
| **Produção** | Somente com plano ativo (`PLANOS_E_PRECOS.md`) |
| **Compliance** | Regras de uso ético em `COMPLIANCE.md` |

É **eticamente correto** cobrar por software proprietário quando:

1. a licença deixa claro que **não é open source**;  
2. o marketing **não promete** resultado jurídico nem volume garantido de clientes;  
3. a operação exige **revisão humana** e respeito à LGPD e às plataformas.

É **incorreto** (e proibido pela licença) fingir que o código público é “grátis para uso comercial”.

---

## Stack

- Python (bot + engine)  
- Next.js (web de qualificação)  
- Groq (classificação / qualify)  
- Telegram (alertas)  
- Supabase (persistência do web)

Credenciais: um único `.env` na raiz → `scripts/sincronizar-env.ps1`.

```powershell
copy .env.example .env
# preencha as chaves
.\INICIAR.ps1 -Instalar
.\INICIAR.ps1
```

---

## Produtos irmãos (legal tech)

O SignalHub é a **plataforma de sinais**. Os sites de produto vivem em repositórios separados:

| Mercado | Repositório |
|---------|-------------|
| Brasil | [lex-rocha-brasil](https://github.com/TiagoIA-UX/lex-rocha-brasil) |
| Portugal | [lex-rocha-portugal](https://github.com/TiagoIA-UX/lex-rocha-portugal) |
| EUA | [judicial-intelligence](https://github.com/TiagoIA-UX/judicial-intelligence) |
| Template | [lex-rocha-template](https://github.com/TiagoIA-UX/lex-rocha-template) |

---

## Comercial

- Planos: [PLANOS_E_PRECOS.md](./PLANOS_E_PRECOS.md)  
- Licença: [LICENSE](./LICENSE)  
- Compliance: [COMPLIANCE.md](./COMPLIANCE.md)

**© 2026 Tiago Aureliano da Rocha — SignalHub, licença business.**  
Todos os direitos reservados.
