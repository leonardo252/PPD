# Fanorona RMI/RPC com Pyro5

Projeto de Fanorona para dois jogadores em computadores diferentes. A comunicacao usa chamadas de metodos remotos com Pyro5; nao ha protocolo de mensagens JSON implementado manualmente nem Name Server obrigatorio.

## Recursos

- tabuleiro tradicional 5 x 9 e 22 pecas por jogador;
- movimentos pelas conexoes horizontais, verticais e diagonais;
- captura por aproximacao e afastamento;
- captura obrigatoria e sequencias com a mesma peca;
- bloqueio de posicoes ja visitadas durante a sequencia;
- servidor autoritativo e controle de turno;
- chat separado dos avisos internos;
- desistência e indicacao de vencedor;
- painel de operacoes remotas, resultado, latencia e versao do estado;
- sincronizacao periodica por chamadas Pyro;
- testes unitarios e teste real de integracao Pyro.

## Instalar

Requer Python 3 com Tkinter:

```bash
python3 -m pip install -r requirements.txt
```

## Executar no mesmo computador

Abra dois terminais na pasta do projeto e execute em ambos:

```bash
python3 main.py
```

Na primeira janela, selecione **Servidor (Brancas)**, mantenha a porta 5000 e clique em **Hospedar partida**.

Na segunda, selecione **Cliente (Pretas)**, use IP `127.0.0.1`, porta 5000 e clique em **Conectar**.

## Executar em computadores diferentes

1. Instale os requisitos nos dois computadores.
2. No servidor, hospede usando a porta escolhida.
3. Descubra o IPv4 do servidor na rede local.
4. No cliente, informe esse IP e a mesma porta.
5. Se necessario, permita Python/Pyro5 no firewall.

O objeto remoto usa a URI:

```text
PYRO:fanorona.game@IP_DO_SERVIDOR:PORTA
```

## Operacoes remotas

O objeto `FanoronaService` expoe:

- `ping()`;
- `join_game(nome)`;
- `get_snapshot(token, versao)`;
- `make_move(token, origem, destino, captura)`;
- `end_capture_sequence(token)`;
- `send_chat(token, texto)`;
- `get_messages(token, ultimo_id)`;
- `surrender(token)`;
- `leave_game(token)`.

Somente o servidor altera `FanoronaGame`. Cada jogador recebe um token e o servidor associa esse token a uma cor. Um `RLock` protege o estado contra chamadas simultaneas.

## Testar

```bash
python3 -m unittest discover -s tests -v
```

## Gerar executavel

O PyInstaller gera um executavel para o sistema em que o comando e executado. Para Windows, execute `build_windows.bat` em um computador Windows. Para Linux ou macOS:

```bash
sh build_linux_macos.sh
```

O resultado fica na pasta `dist`. Um executavel Windows precisa ser gerado no proprio Windows.

O arquivo `ARQUITETURA.md` explica os objetos remotos, as threads, as operacoes e o fluxo de uma jogada para auxiliar na apresentacao.

## Estrutura

```text
fanorona_pyro_game/
├── main.py
├── requirements.txt
├── game/
│   ├── board.py
│   └── game.py
├── remote/
│   ├── client.py
│   ├── server.py
│   └── service.py
├── ui/
│   └── main_window.py
└── tests/
```
