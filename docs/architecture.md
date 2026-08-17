# Architecture — Traffic Analyzer

## 1. Visão geral

O Traffic Analyzer foi desenvolvido para capturar pacotes de uma interface de rede, normalizar informações relevantes, armazenar os dados e apresentar estatísticas básicas sobre o tráfego observado.

A arquitetura foi deliberadamente mantida simples para atender ao escopo do desafio sem introduzir componentes que aumentariam desnecessariamente a complexidade operacional.

Os principais objetivos arquiteturais foram:

- separação de responsabilidades;
- baixo acoplamento;
- facilidade de teste;
- reprodutibilidade;
- facilidade de operação;
- persistência dos dados;
- possibilidade de evolução futura.

---

## 2. Arquitetura de alto nível

```text
                 +----------------------+
                 |  Network Interface   |
                 |  eth0 / wlan / etc. |
                 +----------+-----------+
                            |
                            v
                 +----------------------+
                 |        Scapy         |
                 |   Packet Capture     |
                 +----------+-----------+
                            |
                            v
                 +----------------------+
                 |    Normalization     |
                 |     capture.py       |
                 +----------+-----------+
                            |
                            v
                 +----------------------+
                 |     PacketRecord     |
                 |                      |
                 | source_ip            |
                 | destination_ip       |
                 | protocol             |
                 | packet_size          |
                 +----------+-----------+
                            |
                            v
                 +----------------------+
                 |       SQLite         |
                 |     database.py      |
                 +----------+-----------+
                            |
                            v
                 +----------------------+
                 |     Aggregations     |
                 |                      |
                 | total packets        |
                 | protocol breakdown   |
                 | top source IPs       |
                 | top destination IPs  |
                 +----------+-----------+
                            |
                            v
                 +----------------------+
                 |      CLI Report      |
                 |      report.py       |
                 +----------------------+
```

---

## 3. Componentes

### 3.1 `capture.py`

Responsável pela normalização dos pacotes recebidos do Scapy.

A camada de captura converte os objetos específicos da biblioteca em uma estrutura interna simples:

```text
PacketRecord
├── source_ip
├── destination_ip
├── protocol
└── packet_size
```

Essa decisão cria uma fronteira clara entre a biblioteca utilizada para captura e o restante da aplicação.

As demais camadas não precisam conhecer a estrutura interna dos objetos Scapy.

Isso permite que:

- os testes criem pacotes controlados;
- a persistência trabalhe apenas com dados normalizados;
- a biblioteca de captura possa ser substituída futuramente com menor impacto;
- regras de identificação de protocolo permaneçam centralizadas.

Pacotes sem camada IPv4 ou IPv6 são ignorados, pois não possuem os endereços IP exigidos pelo escopo do desafio.

---

### 3.2 `sniffer.py`

É o ponto principal de execução da aplicação.

Suas responsabilidades incluem:

- receber os argumentos da CLI;
- validar a interface de rede;
- controlar o modo de captura;
- iniciar o Scapy;
- receber os pacotes;
- solicitar sua normalização;
- persistir os registros;
- controlar o escopo da captura atual;
- exibir o relatório ao final.

A captura pode terminar por:

```text
duration
```

ou:

```text
count
```

Os dois parâmetros são mutuamente exclusivos.

Quando nenhum deles é especificado, a aplicação utiliza uma duração padrão de 30 segundos.

---

### 3.3 `database.py`

Responsável pela camada de persistência.

Essa camada:

- inicializa o banco;
- cria a tabela;
- cria os índices;
- insere pacotes;
- conta registros;
- executa agregações;
- calcula os rankings utilizados pelo relatório.

O restante da aplicação não executa SQL diretamente.

Essa separação concentra as decisões relacionadas ao armazenamento em um único componente.

---

### 3.4 `report.py`

Responsável pela apresentação das estatísticas.

O relatório recebe os resultados das consultas e os transforma em uma saída legível no terminal.

São apresentados:

- total de pacotes;
- quantidade por protocolo;
- volume por protocolo;
- Top 5 IPs de origem;
- Top 5 IPs de destino;
- quantidade de pacotes associada aos rankings.

A mesma camada pode ser utilizada:

1. automaticamente ao final de uma captura;
2. posteriormente sobre um banco já existente.

---

## 4. Fluxo de processamento

O fluxo de um pacote pode ser representado como:

