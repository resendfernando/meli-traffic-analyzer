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

## 6. Validação Docker

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

---

## 7. Validação funcional com tráfego real

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

---

## 8. Reconciliação

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

---

## 9. Validação do resultado

Além de capturar e armazenar, o teste funcional verifica a presença de:

```text
Total packets
Packets by protocol
Top 5 source IPs
Top 5 destination IPs
```

Assim, validamos o fluxo completo e não apenas componentes isolados.

---

## 10. O que os testes automatizados não provam

Testes unitários não garantem:

- que a interface existe;
- que o host permite captura;
- que Docker possui as permissões corretas;
- que existe tráfego na interface;
- que a imagem utilizada contém o código mais recente.

Por isso testes automatizados e validação funcional são complementares.

---

## 11. Pirâmide utilizada

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

---

## 12. Critério de aprovação

Uma versão está pronta para entrega quando:

- todos os testes automatizados passam;
- a imagem Docker é construída;
- a CLI inicia;
- uma interface real pode ser capturada;
- dados são persistidos;
- `captured == stored`;
- o relatório é apresentado;
- o banco permanece disponível após o container terminar.

---

## 13. Estratégia para regressões

Quando um bug for identificado:

```text
Bug discovered
      ↓
Reproduce
      ↓
Create regression test
      ↓
Fix
      ↓
Run full suite
      ↓
Functional validation when required
```

A correção não deve depender apenas de conhecimento informal sobre o incidente.

Sempre que viável, o comportamento esperado deve permanecer registrado em um teste.

---

## 14. Próximos níveis de teste

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

Esses testes devem ser introduzidos conforme os requisitos operacionais evoluírem.

---

## 15. Princípio

O objetivo da estratégia não é maximizar a quantidade de testes.

É maximizar confiança sobre os comportamentos que importam.

```text
Test behavior
      +
Test boundaries
      +
Test integration
      +
Validate reality
      =
Confidence
```
