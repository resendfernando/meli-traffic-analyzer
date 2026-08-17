# ADR 0006: Isolar a captura atual do histórico

- **Status:** Aceito
- **Data:** 2026-08-17

## Contexto

O banco SQLite persiste dados entre diferentes execuções.

Isso cria dois conjuntos de informação:

```text
Histórico existente
+
Nova captura
```

Se o relatório apresentado ao final de uma execução consultasse todo o banco, os resultados não representariam exclusivamente o tráfego recém-capturado.

Exemplo:

```text
Banco antes da captura
IDs 1 ... 500

Nova execução
IDs 501 ... 743
```

O operador espera que o resumo da nova execução represente os registros 501 a 743.

## Decisão

Antes de iniciar a captura, registrar o maior `id` existente no banco.

```text
start_id = último ID existente
```

As consultas utilizadas no resumo da execução aplicam:

```sql
WHERE id > start_id
```

O relatório histórico executado separadamente continua analisando todo o banco.

## Justificativa

A solução diferencia explicitamente:

```text
Current Capture Summary
        ↓
O que aconteceu nesta execução?

Historical Report
        ↓
O que existe no banco?
```

Isso evita misturar dois contextos analíticos diferentes.

## Alternativas consideradas

### Limpar o banco antes de cada captura

Simplificaria o relatório, mas destruiria o histórico e reduziria o valor da persistência.

### Criar um banco por execução

Forneceria isolamento forte, porém aumentaria a gestão de arquivos e dificultaria consultas históricas consolidadas.

### Utilizar apenas timestamp

Seria possível, porém o identificador sequencial fornece uma fronteira simples e determinística para o modelo atual.

## Consequências

### Benefícios

- preserva histórico;
- relatório da execução permanece correto;
- não exige novo schema;
- implementação simples;
- análise histórica continua disponível.

### Trade-offs

A estratégia depende da característica sequencial do identificador utilizado pelo modelo atual.

Em uma arquitetura distribuída, essa estratégia provavelmente precisaria ser substituída.

## Validação

O comportamento é coberto por testes automatizados que inserem registros anteriores e posteriores ao ponto inicial da captura.

O relatório deve retornar somente os registros pertencentes ao escopo solicitado.

## Quando revisitar

Se múltiplos coletores passarem a escrever simultaneamente ou houver necessidade de identificar formalmente cada sessão de captura, uma evolução natural seria adicionar:

```text
capture_id
```

ou:

```text
session_id
```

ao modelo.

Isso permitiria tratar cada captura como uma entidade explícita.
