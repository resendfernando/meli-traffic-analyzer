# Testing Strategy

## Objetivo

A estratégia de testes procura responder uma pergunta simples:

> Como sabemos que a solução funciona além de "funcionou na minha máquina"?

A validação foi dividida em camadas.

```text
              Real Traffic
                   ▲
                   │
          Functional Validation
                   ▲
                   │
          Docker Validation
                   ▲
                   │
          CI Validation
                   ▲
                   │
        Persistence / Queries
                   ▲
                   │
             Unit Tests
```

Cada camada reduz um tipo diferente de risco.

---

## 1. Normalização

Pacotes sintéticos são criados com Scapy.

Isso permite testar comportamento determinístico sem depender de tráfego externo.

São validados:

```text
IPv4 + TCP
IPv4 + UDP
IPv4 + ICMP
IPv6
ICMPv6
non-IP traffic
```

O objetivo é garantir que:

```text
Scapy packet
     ↓
normalize_packet()
     ↓
PacketRecord esperado
```

permaneça consistente.

---

## 2. Persistência

Os testes de banco utilizam:

```text
SQLite :memory:
```

Isso permite validar a camada de dados sem arquivos externos.

São testados:

- inicialização do schema;
- inserção;
- campos persistidos;
- múltiplos registros;
- contagem.

---

## 3. Agregações

As consultas que geram as estatísticas são testadas separadamente.

Validamos:

```text
COUNT by protocol
SUM(packet_size)
Top source IPs
Top destination IPs
```

Os dados dos testes são controlados para permitir saber previamente qual resultado deve ocupar cada posição.

---

## 4. Semântica do ranking

Existe um teste específico para evitar uma regressão importante.

Exemplo:

```text
IP A
3 packets × 100 bytes
= 300 bytes

IP B
1 packet × 1000 bytes
= 1000 bytes
```

Resultado esperado:

```text
1. IP B
2. IP A
```

Isso protege a decisão de negócio/técnica de interpretar "mais tráfego" como maior volume em bytes.

---

## 5. Isolamento da captura

Também existe validação para garantir que registros históricos não contaminem o resumo da execução atual.

Cenário:

```text
Existing database
       ↓
Old packet
       ↓
Capture starts
       ↓
New packets
       ↓
Current report
```

Resultado esperado:

```text
Current report = new packets only
```

Esse teste protege uma regra importante que não seria evidente apenas verificando se o SQL executa sem erro.

---

## 6. Validação da CLI e limites de entrada

A interface de linha de comando também faz parte do comportamento da aplicação.

Por isso existem testes específicos para os parâmetros que controlam a captura:

```text
--count
--duration
```

Os testes verificam:

- aceitação de valores inteiros positivos;
- rejeição de zero;
- rejeição de valores negativos;
- rejeição de valores não inteiros.

Exemplos válidos:

```text
--count 10
--duration 30
```

Exemplos rejeitados:

```text
--count 0
--count -1
--duration 0
--duration -1
```

Essa validação impede que entradas semanticamente inválidas sejam encaminhadas para a biblioteca de captura.

Um edge case identificado durante a validação funcional mostrou que:

```text
--count 0
```

poderia resultar em uma captura sem limite, devido à semântica utilizada pela biblioteca subjacente.

O problema foi:

```text
Reproduzido
    ↓
Causa identificada
    ↓
Validação adicionada
    ↓
Teste de regressão criado
    ↓
Suíte completa executada
```

Assim, um comportamento encontrado durante testes exploratórios passou a fazer parte permanente da suíte automatizada.

---

## 7. Suíte automatizada

A solução possui atualmente:

```text
21 automated tests
```

A suíte cobre os principais comportamentos determinísticos da aplicação:

```text
Packet normalization
        +
Persistence
        +
Aggregations
        +
Ranking semantics
        +
Capture isolation
        +
CLI validation
```

A execução local pode ser feita com:

```bash
pytest -q
```

ou utilizando a imagem Docker:

```bash
docker compose run --rm --entrypoint pytest traffic-analyzer -q
```

Resultado esperado:

```text
21 passed
```

---

## 8. Validação Docker

Os testes Python não validam completamente:

- imagem;
- dependências de sistema;
- libpcap;
- network namespace;
- capabilities;
- volume;
- interface real.

Por isso existe uma validação adicional via Docker.

Fluxo:

```text
docker compose build
        ↓
container starts
        ↓
interface accessed
        ↓
packets captured
        ↓
SQLite persisted
        ↓
report generated
```

A construção da imagem também faz parte da validação automatizada no pipeline de CI.

---

## 9. Integração Contínua

O repositório possui um pipeline básico de Continuous Integration utilizando GitHub Actions.

O workflow é executado automaticamente em:

```text
Push → main
Pull Request
```

Atualmente existem dois jobs independentes:

```text
Automated Tests
      +
Docker Build
```

### Automated Tests

O job:

1. realiza checkout do repositório;
2. configura Python 3.12;
3. instala as dependências;
4. executa a suíte com `pytest`.

### Docker Build

O segundo job verifica independentemente se a imagem Docker continua sendo construída com sucesso.

O objetivo da CI neste estágio não é realizar deployment.

