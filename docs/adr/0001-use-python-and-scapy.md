# ADR 0001: Utilizar Python e Scapy para captura de pacotes

- **Status:** Aceito
- **Data:** 2026-08-17

## Contexto

A aplicação precisa capturar pacotes de uma interface de rede especificada e extrair:

- endereço IP de origem;
- endereço IP de destino;
- protocolo;
- tamanho do pacote.

A solução também precisa permanecer simples, testável e fácil de ser compreendida e operada por outra pessoa.

## Decisão

Utilizar Python como linguagem da aplicação e Scapy como biblioteca de captura e interpretação de pacotes.

A dependência do Scapy é isolada do restante da aplicação por meio de uma representação interna chamada `PacketRecord`.

```text
Interface de rede
       ↓
     Scapy
       ↓
normalize_packet()
       ↓
 PacketRecord
       ↓
   Aplicação
```

## Justificativa

O Scapy fornece abstrações maduras para captura e interpretação de pacotes, permitindo concentrar a implementação na lógica do problema.

Python também oferece um ecossistema adequado para:

- testes automatizados;
- integração com SQLite;
- desenvolvimento de CLI;
- automação;
- containerização.

A utilização do `PacketRecord` evita que persistência, relatórios e demais componentes dependam diretamente da estrutura interna dos objetos do Scapy.

## Alternativas consideradas

### Raw sockets

Ofereceriam maior controle em baixo nível, porém aumentariam significativamente a complexidade da implementação sem benefício proporcional para os requisitos atuais.

### tcpdump via subprocess

Ofereceria captura confiável, mas exigiria interpretação da saída de um processo externo e aumentaria o acoplamento com ferramentas do sistema operacional.

### PyShark

Oferece recursos avançados por meio do Wireshark/TShark, porém introduziria dependências adicionais desnecessárias para os campos exigidos pelo desafio.

## Consequências

### Benefícios

- implementação compacta;
- processamento legível;
- facilidade para criação de testes;
- suporte a IPv4 e IPv6;
- menor acoplamento por meio da normalização.

### Trade-offs

- dependência do Scapy;
- necessidade de permissões específicas para captura;
- cenários de throughput muito elevado podem exigir outra estratégia de captura.

## Quando revisitar

Esta decisão deve ser reavaliada caso medições demonstrem que a capacidade de captura se tornou um gargalo ou novos requisitos dependam de funcionalidades melhor atendidas por outra tecnologia.
