# ADR 0005: Utilizar host networking para captura no Docker

- **Status:** Aceito para o escopo atual
- **Data:** 2026-08-17

## Contexto

A aplicação precisa executar dentro de um container Docker e, ao mesmo tempo, capturar pacotes de uma interface de rede existente no host Linux.

O isolamento de rede padrão do Docker faria com que o container enxergasse principalmente suas próprias interfaces virtuais, e não necessariamente a interface física que precisa ser analisada.

## Decisão

Utilizar:

```yaml
network_mode: host
```

para o cenário atual.

Também são concedidas capabilities específicas necessárias à captura:

```yaml
cap_add:
  - NET_RAW
  - NET_ADMIN
```

## Justificativa

Host networking fornece acesso direto às interfaces do host Linux e mantém a configuração do laboratório simples e reproduzível.

Capabilities específicas são utilizadas em vez de executar o container com privilégios irrestritos.

```text
Preferido:
NET_RAW + NET_ADMIN

Evitar sem necessidade:
--privileged
```

## Consequências

### Benefícios

- acesso às interfaces reais do host;
- configuração simples para o desafio;
- execução reproduzível via Docker;
- privilégios mais explícitos do que `--privileged`.

### Trade-offs

- menor isolamento de rede;
- dependência de características do host Linux;
- permissões de captura aumentam a superfície de segurança.

## Consideração de segurança

Captura de pacotes é uma operação privilegiada.

Em um ambiente produtivo, as permissões devem seguir o princípio de menor privilégio e ser revisadas especificamente para a plataforma de execução.

## Quando revisitar

Reavaliar esta decisão antes de uma implantação produtiva ou quando:

- o modelo de deployment mudar;
- requisitos de isolamento aumentarem;
- a plataforma não utilizar Linux;
- existir uma alternativa com menor privilégio que satisfaça a necessidade de captura.