```text
Packet arrives
     |
     v
Scapy receives packet
     |
     v
Is it IPv4 or IPv6?
     |
     +------ No ------> Ignore
     |
    Yes
     |
     v
Extract source IP
     |
     v
Extract destination IP
     |
     v
Identify protocol
     |
     v
Calculate packet size
     |
     v
Create PacketRecord
     |
     v
Persist in SQLite
     |
     v
Include in current capture statistics
```

A análise estatística ocorre sobre os registros persistidos.

---

## 5. Modelo de dados

A tabela principal é:

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

### Campos

#### `id`

Identificador sequencial do registro.

Além de identificar cada pacote, ele é utilizado para separar os dados históricos dos registros pertencentes à captura atual.

#### `captured_at`

Timestamp UTC correspondente ao momento da persistência do pacote.

Foi adicionado para fornecer rastreabilidade temporal.

#### `source_ip`

Endereço IP de origem.

Pode conter IPv4 ou IPv6.

#### `destination_ip`

Endereço IP de destino.

Pode conter IPv4 ou IPv6.

#### `protocol`

Representação normalizada do protocolo.

Exemplos:

```text
TCP
UDP
ICMP
ICMPv6
```

Protocolos IP não classificados explicitamente mantêm o identificador numérico.

#### `packet_size`

Tamanho total do pacote observado, em bytes.

Esse campo também é utilizado para determinar os IPs com maior volume de tráfego.

---

## 6. Índices

Foram criados índices sobre:

```text
protocol
source_ip
destination_ip
```

Schema:

```sql
CREATE INDEX IF NOT EXISTS idx_packets_protocol
ON packets(protocol);

CREATE INDEX IF NOT EXISTS idx_packets_source_ip
ON packets(source_ip);

CREATE INDEX IF NOT EXISTS idx_packets_destination_ip
ON packets(destination_ip);
```

Esses campos são utilizados diretamente nas agregações solicitadas pelo desafio.

A decisão evita adicionar índices sem uma necessidade conhecida.

Em bancos maiores, a estratégia de indexação deveria ser validada a partir dos padrões reais de consulta e dos planos de execução.

---

## 7. Escolha do SQLite

SQLite foi escolhido como banco de dados porque atende ao escopo proposto com baixa complexidade operacional.

### Vantagens para este cenário

- persistência real em disco;
- zero infraestrutura externa;
- não exige servidor de banco;
- fácil execução dentro e fora do Docker;
- fácil inspeção manual;
- suporte nativo no Python;
- suficiente para o volume esperado em uma captura pontual.

### Trade-off

SQLite não é a solução ideal para ingestão concorrente e contínua em grande escala.

Se o requisito mudasse para múltiplos coletores ou alto volume sustentado, a camada de persistência poderia ser substituída sem alterar a normalização dos pacotes.

---

## 8. Definição de tráfego

O requisito solicita os cinco endereços IP de origem e destino com "mais tráfego".

Existem pelo menos duas interpretações possíveis:

```text
maior quantidade de pacotes
```

ou:

```text
maior volume de dados
```

A implementação utiliza volume de dados como critério principal:

```sql
SUM(packet_size)
```

A quantidade de pacotes também é exibida.

Exemplo conceitual:

```text
IP A -> 100 packets -> 10 KiB
IP B -> 20 packets  -> 80 KiB
```

Nesse cenário, o IP B aparece primeiro no ranking porque movimentou maior volume de tráfego, apesar de possuir menos pacotes.

Essa abordagem preserva as duas informações relevantes no relatório.

---

## 9. Isolamento da captura atual

O SQLite pode conter dados de execuções anteriores.

Por isso, utilizar todo o banco no relatório apresentado ao final de uma captura produziria um resultado incorreto para:

```text
tráfego capturado nesta execução
```

Antes de iniciar a captura, a aplicação registra o maior `id` existente:

```text
start_id
```

As consultas do resumo utilizam:

```sql
WHERE id > ?
```

considerando somente os registros criados depois do início da execução.

O comportamento fica:

```text
Historical packets
IDs 1 ... 500
       |
       | start_id = 500
       v
New capture
IDs 501 ... 743
       |
       v
Current Capture Summary
only IDs > 500
```

O relatório executado separadamente pode continuar analisando todo o histórico.

---

## 10. Identificação de protocolos

Os protocolos conhecidos são normalizados para nomes legíveis.

A aplicação reconhece:

```text
TCP
UDP
ICMP
ICMPv6
```

Para protocolos IPv4 não tratados explicitamente:

```text
IP-<protocol-number>
```

Para IPv6:

```text
IPv6-<next-header-number>
```

Essa decisão permite preservar informação sobre protocolos desconhecidos em vez de classificá-los simplesmente como `UNKNOWN`.

