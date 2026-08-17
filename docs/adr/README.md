# Registros de Decisões de Arquitetura (ADRs)

Este diretório contém os Architecture Decision Records (ADRs) do projeto Traffic Analyzer.

Os ADRs registram decisões técnicas relevantes que afetam a arquitetura, operação ou evolução futura da aplicação.

O objetivo não é documentar cada detalhe da implementação, mas preservar o contexto das decisões que, no futuro, poderiam precisar ser redescobertas por outra pessoa.

## Estrutura

Cada ADR utiliza uma estrutura simples:

- **Status** — estado atual da decisão.
- **Contexto** — problema, requisito ou restrição que motivou a decisão.
- **Decisão** — o que foi decidido e por quê.
- **Consequências** — benefícios, limitações e trade-offs introduzidos.

## Status possíveis

- `Aceito`
- `Substituído`
- `Descontinuado`

Quando uma decisão arquitetural mudar, o ADR original deve preferencialmente permanecer no repositório, referenciando a decisão que o substituiu.

Isso preserva o histórico e evita perda de contexto.

## Decisões atuais

| ADR | Decisão | Status |
|---|---|---|
| [0001](0001-use-python-and-scapy.md) | Utilizar Python e Scapy para captura de pacotes | Aceito |
| [0002](0002-use-sqlite.md) | Utilizar SQLite para persistência | Aceito |
| [0003](0003-rank-traffic-by-bytes.md) | Classificar tráfego pelo volume em bytes | Aceito |
| [0004](0004-support-ipv4-and-ipv6.md) | Suportar IPv4 e IPv6 | Aceito |
| [0005](0005-use-host-networking.md) | Utilizar host networking no Docker | Aceito |
| [0006](0006-isolate-current-capture.md) | Isolar a captura atual do histórico | Aceito |

## Princípio de decisão

As decisões deste projeto seguem uma lógica simples:

```text
Entender o requisito
        ↓
Escolher a solução mais simples que o atende
        ↓
Identificar os trade-offs
        ↓
Validar
        ↓
Documentar
        ↓
Revisitar quando as premissas mudarem
```

A arquitetura deve evoluir quando requisitos ou evidências mudarem, e não apenas porque existe uma tecnologia mais sofisticada disponível.
