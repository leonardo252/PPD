# Arquitetura e explicacao para apresentacao

## Por que Pyro5

Pyro significa *Python Remote Objects*. O cliente recebe um proxy que representa o objeto `FanoronaService` hospedado em outro processo. Uma chamada como `proxy.make_move(...)` e serializada, transmitida ao daemon Pyro, executada no servidor e tem seu resultado devolvido ao cliente.

O projeto nao envia comandos com `socket.send` nem implementa enquadramento de JSON. Essa infraestrutura pertence ao Pyro5.

## Componentes

### `game/board.py`

Representa a matriz 5 x 9, as 44 pecas, os limites, as conexoes entre pontos e a contagem de pecas.

### `game/game.py`

Aplica as regras: turno, captura obrigatoria, aproximacao, afastamento, sequencia, posicoes visitadas, desistencia e vencedor.

### `remote/service.py`

`FanoronaService` e o objeto remoto e a fonte oficial do estado. O decorador `@Pyro5.api.expose` permite chamadas remotas aos metodos publicos. Um `RLock` impede alteracoes concorrentes na partida.

Cada jogador recebe um token. O servidor associa o token a uma cor e nunca confia em uma cor declarada pelo cliente.

### `remote/server.py`

Cria o `Pyro5.api.Daemon`, registra a instancia unica do servico com o identificador `fanorona.game` e executa o `requestLoop` em uma thread daemon.

### `remote/client.py`

`PyroGateway` cria o proxy a partir da URI `PYRO:fanorona.game@IP:PORTA`. Um `Lock` serializa o acesso e `_pyroClaimOwnership()` transfere a propriedade do proxy para cada worker antes da chamada. Isso e necessario porque o Pyro5 associa o proxy a uma thread.

`LocalGateway` oferece a mesma interface no computador servidor, sem duplicar a logica da janela.

### `ui/main_window.py`

O Tkinter permanece na thread principal. Chamadas remotas sao executadas em threads auxiliares para nao congelar a janela. Os resultados voltam para a interface por `root.after`.

O cliente consulta periodicamente `get_snapshot` e `get_messages`. A versao do estado evita retransmitir o tabuleiro quando nada mudou.

## Operacoes remotas

| Metodo | Objetivo |
|---|---|
| `ping` | Verificar se o objeto remoto responde |
| `join_game` | Registrar jogador, gerar token e atribuir cor |
| `get_snapshot` | Consultar estado somente quando a versao mudou |
| `make_move` | Validar e aplicar uma jogada no servidor |
| `end_capture_sequence` | Encerrar voluntariamente uma sequencia |
| `send_chat` | Registrar mensagem de usuario |
| `get_messages` | Consultar mensagens posteriores a um ID |
| `surrender` | Declarar desistencia |
| `leave_game` | Informar a saida do jogador |

## Fluxo de uma jogada do cliente

```text
Clique na interface
    -> thread auxiliar
    -> PyroGateway.call("make_move", ...)
    -> Proxy Pyro
    -> rede
    -> Daemon Pyro
    -> FanoronaService.make_move
    -> FanoronaGame.move
    -> novo snapshot
    -> retorno remoto
    -> root.after
    -> redesenho da interface
```

## Concorrencia

Com os dois programas conectados, cada interface possui sua thread principal e threads auxiliares curtas para chamadas. O servidor tambem possui a thread do daemon Pyro e threads internas de atendimento criadas pelo Pyro. O numero pode variar conforme chamadas simultaneas; por isso o servico protege o estado com `RLock`.

## Decisoes do projeto

- servidor autoritativo para evitar tabuleiros divergentes;
- brancas entram primeiro e iniciam a partida;
- URI direta, dispensando um processo Name Server;
- polling por RPC em vez de callbacks bidirecionais;
- chat armazena apenas mensagens dos jogadores;
- avisos tecnicos ficam no painel de operacoes/status;
- todos os dados remotos sao listas, dicionarios, strings, numeros ou booleanos.
