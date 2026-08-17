# Traffic Analyzer — Challenge 01

Aplicação em Python para captura, persistência e análise básica de tráfego de rede.

A solução captura pacotes de uma interface especificada, normaliza os dados relevantes, persiste as evidências em SQLite e apresenta automaticamente estatísticas sobre o tráfego observado.

---

## Visão rápida

```text
Network Interface
       ↓
     Scapy
       ↓
Normalization
       ↓
 PacketRecord
       ↓
     SQLite
       ↓
Aggregations
       ↓
Traffic Summary
```

A aplicação responde rapidamente a quatro perguntas:

1. Quantos pacotes foram capturados?
2. Quais protocolos foram observados?
3. Quais IPs de origem movimentaram mais tráfego?
4. Quais IPs de destino movimentaram mais tráfego?

---

## Resultado

A aplicação foi validada com tráfego real dentro do Docker.

Exemplo de uma execução:

```text
Packets captured this run: 243
Packets stored this run: 243

=== Current Capture Summary ===

Total packets: 243

Packets by protocol:
  TCP             148 packets (111.52 KiB)
  UDP              87 packets (39.74 KiB)
  ICMP              8 packets (784 B)
```

Além da validação funcional, o projeto possui testes automatizados cobrindo captura, normalização, persistência e agregações.

---

# Requisitos atendidos

| Requisito | Implementação |
|---|---|
| Capturar interface especificada | Scapy + CLI |
| IP de origem | Sim |
| IP de destino | Sim |
| Protocolo | Sim |
| Tamanho do pacote | Sim |
| Total de pacotes | Sim |
| Pacotes por protocolo | Sim |
| Top 5 IPs de origem | Sim |
| Top 5 IPs de destino | Sim |
| Persistência | SQLite |
| Python | Sim |
| Docker | Sim |
| Documentação | Sim |
| Testes automatizados | Sim |

---

# Tecnologias

- Python 3.12
- Scapy
- SQLite
- Pytest
- Docker
- Docker Compose

---

# Execução rápida

## 1. Identificar a interface

```bash
ip -br addr
```

Exemplo:

```text
wlp0s20f3    UP    192.168.100.223/24
```

O nome da interface varia de acordo com o host.

---

## 2. Configurar a interface

O `compose.yaml` contém o argumento:

```text
--interface
```

Ajuste o valor para uma interface existente no host.

---

## 3. Construir

```bash
docker compose build
```

Quando for necessário garantir uma reconstrução completa:

```bash
docker compose build --no-cache
```

---

## 4. Executar

```bash
docker compose run --rm traffic-analyzer
```

Por padrão, a aplicação captura tráfego durante 30 segundos.

Ao final, os pacotes são persistidos e o resumo é exibido automaticamente.

---

# Exemplo de saída

```text
Capturing IP traffic on 'wlp0s20f3' for 30 seconds...
Database: /app/data/traffic.db

Capture finished.
Packets captured this run: 243
Packets stored this run: 243

=== Current Capture Summary ===

Total packets: 243

Packets by protocol:
  TCP             148 packets (111.52 KiB)
  UDP              87 packets (39.74 KiB)
  ICMP              8 packets (784 B)

Top 5 source IPs by traffic volume:
  1. ... 66.90 KiB (81 packets)
  2. ...
  3. ...
  4. ...
  5. ...

Top 5 destination IPs by traffic volume:
  1. ... 58.24 KiB (39 packets)
  2. ...
  3. ...
  4. ...
  5. ...
```

---

# Outras formas de execução

## Por duração

```bash
docker compose run --rm traffic-analyzer \
  --interface wlp0s20f3 \
  --duration 60 \
  --database /app/data/traffic.db
```

---

## Por quantidade

```bash
docker compose run --rm traffic-analyzer \
  --interface wlp0s20f3 \
  --count 100 \
  --database /app/data/traffic.db
```

`--duration` e `--count` são mutuamente exclusivos.

Quando nenhum deles é informado, a aplicação utiliza 30 segundos.

---

## Saída detalhada

