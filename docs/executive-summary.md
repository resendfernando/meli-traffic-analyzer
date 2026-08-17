# Executive Summary — Traffic Analyzer

## Em 30 segundos

O Traffic Analyzer é uma aplicação containerizada que captura tráfego de uma interface de rede, registra evidências em banco de dados e transforma os dados coletados em informações simples para investigação.

A solução responde rapidamente a quatro perguntas:

1. Quanto tráfego foi observado?
2. Quais protocolos estão presentes?
3. Quais origens concentram maior volume?
4. Quais destinos concentram maior volume?

O objetivo não é substituir uma plataforma completa de observabilidade, mas fornecer uma ferramenta simples, reproduzível e confiável para coleta inicial de evidências e análise de tráfego.

---

## O problema

Durante uma investigação de rede, capturar pacotes é apenas parte do trabalho.

Os dados precisam ser:

```text
capturados
    ↓
estruturados
    ↓
preservados
    ↓
analisados
    ↓
transformados em informação
```

Sem esse fluxo, a análise pode depender de observação manual, conhecimento individual ou informações que deixam de existir quando a captura termina.

---

## A solução

A aplicação automatiza esse fluxo:

```text
Network Interface
       ↓
Packet Capture
       ↓
Normalization
       ↓
SQLite
       ↓
Traffic Analysis
       ↓
Operational Summary
```

Cada pacote IP gera um registro contendo:

```text
Source IP
Destination IP
Protocol
Packet Size
Timestamp
```

Ao final da execução, a aplicação apresenta automaticamente:

- total de pacotes;
- distribuição por protocolo;
- volume por protocolo;
- Top 5 IPs de origem por volume;
- Top 5 IPs de destino por volume.

Os dados permanecem armazenados para análise posterior.

---

## Resultado validado

A solução foi testada em uma interface real e executada dentro do Docker.

Em uma das validações:

```text
Packets captured: 243
Packets stored:   243
```

Distribuição observada:

```text
TCP     148 packets
UDP      87 packets
ICMP      8 packets
```

Além dos testes funcionais, a aplicação possui testes automatizados cobrindo normalização, persistência e agregações.

---

## Impacto

A ferramenta reduz o esforço necessário para transformar uma captura de rede em informação utilizável.

### Para quem investiga

Fornece evidências objetivas e persistentes.

### Para quem opera

Possui execução padronizada via Docker e procedimentos documentados.

### Para quem mantém

As responsabilidades estão separadas e protegidas por testes automatizados.

### Para liderança

O resultado pode ser consumido sem necessidade de analisar pacotes individualmente ou compreender a implementação.

---

## Decisões importantes

A solução foi mantida propositalmente simples.

Foram utilizados:

```text
Python + Scapy
        ↓
SQLite
        ↓
CLI
        ↓
Docker
```

Não foram adicionados componentes distribuídos porque o requisito atual não os justifica.

Essa escolha reduz:

- complexidade;
- dependências;
- custo operacional;
- superfície de falha;
- tempo necessário para transferência de conhecimento.

---

## Riscos e limitações

A implementação atual é adequada para capturas pontuais e troubleshooting.

Não foi projetada para captura contínua em larga escala.

Os principais limites conhecidos são:

- SQLite como armazenamento local;
- commit individual por pacote;
- ausência de retenção automática;
- processamento no mesmo processo da captura;
- ausência de métricas e alertas externos;
- dependência das permissões de captura da interface.

Essas limitações são conhecidas e documentadas.

---

## Se precisasse ir para produção

A primeira decisão não seria simplesmente adicionar mais tecnologia.

Primeiro seriam medidos:

```text
volume
throughput
retention
concurrency
availability requirement
recovery requirement
security requirement
```

A partir dessas necessidades, poderiam ser introduzidos:

- escrita em batch;
- buffer ou fila;
- armazenamento escalável;
- métricas;
- alertas;
- política de retenção;
- hardening;
- múltiplos coletores.

A arquitetura evoluiria de acordo com evidências e requisitos reais.

---

## Ownership e continuidade

A solução não foi construída para depender exclusivamente de quem a desenvolveu.

O repositório contém:

```text
README
    → como executar

Architecture
    → como funciona

Technical Decisions
    → por que as decisões foram tomadas

Testing Strategy
    → como validamos

Runbook
    → como operar e diagnosticar

Production Readiness
    → o que falta para escalar
```

O objetivo é permitir que outra pessoa consiga entender, executar, diagnosticar e evoluir a solução com segurança.

---

## Conclusão

O resultado entregue não é apenas um script de captura.

É um fluxo pequeno e reproduzível para:

```text
observar
   ↓
registrar
   ↓
analisar
   ↓
comunicar
   ↓
permitir continuidade
```

A implementação atende ao problema atual mantendo uma arquitetura simples e deixando explícitos seus limites e possíveis caminhos de evolução.
