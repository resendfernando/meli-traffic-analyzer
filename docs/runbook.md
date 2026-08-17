# Runbook — Traffic Analyzer

## 1. Objetivo

Este runbook descreve os procedimentos necessários para configurar, executar, validar e diagnosticar o Traffic Analyzer.

O objetivo é permitir que uma pessoa opere a aplicação sem precisar conhecer sua implementação interna.

---

## 2. Pré-requisitos

Ambiente recomendado:

- Linux
- Docker
- Docker Compose
- interface de rede ativa

Para desenvolvimento e execução dos testes:

- Python 3.12+
- virtual environment (`venv`)
- dependências presentes em `requirements.txt`

---

## 3. Verificar o ambiente

### Docker

```bash
docker --version
```

### Docker Compose

```bash
docker compose version
```

### Python

```bash
python3 --version
```

---

## 4. Identificar a interface de rede

Execute:

```bash
ip -br addr
```

Exemplo:

```text
lo          UNKNOWN    127.0.0.1/8
enp2s0      DOWN
wlp0s20f3   UP         192.168.100.223/24
```

Neste exemplo:

```text
wlp0s20f3
```

é a interface Wi-Fi ativa.

O nome da interface pode ser diferente em cada máquina.

---

## 5. Configurar a interface

A interface utilizada pelo container deve corresponder a uma interface existente no host.

Consulte a configuração atual:

```bash
cat compose.yaml
```

Confirme o valor fornecido ao argumento:

```text
--interface
```

Caso necessário, altere o arquivo:

```bash
nano compose.yaml
```

---

## 6. Construir a imagem

Execute:

```bash
docker compose build
```

Resultado esperado:

```text
traffic-analyzer  Built
```

---

## 7. Reconstrução completa

Quando houver alteração no código e existir dúvida se a imagem contém a versão mais recente:

```bash
docker compose build --no-cache
```

Isso evita executar uma imagem criada anteriormente.

---

## 8. Validar a CLI

Antes da captura:

```bash
docker compose run --rm traffic-analyzer --help
```

A saída deve apresentar argumentos semelhantes a:

```text
--interface INTERFACE
--database DATABASE
--verbose
--count COUNT
--duration DURATION
```

Esse teste também é útil para confirmar que a imagem Docker contém a versão esperada da aplicação.

---

## 9. Executar uma captura

Com a interface configurada:

```bash
docker compose run --rm traffic-analyzer
```

Por padrão, a aplicação realiza uma captura de 30 segundos.

Exemplo:

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
  ...

Top 5 destination IPs by traffic volume:
  ...
```

---

## 10. Critério básico de sucesso

Ao final da execução, compare:

```text
Packets captured this run
```

com:

```text
Packets stored this run
```

Em uma execução normal, espera-se:

```text
captured == stored
```

Exemplo:

```text
Packets captured this run: 243
Packets stored this run: 243
```

Também deve ser gerado o relatório da captura.

---

## 11. Gerar tráfego controlado para teste

Durante uma captura, abra outro terminal.

### ICMP

```bash
ping -c 4 8.8.8.8
```

### DNS

```bash
nslookup mercadolivre.com 8.8.8.8
```

### HTTP/HTTPS

```bash
curl -4 https://www.google.com > /dev/null
```

Esses comandos ajudam a gerar diferentes tipos de tráfego durante uma validação funcional.

---

## 12. Captura por duração

Exemplo de captura durante 60 segundos:

```bash
docker compose run --rm traffic-analyzer \
  --interface wlp0s20f3 \
  --duration 60 \
  --database /app/data/traffic.db
```

---

## 13. Captura por quantidade

Exemplo:

```bash
docker compose run --rm traffic-analyzer \
  --interface wlp0s20f3 \
  --count 100 \
  --database /app/data/traffic.db
```

A execução termina quando a quantidade configurada é atingida.

`--count` e `--duration` não devem ser utilizados simultaneamente.

---

## 14. Modo verbose

Para diagnóstico, é possível visualizar os registros normalizados durante a captura:

```bash
docker compose run --rm traffic-analyzer \
  --interface wlp0s20f3 \
  --duration 30 \
  --verbose
```

O modo verbose não é necessário para a operação normal.

---

## 15. Verificar o banco

O banco padrão no host é:

```text
data/traffic.db
```

Verifique:

```bash
ls -lh data/
```

---

## 16. Contar registros

```bash
sqlite3 data/traffic.db \
"SELECT COUNT(*) FROM packets;"
```

---

## 17. Verificar os últimos pacotes

```bash
sqlite3 data/traffic.db \
"SELECT
    id,
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

