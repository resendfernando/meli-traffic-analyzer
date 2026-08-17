# AI-Assisted Infrastructure Log Analysis

A proposta utiliza IA onde sua capacidade de interpretação agrega maior
valor: **correlacionar eventos, priorizar problemas e transformar sinais
técnicos em próximos passos acionáveis**.

O desenho também considera confiabilidade, FinOps, segurança, governança
e mensuração de resultados, permitindo que uma solução inicialmente
simples evolua de forma controlada para um cenário produtivo e
escalável.

## Visão da solução

O prompt abaixo foi desenvolvido especificamente para transformar logs
brutos de infraestrutura em um **diagnóstico curto, priorizado e
acionável**, evitando que a IA apenas descreva cada linha do log.

Sua construção considera quatro objetivos principais:

-   **Foco operacional:** identificar e priorizar os eventos que
    realmente demandam investigação ou ação, agrupando mensagens
    relacionadas em um mesmo incidente.
-   **Confiabilidade:** separar explicitamente evidências observadas de
    hipóteses, evitando inferências sem suporte no log e reduzindo o
    risco de alucinações.
-   **Eficiência e FinOps:** limitar análises redundantes, agrupar
    eventos repetidos e restringir o tamanho da resposta, reduzindo
    consumo desnecessário de tokens e tornando o uso do modelo mais
    viável em escala.
-   **Tomada de decisão:** apresentar severidade, impacto e próximos
    passos em ordem de prioridade, reduzindo o esforço necessário para
    transformar sinais técnicos em ações.

O objetivo não é fazer a IA explicar todo o log, mas responder às
perguntas mais importantes para a operação:

> **O que aconteceu? Qual o impacto? O que pode estar relacionado? E o
> que deve ser investigado primeiro?**

------------------------------------------------------------------------

## 1. Prompt proposto

Você é um **Analista Sênior de Infraestrutura**, especializado em
troubleshooting, redes e análise de incidentes.

Analise exclusivamente os eventos contidos entre `<LOG></LOG>`.

### Objetivo

Transformar o log em um diagnóstico **curto, priorizado e acionável**,
identificando falhas, erros, comportamentos anômalos e possíveis riscos
de segurança.

### 1.1 Foco operacional

-   Identifique somente eventos relevantes para falha, degradação,
    indisponibilidade ou segurança.
-   Considere timestamp, severidade, recurso afetado e sequência
    temporal.
-   Agrupe mensagens relacionadas em um único incidente.
-   Não explique individualmente mensagens normais ou repetitivas quando
    elas não agregarem informação ao diagnóstico.
-   Priorize eventos que demandam investigação ou ação humana.

### 1.2 Confiabilidade

-   Diferencie claramente **EVIDÊNCIA** de **HIPÓTESE**.
-   Evidência deve conter somente informações diretamente suportadas
    pelo log.
-   Não invente informações ausentes.
-   Correlação temporal não significa necessariamente causalidade.
-   Se não houver informações suficientes para determinar uma causa,
    informe: **"Evidência insuficiente para determinar a causa."**
-   Eventos administrativos ou de segurança devem ser destacados, mas
    não classificados como maliciosos sem evidências suficientes.

### 1.3 Eficiência

-   Seja objetivo.
-   Elimine explicações redundantes.
-   Agrupe eventos pertencentes ao mesmo incidente.
-   Não reproduza o log integralmente na resposta.
-   Limite o resumo executivo a 5 linhas.
-   Liste no máximo 5 ações recomendadas.

### 1.4 Priorização

Classifique os incidentes como:

-   **CRÍTICO:** indisponibilidade grave ou risco elevado de segurança.
-   **ALTO:** falha relevante que exige investigação.
-   **MÉDIO:** comportamento anormal que merece atenção.
-   **BAIXO:** evento de baixo impacto.

Ordene os incidentes por **impacto e urgência**, e não apenas pela ordem
em que aparecem no log.

### Formato da resposta

#### Resumo executivo

Em no máximo 5 linhas, informe: - principal problema; - recurso
afetado; - impacto provável; - prioridade de investigação.

#### Incidentes

Para cada incidente relevante:

**\[SEVERIDADE\] Nome do incidente**

-   **Timestamp:**
-   **Recurso:**
-   **Evidência:**
-   **Hipótese:**
-   **Impacto:**
-   **Ação recomendada:**

#### Correlação

Informe somente relações relevantes entre os eventos.

Quando houver apenas proximidade temporal sem evidência suficiente de
causalidade, deixe isso explícito.

#### Próximas ações

Liste no máximo **5 ações**, ordenadas por impacto e urgência.

``` text
<LOG>
COLE O LOG BRUTO AQUI
</LOG>
```

------------------------------------------------------------------------

## 2. Log de exemplo

