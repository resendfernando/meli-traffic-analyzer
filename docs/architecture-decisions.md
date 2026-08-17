# Decisões de Arquitetura

## Visão geral

Este documento apresenta uma visão rápida das principais decisões arquiteturais do Traffic Analyzer.

O objetivo é permitir que um avaliador ou novo integrante do projeto compreenda em poucos minutos:

- quais decisões foram tomadas;
- por que foram tomadas;
- quais limitações foram conscientemente aceitas;
- quando essas decisões deveriam ser revistas.

O detalhamento de contexto, alternativas e consequências está disponível nos [Architecture Decision Records (ADRs)](adr/README.md).

---

## Decisões principais

| Decisão | Escolha | Motivo principal |
|---|---|---|
| Linguagem | Python | Simplicidade, legibilidade e ecossistema |
| Captura | Scapy | Abstração adequada para captura e parsing |
| Modelo interno | `PacketRecord` | Desacoplar captura das demais camadas |
| Persistência | SQLite | Persistência real sem infraestrutura adicional |
| Ranking de tráfego | Volume em bytes | Representar efetivamente o tráfego movimentado |
| Protocolos IP | IPv4 + IPv6 | Cobrir o tráfego observado em redes modernas |
| Containerização | Docker | Execução reproduzível |
| Networking | Host network | Acesso à interface física do host Linux |
| Privilégios | `NET_RAW` + `NET_ADMIN` | Evitar container totalmente privilegiado |
| Escopo do relatório | Captura atual isolada | Não misturar histórico com a execução corrente |

---

## Como a solução foi pensada

A arquitetura segue um princípio simples:

```text
Requisito
   ↓
Solução mínima suficiente
   ↓
Separação de responsabilidades
   ↓
Teste
   ↓
Documentação
   ↓
Evolução baseada em necessidade
```

O objetivo não foi construir a arquitetura mais sofisticada possível.

Foi construir a solução mais simples capaz de atender corretamente ao problema, mantendo limites e caminhos de evolução explícitos.

---

## 1. Python + Scapy

**Decisão:** utilizar Python com Scapy para captura e interpretação dos pacotes.

**Por quê:** permite trabalhar com protocolos de rede utilizando abstrações maduras sem implementar parsing em baixo nível.

**Limite aceito:** cenários de throughput muito elevado podem exigir outra estratégia de captura.

**Detalhes:** [ADR 0001](adr/0001-use-python-and-scapy.md)

---

## 2. Normalização antes da persistência

Os objetos recebidos do Scapy não são propagados diretamente pela aplicação.

Eles são transformados em:

```text
PacketRecord
├── source_ip
├── destination_ip
├── protocol
└── packet_size
```

Isso estabelece uma fronteira clara:

```text
Scapy
   ↓
Normalization
   ↓
Application Domain
   ↓
Persistence / Analysis
```

A consequência é menor acoplamento e maior facilidade para testar ou substituir componentes.

---

## 3. SQLite

**Decisão:** utilizar SQLite como banco de dados.

**Por quê:** o cenário possui um único coletor e não apresenta requisito de ingestão distribuída ou alta concorrência.

SQLite fornece persistência com praticamente zero overhead operacional.

**Limite aceito:** não é a escolha final para ingestão concorrente e contínua em grande escala.

**Detalhes:** [ADR 0002](adr/0002-use-sqlite.md)

---

## 4. Tráfego medido por volume

O requisito solicita os IPs com "mais tráfego".

A implementação considera como métrica principal:

```text
SUM(packet_size)
```

em vez de apenas:

```text
COUNT(packets)
```

Exemplo:

```text
IP A → 100 pacotes → 10 KiB
IP B →  20 pacotes → 80 KiB
```

Nesse cenário, o IP B movimentou mais tráfego.

A quantidade de pacotes também é apresentada para preservar contexto.

**Detalhes:** [ADR 0003](adr/0003-rank-traffic-by-bytes.md)

---

## 5. IPv4 + IPv6

**Decisão:** tratar ambos desde a normalização.

**Por quê:** limitar a aplicação a IPv4 produziria uma visão incompleta em uma rede dual-stack.

Os dois formatos utilizam o mesmo modelo de dados.

**Detalhes:** [ADR 0004](adr/0004-support-ipv4-and-ipv6.md)

---

## 6. Docker com acesso à rede do host

A aplicação precisa executar em Docker e capturar tráfego de uma interface física do host.

Para o ambiente Linux utilizado no desafio:

```yaml
network_mode: host
```

As capabilities necessárias são concedidas explicitamente:

```yaml
NET_RAW
NET_ADMIN
```

Essa abordagem foi escolhida em vez de utilizar um container completamente privilegiado.

**Limite aceito:** host networking reduz o isolamento de rede e deve ser reavaliado em um cenário produtivo.

**Detalhes:** [ADR 0005](adr/0005-use-host-networking.md)

---

## 7. Captura atual separada do histórico

O banco persiste entre execuções.

Portanto:

```text
Historical Data
      +
Current Capture
```

não devem ser automaticamente tratados como o mesmo conjunto analítico.

Antes da captura é registrada a fronteira existente no banco e o resumo final considera somente os novos registros.

Isso permite manter simultaneamente:

```text
Current Capture Summary
        ↓
resultado desta execução

Historical Report
        ↓
histórico completo
```

**Detalhes:** [ADR 0006](adr/0006-isolate-current-capture.md)

---

## 8. Simplicidade deliberada

Algumas tecnologias poderiam ter sido adicionadas:

```text
PostgreSQL
Redis
Kafka
API
Dashboard
Kubernetes
Distributed Workers
```

Elas não foram utilizadas porque não existe requisito atual que justifique seu custo operacional.

A ausência desses componentes não representa desconhecimento de alternativas, mas uma decisão arquitetural.

A evolução deve ocorrer quando houver evidência de necessidade.

---

## 9. O que faria uma decisão mudar?

As decisões não são permanentes.

Exemplos:

```text
Maior throughput
      ↓
reavaliar persistência e batching

Múltiplos coletores
      ↓
reavaliar SQLite e identificação de captura

Operação 24x7
      ↓
adicionar observabilidade e retenção

Requisitos de disponibilidade
      ↓
definir SLO / RTO / RPO e então avaliar HA

Maior exigência de segurança
      ↓
reavaliar networking e capabilities
```

Os ADRs preservam o contexto original para que essas mudanças possam ser feitas conscientemente.

---

## 10. Princípio arquitetural

A abordagem utilizada pode ser resumida como:

```text
Não otimizar antes de medir.
Não distribuir antes de precisar.
Não adicionar dependências sem benefício claro.
Não esconder trade-offs.
Não concentrar conhecimento em uma pessoa.
```

O projeto prioriza:

```text
Clareza
  +
Testabilidade
  +
Operabilidade
  +
Documentação
  +
Evolução controlada
```

sobre complexidade prematura.

---

## Referências

Para aprofundamento:

- [Arquitetura](architecture.md)
- [Architecture Decision Records](adr/README.md)
- [Estratégia de Testes](testing-strategy.md)
- [Runbook Operacional](runbook.md)
- [Prontidão para Produção](production-readiness.md)
- [Resumo Executivo](executive-summary.md)