O objetivo é fornecer feedback automatizado para duas perguntas fundamentais:

```text
O comportamento esperado continua válido?
                ↓
        Automated Tests

O artefato continua reproduzível?
                ↓
           Docker Build
```

Isso reduz a dependência de validação exclusivamente local e cria uma barreira básica contra regressões.

---

## 10. Validação funcional com tráfego real

Além dos testes automatizados, foi realizada captura real.

Tráfego controlado foi gerado utilizando:

```bash
ping -c 4 8.8.8.8
```

```bash
nslookup mercadolivre.com 8.8.8.8
```

```bash
curl -4 https://www.google.com > /dev/null
```

Isso permitiu observar protocolos como:

```text
ICMP
UDP
TCP
```

em uma interface real.

Também foram executados testes funcionais da CLI utilizando:

- captura por quantidade;
- captura por duração;
- saída `--verbose`;
- banco de dados alternativo;
- interface inexistente;
- argumentos mutuamente exclusivos;
- valores zero e negativos.

---

## 11. Reconciliação

Um dos principais invariantes operacionais é:

```text
captured == stored
```

Em uma validação funcional:

```text
Packets captured this run: 243
Packets stored this run: 243
```

Essa comparação é importante porque uma aplicação poderia capturar corretamente e ainda perder dados durante a persistência.

O invariante foi observado em múltiplas execuções durante a validação funcional.

---

## 12. Validação do resultado

Além de capturar e armazenar, o teste funcional verifica a presença de:

```text
Total packets
Packets by protocol
Top 5 source IPs
Top 5 destination IPs
```

Assim, validamos o fluxo completo e não apenas componentes isolados.

Também foi validado que execuções independentes permanecem persistidas no banco histórico enquanto:

```text
Current Capture Summary
```

continua representando somente a execução atual.

---

## 13. O que os testes automatizados não provam

Mesmo com CI, testes unitários e builds automatizados não garantem:

- que uma interface específica existe no ambiente de execução;
- que o host permite captura;
- que as capabilities necessárias estarão disponíveis em qualquer runtime;
- que existe tráfego na interface;
- que uma carga de produção será suportada;
- que não ocorrerão perdas sob alto volume;
- que o armazenamento disponível será suficiente.

Por isso:

```text
Automated Tests
      +
CI
      +
Docker Validation
      +
Functional Validation
      =
Higher Confidence
```

Nenhuma dessas camadas isoladamente representa garantia completa de comportamento em produção.

---

## 14. Pirâmide utilizada

```text
              /\
             /  \
            /Real\
           /Traffic\
          /--------\
         / Docker   \
        /------------\
       / Integration  \
      /----------------\
     /   Unit Tests     \
    /____________________\
```

A maior parte das regras é validada rapidamente em testes automatizados.

Um número menor de testes valida integração e ambiente real.

A CI executa automaticamente as validações determinísticas e de build, enquanto testes dependentes de interface e tráfego permanecem como validação funcional.

---

## 15. Critério de aprovação

Uma versão está pronta para entrega quando:

- todos os testes automatizados passam;
- o pipeline de CI está verde;
- a imagem Docker é construída;
- a CLI inicia;
- uma interface válida pode ser capturada no ambiente apropriado;
- dados são persistidos;
- `captured == stored`;
- o relatório é apresentado;
- o banco permanece disponível após o container terminar.

Para o estado atual da solução, esses critérios foram validados.

---

## 16. Estratégia para regressões

Quando um bug for identificado:

```text
Bug discovered
      ↓
Reproduce
      ↓
Understand root cause
      ↓
Create regression test
      ↓
Fix
      ↓
Run full suite
      ↓
CI validation
      ↓
Functional validation when required
```

A correção não deve depender apenas de conhecimento informal sobre o incidente.

Sempre que viável, o comportamento esperado deve permanecer registrado em um teste.

A validação de `--count` e `--duration` é um exemplo concreto dessa estratégia aplicada durante o desenvolvimento da solução.

---

## 17. Próximos níveis de teste

Se a solução evoluir para produção, seriam avaliados:

### Performance tests

Determinar:

```text
packets/second
writes/second
latency
drop rate
```

### Soak tests

Executar capturas prolongadas para identificar:

- crescimento de memória;
- crescimento de armazenamento;
- degradação de performance;
- vazamentos de recursos.

### Failure tests

Simular:

- banco indisponível;
- disco cheio;
- perda da interface;
- interrupção do processo;
- container restart.

### Security validation

Revisar:

- capabilities;
- usuário do container;
- acesso aos dados;
- dependências;
- imagem base.

Em uma evolução do pipeline, também poderiam ser adicionadas validações automatizadas como:

```text
Dependency scanning
Container image scanning
Static analysis
Linting
```

Essas verificações devem ser introduzidas conforme risco, criticidade e requisitos operacionais justificarem a complexidade adicional.

---

## 18. Princípio

O objetivo da estratégia não é maximizar a quantidade de testes.

É maximizar confiança sobre os comportamentos que importam.

```text
Test behavior
      +
Test boundaries
      +
Test integration
      +
Automate validation
      +
Validate reality
      =
Confidence
```