``` text
May 16 14:01:22.123: %LINK-3-UPDOWN: Interface GigabitEthernet1/0/1, changed state to down
May 16 14:01:22.125: %LINEPROTO-5-UPDOWN: Line protocol on Interface GigabitEthernet1/0/1, changed state to down
May 16 14:01:23.101: %SPANTREE-5-TOPO_CHANGE: Topology Change Notice received on VLAN0010
May 16 14:01:23.105: %SPANTREE-6-PORTSTATE: Port Gi1/0/3 state changed from FORWARDING to BLOCKING
May 16 14:01:24.001: %SPANTREE-6-PORTSTATE: Port Gi1/0/4 state changed from BLOCKING to LISTENING
May 16 14:01:26.003: %SPANTREE-6-PORTSTATE: Port Gi1/0/4 state changed from LISTENING to LEARNING
May 16 14:01:28.005: %SPANTREE-6-PORTSTATE: Port Gi1/0/4 state changed from LEARNING to FORWARDING
May 16 14:01:28.006: %SPANTREE-5-ROOTCHANGE: Root changed for VLAN0010
New root is 00e0.b6ff.ee11, cost is 19, port Gi1/0/4
May 16 14:01:30.000: %CDP-4-DUPLEX_MISMATCH: duplex mismatch discovered on GigabitEthernet1/0/2 (full), with SW-Backup GigabitEthernet0/1 (half).
May 16 14:01:32.500: %PORT_SECURITY-2-PSECURE_VIOLATION: Security violation occurred on interface GigabitEthernet1/0/5
May 16 14:01:35.500: %SYS-5-CONFIG_I: Configured from console by vty0 (192.168.1.5)
```

------------------------------------------------------------------------

## 3. Resposta esperada da IA

### Resumo executivo

Foi identificada queda da interface **Gi1/0/1**, seguida por
reconvergência do Spanning Tree na VLAN 10 e mudança do root bridge.
Também há um **duplex mismatch** na Gi1/0/2, uma **violação de Port
Security** na Gi1/0/5 e uma alteração administrativa via VTY. A
prioridade é investigar a queda da Gi1/0/1 e validar se a nova topologia
STP é esperada.

### \[ALTO\] Queda de interface e alteração da topologia STP

-   **Timestamp:** 14:01:22--14:01:28
-   **Recurso:** Gi1/0/1, Gi1/0/3, Gi1/0/4 e VLAN 10
-   **Evidência:** Gi1/0/1 mudou para down; em seguida houve Topology
    Change, alteração dos estados STP e mudança do root bridge.
-   **Hipótese:** a perda da Gi1/0/1 pode ter provocado ou contribuído
    para a reconvergência. A topologia precisa ser validada para
    confirmar causalidade.
-   **Impacto:** possível perda temporária de conectividade e alteração
    do caminho utilizado pelo tráfego.
-   **Ação recomendada:** investigar a causa da queda da Gi1/0/1 e
    confirmar se `00e0.b6ff.ee11` é o root bridge esperado.

### \[ALTO\] Violação de Port Security

-   **Timestamp:** 14:01:32
-   **Recurso:** Gi1/0/5
-   **Evidência:** registro `PSECURE_VIOLATION`.
-   **Hipótese:** dispositivo/MAC não autorizado, limite de MACs
    excedido ou alteração legítima ainda não refletida na configuração.
-   **Impacto:** dependendo da política configurada, pode ocorrer
    bloqueio de tráfego ou proteção/shutdown da porta.
-   **Ação recomendada:** identificar os MAC addresses observados e
    validar o dispositivo conectado antes de alterar a política.

### \[MÉDIO\] Duplex mismatch

-   **Timestamp:** 14:01:30
-   **Recurso:** Gi1/0/2 ↔ SW-Backup Gi0/1
-   **Evidência:** uma extremidade opera em full duplex e a outra em
    half duplex.
-   **Hipótese:** configuração incompatível ou problema de
    autonegociação.
-   **Impacto:** degradação de desempenho, colisões, retransmissões ou
    perda de pacotes.
-   **Ação recomendada:** validar e padronizar speed/duplex nas duas
    extremidades.

### \[MÉDIO\] Alteração administrativa

-   **Timestamp:** 14:01:35
-   **Recurso:** equipamento analisado / sessão VTY
-   **Evidência:** alteração de configuração originada de `192.168.1.5`.
-   **Hipótese:** atividade administrativa legítima ou alteração que
    requer auditoria. O log não informa usuário nem comandos executados.
-   **Impacto:** indeterminado com os dados disponíveis.
-   **Ação recomendada:** correlacionar com AAA/TACACS+/RADIUS,
    histórico de configuração e change management.

### Correlação

A sequência **Gi1/0/1 down → Topology Change → alteração de estados STP
→ Root Change** apresenta forte correlação temporal e pode representar
um único incidente.

O duplex mismatch e a violação de Port Security parecem eventos
independentes com as evidências disponíveis.

A alteração via VTY deve ser auditada, mas ocorreu após os principais
eventos e **não há evidência suficiente para atribuir a ela a causa do
incidente**.