Por padrão, cada pacote individual não é exibido.

Para diagnóstico:

```bash
docker compose run --rm traffic-analyzer \
  --interface wlp0s20f3 \
  --duration 30 \
  --verbose
```

---

# Dados capturados

Cada pacote IP é normalizado para:

```text
PacketRecord
├── source_ip
├── destination_ip
├── protocol
└── packet_size
```

Também é armazenado:

```text
captured_at
```

Pacotes sem IPv4 ou IPv6 são ignorados porque não possuem os endereços IP exigidos pelo contrato da aplicação.

---

# Banco de dados

A solução utiliza SQLite.

Schema:

```sql
CREATE TABLE IF NOT EXISTS packets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    captured_at TEXT NOT NULL,
    source_ip TEXT NOT NULL,
    destination_ip TEXT NOT NULL,
    protocol TEXT NOT NULL,
    packet_size INTEGER NOT NULL
);
```

Índices:

```sql
CREATE INDEX IF NOT EXISTS idx_packets_protocol
ON packets(protocol);

CREATE INDEX IF NOT EXISTS idx_packets_source_ip
ON packets(source_ip);

CREATE INDEX IF NOT EXISTS idx_packets_destination_ip
ON packets(destination_ip);
```

SQLite foi escolhido porque atende ao requisito de persistência sem introduzir infraestrutura adicional desnecessária para o escopo atual.

---

# Definição de "mais tráfego"

O ranking dos IPs utiliza volume transferido:

```sql
SUM(packet_size)
```

como critério principal.

A quantidade de pacotes também é apresentada.

Isso permite distinguir:

```text
muitos pacotes pequenos
```

de:

```text
menos pacotes movimentando maior volume
```

A decisão completa está documentada em:

[ADR 0003 — Classificar tráfego pelo volume em bytes](docs/adr/0003-rank-traffic-by-bytes.md)

---

# Persistência

O diretório:

```text
./data
```

é montado no container em:

```text
/app/data
```

O banco padrão é:

```text
data/traffic.db
```

Assim, os dados permanecem no host mesmo depois que o container termina.

---

# Consultar os dados

Quantidade total:

```bash
sqlite3 data/traffic.db \
"SELECT COUNT(*) FROM packets;"
```

Últimos pacotes:

```bash
sqlite3 data/traffic.db \
"SELECT
    captured_at,
    source_ip,
    destination_ip,
    protocol,
    packet_size
 FROM packets
 ORDER BY id DESC
 LIMIT 10;"
```

---

# Relatório histórico

Também é possível analisar todo o banco posteriormente:

```bash
python -m app.report --database data/traffic.db
```

Existe uma diferença intencional:

```text
Current Capture Summary
        ↓
somente a execução atual

Historical Report
        ↓
todo o banco
```

Isso impede que capturas anteriores contaminem as estatísticas da execução corrente.

---

# Testes

Crie e ative o ambiente:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Instale:

```bash
pip install -r requirements.txt
```

Execute:

```bash
pytest -v
```

A suíte cobre:

- IPv4;
- IPv6;
- TCP;
- UDP;
- ICMP;
- ICMPv6;
- tráfego não IP;
- persistência;
- múltiplos registros;
- agregações;
- ranking por bytes;
- isolamento entre histórico e captura atual.

---

# Documentação

O projeto utiliza documentação em níveis diferentes para permitir leitura rápida ou aprofundamento conforme a necessidade.

## Quero entender o projeto rapidamente

[Resumo Executivo](docs/executive-summary.md)

Explica:

- o problema;
- a solução;
- impacto;
- resultado;
- limitações;
- próximos passos.

---

## Quero entender como a solução funciona

[Arquitetura](docs/architecture.md)

Apresenta:

- componentes;
- fluxo dos dados;
- banco;
- responsabilidades;
- segurança;
- escalabilidade.

---

## Quero conhecer as principais decisões

[Resumo das Decisões de Arquitetura](docs/architecture-decisions.md)

Permite visualizar rapidamente:

- decisões;
- justificativas;
- trade-offs;
- pontos de revisão.

---

## Quero entender por que cada decisão foi tomada

[Architecture Decision Records](docs/adr/README.md)

ADRs disponíveis:

- [ADR 0001 — Python + Scapy](docs/adr/0001-use-python-and-scapy.md)
- [ADR 0002 — SQLite](docs/adr/0002-use-sqlite.md)
- [ADR 0003 — Ranking por bytes](docs/adr/0003-rank-traffic-by-bytes.md)
- [ADR 0004 — IPv4 + IPv6](docs/adr/0004-support-ipv4-and-ipv6.md)
- [ADR 0005 — Host networking](docs/adr/0005-use-host-networking.md)
- [ADR 0006 — Isolamento da captura](docs/adr/0006-isolate-current-capture.md)

---

## Quero saber como validamos

[Estratégia de Testes](docs/testing-strategy.md)

Descreve:

- testes unitários;
- persistência;
- agregações;
- Docker;
- validação funcional;
- tráfego real;
- regressões.

---

## Quero executar ou diagnosticar

[Runbook Operacional](docs/runbook.md)

Contém:

- configuração;
- execução;
- validação;
- troubleshooting;
- escalonamento.

---

## Quero avaliar uso em produção

[Prontidão para Produção](docs/production-readiness.md)

Apresenta:

- limites atuais;
- riscos;
- performance;
- segurança;
- observabilidade;
- retenção;
- confiabilidade;
- possíveis caminhos de evolução.

---

# Estrutura do projeto

```text
.
├── app/
│   ├── __init__.py
│   ├── capture.py
│   ├── database.py
│   ├── report.py
│   └── sniffer.py
│
├── data/
│   └── .gitkeep
│
├── docs/
│   ├── adr/
│   │   ├── README.md
│   │   ├── 0001-use-python-and-scapy.md
│   │   ├── 0002-use-sqlite.md
│   │   ├── 0003-rank-traffic-by-bytes.md
│   │   ├── 0004-support-ipv4-and-ipv6.md
│   │   ├── 0005-use-host-networking.md
│   │   └── 0006-isolate-current-capture.md
│   │
│   ├── architecture-decisions.md
│   ├── architecture.md
│   ├── executive-summary.md
│   ├── production-readiness.md
│   ├── runbook.md
│   └── testing-strategy.md
│
├── tests/
│   ├── test_capture.py
│   └── test_database.py
│
├── .dockerignore
├── .gitignore
├── compose.yaml
├── Dockerfile
├── pytest.ini
├── requirements.txt
└── README.md
```

---

# Principais decisões

A solução priorizou:

```text
Aderência ao requisito
        +
Simplicidade
        +
Separação de responsabilidades
        +
Testabilidade
        +
Reprodutibilidade
        +
Operabilidade
        +
Transferência de conhecimento
```

Não foram adicionados componentes como filas, bancos externos, APIs ou plataformas de orquestração porque o requisito atual não os justifica.

Os limites são conhecidos e os caminhos de evolução estão documentados.

---

# Limitações atuais

A implementação foi dimensionada para capturas pontuais e troubleshooting.

Entre os limites conhecidos:

- SQLite como armazenamento local;
- commit individual por pacote;
- ausência de política automática de retenção;
- ausência de processamento distribuído;
- ausência de observabilidade externa;
- dependência das permissões da interface;
- utilização de host networking para captura no Docker.

Essas limitações estão detalhadas em:

[Prontidão para Produção](docs/production-readiness.md)

---

# Filosofia da solução

A aplicação foi construída seguindo uma regra simples:

```text
Resolver o problema atual
        ↓
Com a menor complexidade necessária
        ↓
Deixar os trade-offs explícitos
        ↓
Validar objetivamente
        ↓
Documentar
        ↓
Evoluir somente quando houver necessidade
```

O objetivo não é demonstrar complexidade técnica pela quantidade de componentes.

É entregar uma solução que funcione, possa ser compreendida, validada, operada e evoluída por outras pessoas.
