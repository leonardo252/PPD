# Arquitetura e roteiro de explicacao

## MOM

Message-Oriented Middleware desacopla produtores e consumidores. O cliente nao chama diretamente um worker; ele publica uma mensagem no broker. O worker tambem nao chama diretamente o dashboard; publica um evento no topico.

## Fila

`/queue/mom.keyword.lines` usa o padrao *competing consumers*. Com N workers, cada linha e entregue para somente um deles. A quantidade pode aumentar sem mudar o cliente.

## Topico

`/topic/mom.keyword.results` distribui cada resultado aos subscribers ativos. O dashboard soma as contagens recebidas.

## Workflow

```text
Cliente
  -> leitor par + leitor impar
  -> producer STOMP
  -> fila do RabbitMQ
  -> N consumers/workers
  -> contagem
  -> publisher STOMP
  -> topico do RabbitMQ
  -> subscriber
  -> dashboard
```

## Mensagens

- `job_started`: identifica arquivo, palavras e inicio;
- `line`: representa uma unidade paralelizavel;
- `line_result`: contagem parcial feita por um worker;
- `job_manifest`: informa total de linhas;
- `worker_started`, `worker_stopped`, `worker_error`: monitoramento.

## Entrega e ACK

O worker usa ACK individual. A ordem e: receber, contar, publicar o resultado e confirmar a linha. Se falhar antes do ACK, o broker pode redelivery a mensagem. Como isso pode gerar resultado duplicado, o dashboard guarda as linhas ja processadas por `job_id` e `line_number`.

## Threads e processos

- Tkinter permanece na thread principal;
- conexoes e leitura usam threads auxiliares;
- RabbitMQ executa como servico local instalado pelo Homebrew;
- workers externos sao processos independentes e podem estar em outras maquinas;
- stomp.py possui sua propria thread de recepcao por conexao.

## Demonstracao sugerida

1. Abra o console do RabbitMQ.
2. Inicie o dashboard.
3. Inicie dois workers externos.
4. Configure zero workers locais no cliente.
5. Processe um arquivo grande.
6. Inicie mais workers durante o processamento.
7. Mostre o aumento da lista de workers e a atualizacao do dashboard.