## 18. Verificar protocolos

```bash
sqlite3 data/traffic.db \
"SELECT
    protocol,
    COUNT(*) AS packet_count,
    SUM(packet_size) AS total_bytes
 FROM packets
 GROUP BY protocol
 ORDER BY packet_count DESC;"
```

---

## 19. Gerar relatório histórico

Para analisar todos os registros existentes no banco:

```bash
python -m app.report --database data/traffic.db
```

Esse relatório considera o histórico completo.

O relatório apresentado automaticamente pelo sniffer ao final da captura considera apenas os pacotes daquela execução.

---

## 20. Executar testes automatizados

Ative o ambiente virtual:

```bash
source .venv/bin/activate
```

Execute:

```bash
pytest -v
```

Todos os testes devem passar antes da entrega de uma nova versão.

---

# Troubleshooting

## 21. Interface não encontrada

### Sintoma

A aplicação informa:

```text
ERROR: Interface 'xxx' was not found.
```

### Diagnóstico

Execute:

```bash
ip -br addr
```

Compare as interfaces disponíveis com a configuração utilizada pela aplicação.

### Correção

Informe uma interface válida.

---

## 22. Interface existe no host, mas não no container

Verifique a configuração de rede:

```bash
cat compose.yaml
```

Para a arquitetura atual, confirme:

```yaml
network_mode: host
```

Depois valide novamente:

```bash
docker compose run --rm traffic-analyzer --help
```

---

## 23. Erro de permissão durante a captura

### Sintoma

A aplicação não consegue abrir a interface para captura.

### Verificação

Confirme no `compose.yaml`:

```yaml
cap_add:
  - NET_RAW
  - NET_ADMIN
```

Essas capabilities fornecem as permissões necessárias para a captura no cenário utilizado pela aplicação.

Evite substituir essa configuração por:

```text
--privileged
```

sem uma necessidade específica, pois isso concederia privilégios significativamente maiores ao container.

---

## 24. Container executando código antigo

### Sintoma

O comportamento observado não corresponde ao código presente no projeto.

Por exemplo:

- um novo argumento não aparece no `--help`;
- uma alteração de saída não aparece;
- comportamento removido continua acontecendo.

### Correção

Reconstrua:

```bash
docker compose build --no-cache
```

Depois valide:

```bash
docker compose run --rm traffic-analyzer --help
```

Somente depois execute novamente a captura.

---

## 25. Banco não aparece no host

Verifique:

```bash
ls -lah data/
```

Depois consulte:

```bash
cat compose.yaml
```

Confirme que existe um volume equivalente a:

```yaml
volumes:
  - ./data:/app/data
```

O caminho utilizado pela aplicação dentro do container deve estar dentro de `/app/data`.

---

## 26. Nenhum pacote capturado

Primeiro confirme que a interface está ativa:

```bash
ip -br addr
```

Depois gere tráfego:

```bash
ping -c 4 8.8.8.8
```

Se necessário, valide a captura fora da aplicação utilizando uma ferramenta disponível no sistema, como `tcpdump`.

Exemplo:

```bash
sudo tcpdump -i wlp0s20f3 -c 10
```

### Interpretação

Se nenhuma ferramenta consegue capturar:

```text
problema provavelmente está no ambiente/interface/permissão
```

Se outra ferramenta captura, mas a aplicação não:

```text
investigar configuração da aplicação/container/filtro
```

Essa separação ajuda a evitar investigação desnecessária no código quando o problema está em uma camada inferior.

---

## 27. Pacotes capturados diferentes dos armazenados

### Sintoma

Exemplo:

```text
Packets captured this run: 200
Packets stored this run: 180
```

### Resultado esperado

```text
Packets captured this run == Packets stored this run
```

### Diagnóstico

1. Execute novamente com `--verbose`.
2. Verifique erros no terminal.
3. Confirme espaço disponível em disco.
4. Valide o arquivo SQLite.
5. Execute os testes automatizados.

Teste:

```bash
pytest -v
```

Banco:

```bash
sqlite3 data/traffic.db "PRAGMA integrity_check;"
```

Resultado esperado:

```text
ok
```

---

## 28. Banco SQLite corrompido

Execute:

```bash
sqlite3 data/traffic.db "PRAGMA integrity_check;"
```

Se o resultado não for:

```text
ok
```

preserve o arquivo antes de qualquer ação:

```bash
cp data/traffic.db data/traffic.db.backup
```

