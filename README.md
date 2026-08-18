# Traffic Analyzer — Challenge 01

> **Challenge 01 — Network Traffic Analyzer**
>
> Este README documenta a implementação do primeiro exercício do desafio técnico.
>
> **Challenge 02:** [Prompt para Análise de Logs de Infraestrutura](docs/challenge-02-ai-log-analysis.md)
>
> **Validação adversarial:** [Testes adversariais do Challenge 02](docs/challenge-02-adversarial-tests.md)

Aplicação em Python para captura, persistência e análise básica de tráfego de rede.

A solução captura pacotes de uma interface de rede, normaliza os dados relevantes, persiste as evidências em SQLite e apresenta automaticamente estatísticas sobre o tráfego observado.

---

# Quick Start

Para o caminho mais simples:

```bash
docker compose up --build
```

A aplicação:

1. detecta automaticamente uma interface de rede adequada;
2. captura tráfego durante 30 segundos;
3. persiste os pacotes em SQLite;
4. gera o relatório da captura;
5. encerra normalmente.

Exemplo:

```text
Auto-detected interface: wlp0s20f3
Capturing IP traffic on 'wlp0s20f3' for 30 seconds...
Database: /app/data/traffic.db

Capture finished.
Packets captured this run: 153
Packets stored this run: 153

=== Current Capture Summary ===

Total packets: 153

Packets by protocol:
  TCP              82 packets (28.87 KiB)
  UDP              71 packets (29.72 KiB)

Top 5 source IPs by traffic volume:
  ...

Top 5 destination IPs by traffic volume:
  ...
```

Não é necessário editar o `compose.yaml` para o uso padrão.

---

# O que a aplicação responde

Ao final de cada captura:

1. Quantos pacotes foram capturados?
2. Quais protocolos foram observados?
3. Quais IPs de origem movimentaram maior volume?
4. Quais IPs de destino movimentaram maior volume?

Fluxo:

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

---

# Requisitos atendidos

| Requisito | Implementação |
|---|---|
| Capturar interface de rede | Scapy |
| Interface especificável | `--interface` |
| IP de origem | IPv4 + IPv6 |
| IP de destino | IPv4 + IPv6 |
| Protocolo | TCP / UDP / ICMP / ICMPv6 + fallback |
| Tamanho do pacote | `packet_size` |
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

# Interface de rede

## Detecção automática

Quando `--interface` não é informado, a aplicação tenta identificar automaticamente uma interface adequada.

A estratégia preferencial utiliza a interface associada à rota IPv4 padrão.

Se isso não for possível, a aplicação tenta selecionar uma interface não-loopback e evita interfaces virtuais comuns.

A interface escolhida é informada antes da captura:

```text
Auto-detected interface: eth0
```

## Interface explícita

Quando necessário, é possível escolher manualmente:

```bash
docker compose run --rm traffic-analyzer \
  --interface eth0 \
  --duration 30
```

Isso sobrescreve a autodetecção.

Para listar as interfaces no Linux:

```bash
ip -br addr
```

---

# Modos de captura

## Por duração

```bash
docker compose run --rm traffic-analyzer \
  --interface eth0 \
  --duration 60
```

## Por quantidade

```bash
docker compose run --rm traffic-analyzer \
  --interface eth0 \
  --count 100
```

`--duration` e `--count` são mutuamente exclusivos.

Ambos aceitam somente valores inteiros maiores que zero. Valores zero, negativos ou não inteiros são rejeitados antes do início da captura.

Quando nenhum deles é informado, a aplicação utiliza:

```text
30 segundos
```

---

# Saída detalhada

Por padrão, os pacotes individuais não são impressos no terminal.

Isso reduz ruído e mantém o foco no resumo operacional.

Para visualizar cada registro:

```bash
docker compose run --rm traffic-analyzer \
  --interface eth0 \
  --duration 30 \
  --verbose
```

---

# Dados capturados

Cada pacote IPv4 ou IPv6 é normalizado para:

```text
PacketRecord
├── source_ip
├── destination_ip
├── protocol
└── packet_size
```

Também é persistido:

```text
captured_at
```

Frames não-IP não fazem parte das estatísticas porque não possuem os endereços IP exigidos pelo escopo do desafio.

Portanto:

