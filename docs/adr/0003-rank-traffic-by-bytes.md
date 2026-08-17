# ADR 0003: Classificar tráfego pelo volume em bytes

- **Status:** Aceito
- **Data:** 2026-08-17

## Contexto

O requisito solicita:

- Top 5 endereços IP de origem com mais tráfego;
- Top 5 endereços IP de destino com mais tráfego.

"Mais tráfego" pode ser interpretado de duas maneiras principais:

1. maior quantidade de pacotes;
2. maior volume de dados transferidos.

Essas métricas podem produzir resultados diferentes.

Exemplo:

```text
IP A → 100 pacotes → 10 KiB
IP B →  20 pacotes → 80 KiB
```

Classificar somente pela quantidade colocaria o IP A em primeiro lugar, embora o IP B tenha movimentado significativamente mais dados.

## Decisão

Utilizar como critério principal:

```sql
SUM(packet_size)
```

A quantidade de pacotes também é exibida como informação complementar.

```text
Volume em bytes      → ranking principal
Quantidade de pacotes → contexto adicional
```

## Justificativa

O volume em bytes representa de maneira mais direta a quantidade de tráfego movimentada por determinado endereço.

Manter também a quantidade de pacotes permite analisar as duas dimensões sem aumentar significativamente a complexidade do relatório.

## Alternativas consideradas

### Quantidade de pacotes

É uma métrica válida para frequência, mas não representa necessariamente utilização de rede.

### Dois rankings independentes

Forneceria mais informação, porém aumentaria a saída sem necessidade para o escopo atual.

## Consequências

### Benefícios

- ranking representa volume efetivamente movimentado;
- quantidade de pacotes continua visível;
- grandes fluxos não ficam escondidos por grandes quantidades de pacotes pequenos.

### Trade-off

Um usuário que interprete "tráfego" exclusivamente como frequência de pacotes pode inicialmente esperar outro ranking.

Por isso, a saída identifica explicitamente:

```text
Top 5 ... by traffic volume
```

## Validação

A regra é protegida por testes automatizados utilizando IPs com quantidades e volumes propositalmente diferentes.

## Quando revisitar

Caso o consumidor da informação passe a definir "tráfego" por outra métrica, o ranking poderá ser alterado ou tornado configurável.