Para uma captura de laboratório descartável, um novo banco pode ser criado removendo o arquivo antigo.

Não remova um banco que contenha informações necessárias para investigação sem antes preservar os dados.

---

## 29. Começar um teste com banco vazio

Para um teste controlado em que o histórico não seja necessário:

```bash
rm -f data/traffic.db
```

A aplicação recriará automaticamente o schema na próxima execução.

Esse procedimento deve ser utilizado somente quando os dados anteriores puderem ser descartados.

---

## 30. Estatísticas inesperadas

Primeiro determine se está sendo analisada:

```text
captura atual
```

ou:

```text
base histórica completa
```

O resumo apresentado automaticamente após uma captura considera apenas a execução atual.

O comando:

```bash
python -m app.report --database data/traffic.db
```

considera todo o banco.

Essa diferença é intencional.

---

## 31. Top 5 diferente da quantidade de pacotes

Os rankings são ordenados por:

```text
total de bytes
```

e não apenas por quantidade de pacotes.

Portanto, um IP com menos pacotes pode aparecer acima de outro caso tenha movimentado maior volume de dados.

A quantidade de pacotes é exibida como informação complementar.

---

## 32. Diagnóstico em camadas

Durante um incidente, recomenda-se investigar na seguinte ordem:

```text
1. Host
   |
2. Interface
   |
3. Network traffic
   |
4. Docker
   |
5. Permissions
   |
6. Application
   |
7. Database
   |
8. Statistics
```

### Host

A máquina está funcionando normalmente?

### Interface

A interface existe e está UP?

```bash
ip -br addr
```

### Network traffic

Existe tráfego chegando à interface?

```bash
ping -c 4 8.8.8.8
```

ou, quando disponível:

```bash
sudo tcpdump -i <interface> -c 10
```

### Docker

A imagem está atualizada?

```bash
docker compose build
```

### Permissions

As capabilities estão configuradas?

### Application

Os testes passam?

```bash
pytest -v
```

### Database

O SQLite está íntegro?

```bash
sqlite3 data/traffic.db "PRAGMA integrity_check;"
```

### Statistics

O relatório está analisando o escopo esperado?

Essa abordagem reduz o tempo gasto investigando uma camada que não é responsável pela falha.

---

## 33. Procedimento de validação antes da entrega

### Etapa 1 — Testes

```bash
pytest -v
```

Resultado esperado:

```text
all tests passed
```

### Etapa 2 — Build limpo

```bash
docker compose build --no-cache
```

### Etapa 3 — CLI

```bash
docker compose run --rm traffic-analyzer --help
```

### Etapa 4 — Banco limpo para teste

Quando os dados existentes puderem ser descartados:

```bash
rm -f data/traffic.db
```

### Etapa 5 — Captura

```bash
docker compose run --rm traffic-analyzer
```

### Etapa 6 — Gerar tráfego

Em outro terminal:

```bash
ping -c 4 8.8.8.8
```

```bash
nslookup mercadolivre.com 8.8.8.8
```

```bash
curl -4 https://www.google.com > /dev/null
```

### Etapa 7 — Validar resultado

Confirmar:

```text
captured == stored
```

Confirmar também a presença de:

```text
Total packets
Packets by protocol
Top 5 source IPs by traffic volume
Top 5 destination IPs by traffic volume
```

### Etapa 8 — Validar persistência

```bash
sqlite3 data/traffic.db "SELECT COUNT(*) FROM packets;"
```

---

## 34. Informações para escalonamento

Caso outra pessoa precise assumir uma investigação, compartilhar pelo menos:

```text
Operating system:
Docker version:
Docker Compose version:
Application commit:
Network interface:
Capture mode:
Capture duration/count:
Packets captured:
Packets stored:
Error message:
Tests result:
Database integrity:
```

Para identificar o commit:

```bash
git rev-parse --short HEAD
```

Para consultar o status:

```bash
git status
```

Essas informações ajudam a reproduzir o mesmo cenário e reduzem dependência de comunicação informal.

---

## 35. Critério de encerramento de incidente

Um problema operacional pode ser considerado resolvido quando:

1. a causa foi identificada;
2. a aplicação voltou a capturar;
3. os pacotes estão sendo persistidos;
4. `captured == stored`;
5. o relatório é gerado corretamente;
6. os testes continuam passando;
7. a correção necessária foi documentada quando aplicável.

O objetivo não é apenas restaurar a execução, mas deixar informação suficiente para que o mesmo problema possa ser diagnosticado mais rapidamente no futuro.