```text
Total packets
```

representa os pacotes IPv4 e IPv6 processados pelo filtro da aplicação.

---

# Protocolos

A aplicação reconhece diretamente:

```text
TCP
UDP
ICMP
ICMPv6
```

Outros protocolos IP continuam sendo registrados utilizando seu identificador numérico.

Exemplos:

```text
IP-2
IPv6-50
```

Isso evita descartar tráfego IP que não tenha um nome explicitamente mapeado.

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

SQLite foi escolhido porque atende ao requisito de persistência sem introduzir um serviço externo de banco de dados para o escopo atual.

---

# Persistência dos dados

No host:

```text
./data
```

é montado no container como:

```text
/app/data
```

Banco padrão:

```text
data/traffic.db
```

Os dados permanecem disponíveis mesmo após o encerramento do container.

---

# Definição de "mais tráfego"

Os Top 5 são classificados pelo volume total movimentado:

```sql
SUM(packet_size)
```

A quantidade de pacotes também é exibida.

Exemplo:

```text
IP A → 100 pacotes → 10 KiB
IP B →  20 pacotes → 80 KiB
```

Nesse cenário, o IP B aparece primeiro porque movimentou maior volume.

Detalhes:

[ADR 0003 — Classificar tráfego pelo volume em bytes](docs/adr/0003-rank-traffic-by-bytes.md)

---

# Captura atual x histórico

O banco pode conter várias execuções.

Por isso existem dois contextos:

```text
Current Capture Summary
        ↓
somente os pacotes da execução atual
```

e:

```text
Historical Report
        ↓
todos os registros existentes no banco
```

A separação evita que dados antigos alterem as estatísticas de uma nova captura.

Detalhes:

[ADR 0006 — Isolar a captura atual do histórico](docs/adr/0006-isolate-current-capture.md)

---

# Consultar o banco

Total de registros:

```bash
sqlite3 data/traffic.db \
"SELECT COUNT(*) FROM packets;"
```

Últimos registros:

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

Para analisar todo o banco:

```bash
python -m app.report --database data/traffic.db
```

---

# Desenvolvimento local

Crie o ambiente:

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
sudo .venv/bin/python -m app.sniffer \
  --interface eth0 \
  --duration 30
```

Também é possível usar autodetecção:

```bash
sudo .venv/bin/python -m app.sniffer
```

---

# Testes

Execute:

```bash
pytest -q
```

A suíte possui atualmente **21 testes automatizados**.

A cobertura inclui:

- IPv4;
- IPv6;
- TCP;
- UDP;
- ICMP;
- ICMPv6;
- descarte de tráfego não-IP;
- criação e persistência no banco;
- múltiplos registros;
- agregação por protocolo;
- ranking por bytes;
- isolamento da captura atual;
- validação dos parâmetros da CLI;
- aceitação de valores positivos para `--count` e `--duration`;
- rejeição de zero e valores negativos;
- rejeição de valores não inteiros.

Além dos testes automatizados, a solução foi validada com tráfego real dentro do Docker.

Também foram executados testes funcionais dos principais fluxos da CLI, incluindo captura por duração, captura por quantidade, modo verbose, banco alternativo, interface inexistente e argumentos mutuamente exclusivos.

---

# Validação funcional

Para gerar tráfego controlado durante uma captura:

```bash
ping -c 4 8.8.8.8
```

```bash
nslookup mercadolivre.com 8.8.8.8
```

```bash
curl -4 https://www.google.com > /dev/null
```

Um dos principais invariantes operacionais é:

```text
Packets captured this run
==
Packets stored this run
```

Esse comportamento foi validado em múltiplas execuções.

Também foi validada a persistência histórica entre execuções independentes, mantendo o `Current Capture Summary` isolado da visão histórica do banco.

---

# Segurança

Para capturar tráfego do host Linux, o container utiliza:

```yaml
network_mode: host
```

e:

```yaml
cap_add:
  - NET_RAW
  - NET_ADMIN
