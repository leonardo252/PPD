# Projeto MOM - Contador paralelo de palavras-chave

Aplicacao em Python que usa RabbitMQ como Message-Oriented Middleware. Dois produtores leem linhas pares e impares de um arquivo, publicam cada linha em uma fila, N workers competem pelo trabalho e publicam os resultados em um topico acompanhado por um dashboard.

O broker ja esta configurado no codigo como `127.0.0.1:61613`, usuario `guest`, senha `guest` e virtual host `/`. As interfaces conectam automaticamente; o usuario nao precisa preencher host, porta ou credenciais.

## Componentes

- `client_app.py`: interface do cliente, dois leitores e produtores;
- `dashboard_app.py`: subscriber e dashboard em tempo real;
- `worker_app.py`: worker externo, executavel em qualquer computador;
- `main.py`: menu para abrir cliente ou dashboard;
- `common/`: mensagens JSON e contagem;
- `broker/`: adaptador STOMP;
- `workers/`: consumidores concorrentes;
- `tests/`: testes unitarios e teste opcional com broker real.

## Instalar

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

No Windows, a ativacao e:

```bat
.venv\Scripts\activate
```

## Preparar o RabbitMQ no macOS (uma unica vez)

Instale e habilite os plugins STOMP e de gerenciamento:

```bash
brew install rabbitmq
"$(brew --prefix rabbitmq)/sbin/rabbitmq-plugins" enable rabbitmq_stomp
"$(brew --prefix rabbitmq)/sbin/rabbitmq-plugins" enable rabbitmq_management
```

Inicie o servico:

```bash
brew services start rabbitmq
```

Teste a porta usada pelo projeto:

```bash
nc -vz 127.0.0.1 61613
```

O painel do RabbitMQ fica em `http://localhost:15672`, com `guest` / `guest`.

## Ordem de execucao

1. Inicie o RabbitMQ.
2. Abra o dashboard antes do job, pois o topico e em tempo real. A conexao e automatica.
3. Abra o cliente. A conexao tambem e automatica.
4. Selecione o arquivo, informe palavras-chave e a quantidade de workers locais.
5. Inicie o processamento.

Terminais:

```bash
python dashboard_app.py
python client_app.py
```

Ou use o menu:

```bash
python main.py
```

## Workers externos

Defina `Workers locais` como 0 e execute quantos workers externos desejar:

```bash
python worker_app.py --id worker-1
python worker_app.py --id worker-2
python worker_app.py --id worker-3
```

Todos consomem `/queue/mom.keyword.lines`. O RabbitMQ entrega cada linha a apenas um worker. Esta versao pronta para uso local nao pede configuracoes de rede.

## Destinos MOM

| Destino | Tipo | Uso |
|---|---|---|
| `/queue/mom.keyword.lines` | Fila | Linhas distribuídas entre os workers |
| `/topic/mom.keyword.results` | Topico | Resultados e eventos enviados ao dashboard |

## Confiabilidade

- ACK `client-individual` somente depois de publicar o resultado;
- `prefetch-count=1` para distribuir melhor entre workers no RabbitMQ;
- mensagens de linha persistentes;
- `job_id` separa execucoes;
- `(job_id, line_number)` torna o dashboard idempotente;
- mensagem `job_manifest` informa o total esperado;
- erros de mensagem sao publicados como eventos de worker.

## Testes

```bash
python -m unittest discover -s tests -v
```

Com RabbitMQ local ativo, inclua a integracao real:

```bash
RUN_RABBITMQ_TESTS=1 python -m unittest tests.test_activemq_integration -v
```

## Gerar executaveis

Instale o PyInstaller:

```bash
python -m pip install -r requirements-dev.txt
```

No Windows:

```bat
build_windows.bat
```

No Linux ou macOS:

```bash
sh build_linux_macos.sh
```

Os executaveis sao gerados em `dist`.