---

## 11. IPv4 e IPv6

A aplicação suporta ambos.

Exemplo IPv4:

```text
192.168.100.223
```

Exemplo IPv6:

```text
2804:d45:b302:1000:59af:8fc7:2789:b1d0
```

Os endereços são armazenados como texto.

Isso mantém o modelo simples e permite armazenar os dois formatos na mesma estrutura.

---

## 12. Persistência por pacote

A implementação atual realiza:

```text
packet
  |
  v
INSERT
  |
  v
COMMIT
```

para cada registro.

### Motivo

Para o escopo atual, essa abordagem prioriza:

- simplicidade;
- previsibilidade;
- persistência imediata;
- facilidade de entendimento.

### Trade-off

O custo de commits individuais pode se tornar significativo em alto volume.

Uma evolução natural seria:

```text
Packets
   |
   v
In-memory buffer
   |
   v
Batch INSERT
   |
   v
Periodic COMMIT
```

Outra possibilidade seria desacoplar captura e persistência utilizando uma fila.

Essas otimizações não foram implementadas porque não são necessárias para atender ao problema atual.

---

## 13. Docker

A aplicação é empacotada em uma imagem Docker para garantir um ambiente reproduzível.

A imagem contém:

- Python;
- dependências;
- aplicação;
- testes;
- suporte necessário para captura.

O banco é mantido fora do ciclo de vida do container por meio de volume.

```text
Host
./data/traffic.db
        |
        | volume
        v
Container
/app/data/traffic.db
```

Assim, remover o container não remove os dados capturados.

---

## 14. Network mode

O container utiliza:

```yaml
network_mode: host
```

### Motivo

A aplicação precisa capturar tráfego de uma interface física existente no host.

No Linux, utilizar a rede do host permite que o container tenha acesso às interfaces necessárias para o cenário do desafio.

### Trade-off

`network_mode: host` reduz o isolamento de rede normalmente fornecido por containers.

Essa decisão é adequada ao cenário de laboratório/desafio, mas deve ser reavaliada antes de uma eventual utilização produtiva.

---

## 15. Capabilities

A configuração adiciona:

```yaml
cap_add:
  - NET_RAW
  - NET_ADMIN
```

A captura de pacotes requer privilégios de rede adicionais.

Adicionar capabilities específicas é preferível a executar o container utilizando:

```text
--privileged
```

porque mantém o conjunto de privilégios mais restrito.

Ainda assim, qualquer permissão adicional deve ser avaliada de acordo com o ambiente onde a aplicação será executada.

---

## 16. Segurança e privacidade

A aplicação não armazena payload.

Somente os seguintes metadados são persistidos:

```text
captured_at
source_ip
destination_ip
protocol
packet_size
```

Isso reduz a quantidade de informação coletada e mantém o escopo alinhado aos requisitos.

Mesmo assim, endereços IP e metadados de comunicação podem ser informações sensíveis dependendo do ambiente.

Uma implantação real deveria considerar:

- autorização para captura;
- controle de acesso ao banco;
- política de retenção;
- proteção do arquivo SQLite;
- requisitos de privacidade;
- requisitos regulatórios.

---

## 17. Testabilidade

A arquitetura foi estruturada para permitir testes sem depender de tráfego real em todas as validações.

O Scapy pode criar pacotes sintéticos utilizados nos testes de normalização.

Exemplo conceitual:

```text
Synthetic Scapy Packet
        |
        v
normalize_packet()
        |
        v
Expected PacketRecord
```

A camada de banco utiliza:

```text
:memory:
```

durante os testes.

Isso permite validar:

- schema;
- persistência;
- agregações;
- rankings;

sem criar bancos permanentes.

A captura real é utilizada como teste funcional complementar.

---

## 18. Observabilidade operacional

Para o escopo atual, a própria CLI fornece os principais sinais operacionais:

```text
Packets captured this run
Packets stored this run
```

Em uma execução normal, espera-se:

```text
captured == stored
```

A aplicação também apresenta imediatamente as estatísticas da execução.

Para uma solução de produção, seria recomendável adicionar métricas como:

- packets received;
- packets processed;
- packets dropped;
- database write latency;
- processing latency;
- buffer utilization;
- capture errors;
- storage errors.

Essas métricas poderiam alimentar uma plataforma de observabilidade e alertas.

---

## 19. Escalabilidade

A arquitetura atual é adequada para:

- troubleshooting;
- diagnóstico pontual;
- pequenos períodos de captura;
- análise local;
- ambientes de laboratório.

Não foi projetada para:

- captura 24x7 em larga escala;
- milhares de interfaces;
- múltiplos coletores concorrentes;
- analytics distribuído;
- retenção de grandes volumes.

Se o requisito evoluísse, uma possível arquitetura seria:

```text
             +----------------+
             | Collector 01   |
             +-------+--------+
                     |
             +-------v--------+
             | Collector 02   |
             +-------+--------+
                     |
                     v
             +----------------+
             | Queue / Buffer |
             +-------+--------+
                     |
                     v
             +----------------+
             | Processing     |
             +-------+--------+
                     |
             +-------+--------+
             |                |
             v                v
     +---------------+   +---------------+
     | Metrics Store |   | Data Storage  |
     +-------+-------+   +-------+-------+
             |                   |
             v                   v
         Monitoring          Analytics
             |                   |
             +---------+---------+
                       |
                       v
                Alerts / Dashboard
```

O importante é que essa complexidade só deve ser adicionada quando houver um requisito que a justifique.

---

## 20. Limitações conhecidas

### SQLite

Não é indicado para alto volume de escrita concorrente.

### Commit individual

Existe um commit para cada pacote.

### Retenção

Não existe limpeza automática ou política de retenção.

### Processamento

Captura e persistência fazem parte do mesmo processo.

### Fila

Não existe buffer assíncrono entre captura e banco.

### Alta disponibilidade

A solução atual utiliza uma única instância.

### Payload

Não existe Deep Packet Inspection.

### Visibilidade

A aplicação só pode analisar o tráfego que esteja visível na interface selecionada.

### Plataforma

A configuração Docker de captura utiliza recursos específicos adequados ao host Linux utilizado no desafio.

---

## 21. Evoluções possíveis

Se justificadas por novos requisitos:

### Performance

- batch inserts;
- transações maiores;
- buffer em memória;
- processamento assíncrono.

### Persistência

- PostgreSQL;
- banco analítico;
- time-series database;
- object storage para grandes volumes.

### Processamento

- filas;
- workers;
- processamento distribuído.

### Operação

- métricas;
- health checks;
- dashboards;
- alertas;
- retenção automática.

### Segurança

- usuário não root;
- redução adicional de capabilities;
- criptografia;
- controle de acesso;
- gestão de secrets.

### Produto

- filtros por protocolo;
- filtros por IP;
- intervalos temporais;
- exportação;
- API;
- interface web.

---

## 22. Decisões deliberadamente não tomadas

Alguns componentes poderiam ter sido adicionados, mas não foram necessários para resolver o desafio.

Por exemplo:

- API REST;
- frontend;
- Redis;
- Kafka;
- PostgreSQL;
- Kubernetes;
- dashboard;
- sistema distribuído.

Adicionar esses componentes aumentaria:

- quantidade de código;
- dependências;
- superfície de falha;
- esforço operacional;
- tempo necessário para entendimento.

A solução segue o princípio de utilizar a menor arquitetura capaz de atender adequadamente aos requisitos atuais.

---

## 23. Transferência de conhecimento

Uma preocupação da implementação é permitir que outra pessoa consiga operar e evoluir a aplicação.

Por isso o projeto possui:

```text
README
    |
    +--> configuração e uso

architecture.md
    |
    +--> decisões e trade-offs

runbook.md
    |
    +--> operação e troubleshooting

automated tests
    |
    +--> validação objetiva

Docker
    |
    +--> ambiente reproduzível
```

O objetivo é reduzir dependência de conhecimento individual.

---

## 24. Critérios de sucesso operacional

Uma captura pode ser considerada bem-sucedida quando:

1. A interface solicitada existe.
2. A aplicação inicia sem erro de permissão.
3. Pacotes IP são recebidos.
4. Os pacotes são normalizados.
5. Os registros são persistidos.
6. A quantidade capturada coincide com a quantidade armazenada.
7. O relatório é gerado.
8. A soma dos protocolos corresponde ao total de pacotes.
9. Os rankings são calculados sobre o escopo correto da captura.

Esses critérios fornecem uma forma simples e objetiva de verificar a saúde da execução.

---

## 25. Resumo

A arquitetura foi desenhada para resolver o problema apresentado com o menor nível de complexidade necessário, mantendo separação clara entre:

```text
capture
normalization
storage
analysis
presentation
```

A solução atual privilegia simplicidade e operabilidade.

Ao mesmo tempo, as fronteiras entre os componentes permitem que partes específicas — principalmente armazenamento e processamento — sejam substituídas caso novos requisitos de escala, performance ou disponibilidade apareçam.