### Próximas ações

1.  Investigar a causa da queda da Gi1/0/1.
2.  Confirmar se o novo root bridge da VLAN 10 é esperado.
3.  Investigar a violação de Port Security na Gi1/0/5.
4.  Corrigir o duplex mismatch da Gi1/0/2.
5.  Auditar a alteração administrativa originada de 192.168.1.5.

------------------------------------------------------------------------

## 4. Decisões de design do prompt

  -----------------------------------------------------------------------
  Decisão                             Objetivo
  ----------------------------------- -----------------------------------
  Agrupar eventos relacionados        Reduzir ruído, redundância e
                                      consumo de tokens

  Separar evidência de hipótese       Reduzir alucinações e tornar a
                                      análise auditável

  Não assumir causalidade             Evitar conclusões incorretas
                                      baseadas apenas em proximidade
                                      temporal

  Limitar resumo e ações              Manter a resposta objetiva e
                                      controlar tokens de saída

  Priorizar por impacto e urgência    Apoiar tomada de decisão
                                      operacional

  Não reproduzir o log                Evitar consumo desnecessário de
                                      tokens

  Destacar sem acusar eventos         Melhorar segurança sem gerar falsos
  administrativos                     positivos
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 5. Considerações para uso em produção

O prompt atende ao cenário solicitado, no qual um trecho de log é
fornecido diretamente à IA. Em um ambiente corporativo com grandes
volumes, porém, **não seria eficiente nem economicamente adequado enviar
todos os logs brutos diretamente para um LLM**.

Uma evolução da solução deveria considerar:

-   **Pré-processamento:** parsing, normalização, filtros, regras e
    deduplicação antes da IA.
-   **FinOps:** acompanhar tokens, custo por análise e custo por
    incidente corretamente identificado; utilizar modelos mais avançados
    somente quando a complexidade justificar.
-   **Segurança e governança:** classificar e, quando necessário,
    mascarar credenciais, tokens, dados pessoais e informações internas
    antes do envio ao modelo.
-   **Confiabilidade:** manter evidências separadas de hipóteses e
    exigir validação humana para decisões de maior impacto.
-   **Observabilidade:** medir precisão, falsos positivos/negativos,
    latência, custo e impacto em MTTA/MTTR.
-   **Escalabilidade:** utilizar processamento determinístico para
    tarefas simples e de alto volume, reservando o LLM para correlação,
    contexto e interpretação.

Fluxo conceitual:

``` text
Logs
  ↓
Parsing / Normalização
  ↓
Filtros / Regras / Deduplicação
  ↓
Eventos relevantes
  ↓
IA — Correlação / Priorização / Diagnóstico
  ↓
Recomendação acionável
  ↓
Validação humana
```

A implementação pode começar com um **PoC controlado**, evoluir para um
**piloto com métricas** e chegar à produção somente quando qualidade,
ganho operacional, custo e risco justificarem a escala.

------------------------------------------------------------------------

## 6. Métricas de sucesso

A solução deve ser avaliada pelo resultado operacional, e não apenas
pela capacidade do modelo de produzir uma análise tecnicamente correta.

Indicadores recomendados:

-   MTTA (Mean Time to Acknowledge);
-   MTTR (Mean Time to Resolve);
-   precisão das classificações;
-   falsos positivos e falsos negativos;
-   tokens por análise;
-   custo por análise;
-   **custo por incidente corretamente identificado**;
-   percentual de casos escalados para análise humana;
-   horas de triagem manual economizadas.

A pergunta final para decisão de escala deve ser:

> **A utilização da IA melhorou a operação o suficiente para justificar
> o custo, o risco e a complexidade adicionais?**

------------------------------------------------------------------------

## 7. Documentação como ativo reutilizável

Além de servir como entrega técnica, este documento pode ser mantido
como **base de conhecimento operacional**.

Em um cenário corporativo, a mesma documentação pode ser:

-   compartilhada diretamente com times de Infraestrutura, NOC, SRE,
    Service Desk ou Segurança;
-   publicada em uma plataforma interna de knowledge management;
-   versionada junto ao código e aos processos operacionais;
-   utilizada como referência para troubleshooting e treinamento;
-   indexada futuramente por mecanismos de busca semântica ou soluções
    de RAG.

Caso a organização evolua para um **agente interno de suporte ou
operações**, essa base de conhecimento pode ser disponibilizada como
fonte autorizada. Assim, ao receber uma dúvida ou identificar um
contexto relacionado, o agente poderá **localizar e recomendar a
documentação relevante ao colaborador**, mantendo a resposta vinculada a
conteúdo interno validado e versionado.

Nesse modelo, o documento deixa de ser apenas uma resposta pontual ao
desafio e passa a representar um **ativo de conhecimento reutilizável,
pesquisável e preparado para integração com futuras soluções de IA**.

------------------------------------------------------------------------


