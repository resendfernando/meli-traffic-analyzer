# ADR 0002: Utilizar SQLite para persistência

- **Status:** Aceito
- **Data:** 2026-08-17

## Contexto

Os pacotes capturados precisam ser armazenados em um banco de dados.

O cenário atual possui um único coletor realizando análise local e não apresenta requisitos de:

- múltiplos escritores concorrentes;
- ingestão distribuída;
- alta disponibilidade;
- retenção de grande escala.

Introduzir um serviço externo de banco de dados aumentaria a complexidade operacional sem resolver uma necessidade atual.

## Decisão

Utilizar SQLite como camada de persistência.

Cada pacote normalizado é armazenado com:

```text
id
captured_at
source_ip
destination_ip
protocol
packet_size
```

Também são utilizados índices nos campos relevantes para as principais consultas de agregação.

## Justificativa

SQLite fornece:

- persistência real;
- comportamento transacional;
- nenhuma infraestrutura externa;
- integração nativa com Python;
- facilidade de inspeção;
- persistência simples via volume Docker.

Atende integralmente ao requisito atual com baixo custo operacional.

## Alternativas consideradas

### PostgreSQL

Forneceria maior capacidade de concorrência e escalabilidade, mas essas características não são exigidas pelo cenário atual.

### Armazenamento em memória

Simplificaria a implementação, porém não atenderia ao requisito de persistência e perderia as evidências após o encerramento do processo.

### Arquivos

Permitiriam persistência, porém consultas estruturadas e agregações seriam menos adequadas do que em um banco relacional.

## Consequências

### Benefícios

- nenhuma infraestrutura adicional;
- implantação simples;
- fácil inspeção e backup;
- suporte a agregações SQL;
- dados persistem após o encerramento do container.

### Trade-offs

- capacidade limitada para escrita concorrente;
- armazenamento permanece associado ao nó;
- commits individuais não são ideais para ingestão de alto volume.

## Quando revisitar

Reavaliar a persistência quando existirem requisitos ou medições indicando:

- alto volume sustentado;
- múltiplos coletores;
- escritores concorrentes;
- analytics centralizado;
- alta disponibilidade;
- grande período de retenção.

A tecnologia deve evoluir quando o workload justificar essa mudança.
