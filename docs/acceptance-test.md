# Teste de Aceitação e Compatibilidade

Este documento registra a validação final da solução a partir de um clone limpo do repositório, simulando o fluxo de execução de um avaliador.

O objetivo é documentar o comportamento observado em Linux e Windows e explicitar uma diferença importante de visibilidade de rede quando a aplicação é executada através do Docker Desktop.

---

# 1. Critérios de Aceitação

A validação considera os seguintes critérios:

| Critério | Resultado |
|---|---|
| Clone limpo do repositório | ✅ |
| Build via Docker Compose | ✅ |
| Inicialização sem configuração manual da interface | ✅ |
| Detecção automática de interface | ✅ |
| Captura de tráfego IP | ✅ |
| Persistência em SQLite | ✅ |
| Pacotes capturados = pacotes persistidos | ✅ |
| Estatísticas por protocolo | ✅ |
| Top 5 IPs de origem | ✅ |
| Top 5 IPs de destino | ✅ |
| Encerramento normal | ✅ |
| Testes automatizados | ✅ 21/21 |
| Execução validada em Linux | ✅ |
| Execução validada em Windows + Docker Desktop | ✅ |

---

# 2. Teste de Aceitação — Linux

## Ambiente

A validação principal foi executada em Linux a partir de um clone limpo do repositório.

Fluxo utilizado:

```bash
git clone https://github.com/resendfernando/meli-traffic-analyzer.git
cd meli-traffic-analyzer
docker compose up --build
```

Nenhuma alteração no código ou no `compose.yaml` foi necessária antes da execução.

---

## Resultado

A aplicação detectou automaticamente a interface de rede do host:

```text
Auto-detected interface: wlp0s20f3
Capturing IP traffic on 'wlp0s20f3' for 30 seconds...
Database: /app/data/traffic.db
```

Ao final da captura:

```text
Capture finished.
Packets captured this run: 2805
Packets stored this run: 2805
```

O relatório foi produzido normalmente:

```text
=== Current Capture Summary ===

Total packets: 2805

Packets by protocol:
  UDP            1625 packets
  TCP            1113 packets
  ICMP             62 packets
  IP-2               2 packets
  IPv6-0             2 packets
  ICMPv6              1 packet
```

Também foram produzidos:

- Top 5 IPs de origem por volume;
- Top 5 IPs de destino por volume;
- quantidade de pacotes por IP;
- volume movimentado por IP.

O container encerrou normalmente:

```text
traffic-analyzer-1 exited with code 0
```

---

# 3. Invariante de Persistência

Um dos principais critérios utilizados durante a validação foi:

```text
Packets captured this run
==
Packets stored this run
```

No teste final em Linux:

```text
2805 capturados
2805 persistidos
```

Portanto, todos os pacotes normalizados durante essa execução foram persistidos no SQLite.

---

# 4. Testes Automatizados

A suíte automatizada também foi executada antes da validação final:

```bash
pytest -q
```

Resultado:

```text
..................... [100%]
21 passed
```

Os testes cobrem normalização, IPv4, IPv6, protocolos, persistência, agregações, ranking, isolamento entre capturas e validação dos argumentos da CLI.

---

# 5. Validação em Windows

A aplicação também foi validada em Windows utilizando Docker Desktop.

O teste foi realizado a partir de um novo clone do repositório:

```powershell
git clone https://github.com/resendfernando/meli-traffic-analyzer.git
cd meli-traffic-analyzer
docker compose up --build
```

A aplicação iniciou normalmente e detectou:

```text
Auto-detected interface: eth0
```

Resultado observado:

```text
Capture finished.
Packets captured this run: 409
Packets stored this run: 409
```

O relatório foi gerado e o processo encerrou com:

```text
exited with code 0
```

O arquivo SQLite também foi criado normalmente no volume persistente:

```text
data/traffic.db
```

---

# 6. Linux x Windows com Docker Desktop

Existe uma diferença importante entre os ambientes.

## Linux

No Linux, o Docker pode utilizar diretamente a pilha de rede do host através de:

```yaml
network_mode: host
```

Isso permite que a aplicação observe a interface real utilizada pelo sistema operacional, como:

```text
wlp0s20f3
eth0
enp3s0
```

No teste de aceitação, por exemplo:

```text
Auto-detected interface: wlp0s20f3
```

---

## Windows

No Windows, Docker Desktop executa containers Linux através de uma camada de virtualização.

Consequentemente, uma interface detectada dentro do container, como:

```text
eth0
```

pode representar a interface disponibilizada pelo ambiente Docker, e não necessariamente a interface física do Windows.

A aplicação continua funcionando e capturando o tráfego visível nessa interface, como demonstrado no teste realizado.

Entretanto, a quantidade e o tipo de tráfego visível dependem da rede disponibilizada ao container pelo Docker Desktop.

---

# 7. Visibilidade da Rede no Windows

Se o objetivo for observar tráfego além daquele naturalmente visível dentro da rede do Docker Desktop, é necessário garantir que a interface ou o tráfego desejado esteja acessível ao ambiente Docker.

Em outras palavras:

```text
Windows Host
     ↓
Docker Desktop / Virtualização
     ↓
Rede disponibilizada ao container
     ↓
Traffic Analyzer
```

A aplicação somente consegue capturar pacotes que chegam à interface visível dentro desse ambiente.

Por isso, caso a execução no Windows apresente pouco tráfego ou tráfego diferente daquele observado diretamente no host, isso não significa necessariamente falha no analisador.

O primeiro ponto de verificação deve ser a visibilidade da interface de rede dentro do Docker Desktop/container.

---

# 8. Verificação da Interface

A interface utilizada pode ser informada explicitamente:

```bash
docker compose run --rm traffic-analyzer \
  --interface eth0 \
  --duration 30
```

Também é possível consultar as opções da aplicação:

```bash
docker compose run --rm traffic-analyzer --help
```

No uso padrão, nenhuma interface precisa ser especificada:

```bash
docker compose up --build
```

A aplicação tentará selecionar automaticamente uma interface adequada.

---

# 9. Interpretação dos Resultados em Ambientes Virtualizados

Captura de pacotes depende da posição do analisador na topologia de rede.

Assim, em ambientes como:

- Docker Desktop;
- máquinas virtuais;
- WSL;
- redes NAT;
- bridges;
- ambientes de CI;

a aplicação captura o tráfego que é efetivamente apresentado à interface selecionada.

Portanto, dois ambientes diferentes podem apresentar volumes e endereços IP diferentes mesmo executando exatamente a mesma versão da aplicação.

Esse comportamento é esperado para ferramentas de captura de rede.

---

# 10. Resultado Final

A solução foi validada através de:

```text
Clone limpo
    ↓
Docker build
    ↓
Inicialização
    ↓
Detecção automática da interface
    ↓
Captura real
    ↓
Normalização
    ↓
Persistência SQLite
    ↓
Agregações
    ↓
Relatório
    ↓
Encerramento com código 0
```

Resultados principais:

```text
Linux
2805 pacotes capturados
2805 pacotes persistidos
exit code 0

Windows + Docker Desktop
409 pacotes capturados
409 pacotes persistidos
exit code 0

Testes automatizados
21/21 passed
```

A validação demonstra que a aplicação pode ser executada a partir de um clone limpo utilizando o fluxo documentado no README.

Em Windows e outros ambientes virtualizados, a principal consideração adicional é a visibilidade da rede disponibilizada pelo runtime de containers.