```

A escolha evita utilizar um container completamente privilegiado.

Essas permissões devem ser reavaliadas antes de uma eventual implantação produtiva.

A aplicação não armazena payload.

Somente:

```text
timestamp
source IP
destination IP
protocol
packet size
```

---

# Limitações atuais

A solução foi dimensionada para capturas pontuais e troubleshooting.

Limitações conhecidas:

- SQLite como armazenamento local;
- commit individual por pacote;
- ausência de política automática de retenção;
- ausência de fila assíncrona;
- ausência de processamento distribuído;
- ausência de monitoramento externo;
- captura limitada ao tráfego visível na interface selecionada;
- a visibilidade de interfaces em ambientes virtualizados ou containerizados depende da rede exposta pelo runtime.

Esses limites são documentados e não impedem o atendimento ao escopo atual.

---

# Documentação

A documentação está organizada para diferentes níveis de leitura.

## Challenge 02 — Análise de Logs com IA

[Prompt para Análise de Logs de Infraestrutura](docs/challenge-02-ai-log-analysis.md)

Contém o prompt completo, log de exemplo, resposta esperada e as principais decisões adotadas na construção da solução.

[Validação Adversarial do Prompt](docs/challenge-02-adversarial-tests.md)

Documenta os oito cenários adversariais utilizados para avaliar robustez, segurança, tratamento de evidências, causalidade, severidade e comportamento diante de dados incompletos.

## Visão rápida para liderança

[Resumo Executivo](docs/executive-summary.md)

Problema, solução, resultado, impacto e limitações.

## Arquitetura

[Arquitetura](docs/architecture.md)

Componentes, fluxo, dados e limites técnicos.

## Decisões principais

[Resumo das Decisões de Arquitetura](docs/architecture-decisions.md)

Leitura curta das escolhas mais relevantes.

## Decisões detalhadas

[Architecture Decision Records](docs/adr/README.md)

- [ADR 0001 — Python + Scapy](docs/adr/0001-use-python-and-scapy.md)
- [ADR 0002 — SQLite](docs/adr/0002-use-sqlite.md)
- [ADR 0003 — Ranking por bytes](docs/adr/0003-rank-traffic-by-bytes.md)
- [ADR 0004 — IPv4 + IPv6](docs/adr/0004-support-ipv4-and-ipv6.md)
- [ADR 0005 — Host networking](docs/adr/0005-use-host-networking.md)
- [ADR 0006 — Isolamento da captura](docs/adr/0006-isolate-current-capture.md)

## Estratégia de validação

[Estratégia de Testes](docs/testing-strategy.md)

Como a solução é validada em diferentes camadas.

## Operação

[Runbook](docs/runbook.md)

Execução, diagnóstico e troubleshooting.

## Evolução

[Prontidão para Produção](docs/production-readiness.md)

Limites atuais e critérios para evolução.

---

# Estrutura

```text
.
├── .github/
│   └── workflows/
│       └── ci.yml
├── app/
│   ├── __init__.py
│   ├── capture.py
│   ├── database.py
│   ├── report.py
│   └── sniffer.py
├── data/
│   └── .gitkeep
├── docs/
│   ├── adr/
│   │   ├── README.md
│   │   ├── 0001-use-python-and-scapy.md
│   │   ├── 0002-use-sqlite.md
│   │   ├── 0003-rank-traffic-by-bytes.md
│   │   ├── 0004-support-ipv4-and-ipv6.md
│   │   ├── 0005-use-host-networking.md
│   │   └── 0006-isolate-current-capture.md
│   ├── architecture-decisions.md
│   ├── architecture.md
│   ├── challenge-02-adversarial-tests.md
│   ├── challenge-02-ai-log-analysis.md
│   ├── executive-summary.md
│   ├── production-readiness.md
│   ├── runbook.md
│   └── testing-strategy.md
├── tests/
│   ├── test_capture.py
│   ├── test_database.py
│   └── test_sniffer.py
├── .dockerignore
├── .gitignore
├── compose.yaml
├── Dockerfile
├── pytest.ini
├── requirements.txt
└── README.md
```

---

# Princípio da solução

A implementação segue uma regra simples:

```text
Resolver o problema atual
        ↓
Com a menor complexidade necessária
        ↓
Tornar os trade-offs explícitos
        ↓
Testar
        ↓
Documentar
        ↓
Evoluir quando houver evidência
```

O objetivo é entregar uma solução que funcione, seja simples de executar e possa ser compreendida, validada e evoluída por outra pessoa.
