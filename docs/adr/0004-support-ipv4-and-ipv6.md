# ADR 0004: Suportar IPv4 e IPv6

- **Status:** Aceito
- **Data:** 2026-08-17

## Contexto

Interfaces de rede modernas podem transportar simultaneamente tráfego IPv4 e IPv6.

Limitar a captura a IPv4 poderia produzir uma visão incompleta do tráfego real observado na interface.

Durante os testes funcionais, ambos os tipos de endereço foram observados.

## Decisão

Normalizar e persistir pacotes IPv4 e IPv6.

Ambos utilizam a mesma representação:

```text
PacketRecord
├── source_ip
├── destination_ip
├── protocol
└── packet_size
```

Os endereços são armazenados como texto no banco.

## Justificativa

A representação textual permite armazenar IPv4 e IPv6 utilizando o mesmo schema, mantendo a solução simples.

Protocolos conhecidos são normalizados para nomes legíveis:

```text
TCP
UDP
ICMP
ICMPv6
```

Quando um protocolo IP não possui tratamento específico, seu identificador numérico é preservado.

## Consequências

### Benefícios

- visão mais completa do tráfego;
- mesmo modelo para IPv4 e IPv6;
- nenhuma necessidade de schemas separados;
- compatibilidade com redes dual-stack.

### Trade-offs

- identificação de protocolos IPv6 possui particularidades adicionais;
- endereços armazenados como texto não são otimizados para todos os tipos possíveis de consulta em grande escala.

## Validação

Existem testes automatizados específicos para:

- IPv4;
- IPv6;
- ICMP;
- ICMPv6.

A captura funcional também confirmou tráfego IPv4 e IPv6 em uma interface real.

## Quando revisitar

Caso o sistema evolua para análises de rede em grande escala, pode ser necessário reavaliar a representação dos endereços para otimizar armazenamento, indexação ou consultas especializadas.
