# Fanorona em Rede

Fanorona com interface Tkinter e comunicação TCP persistente.

## Arquitetura

- O servidor joga com as peças brancas.
- O cliente joga com as peças pretas.
- O servidor mantém o estado oficial da partida.
- O cliente envia solicitações de jogada.
- O servidor valida as regras e envia o estado atualizado.
- O mesmo socket TCP permanece aberto durante toda a partida.
- Chat e comandos do jogo trafegam como JSON delimitado por `\n`.

## Executar no mesmo computador

Abra dois terminais na raiz do projeto.

Primeiro terminal:

```bash
python3 main.py
```

Selecione **Servidor** e clique em **Iniciar servidor**.

Segundo terminal:

```bash
python3 main.py
```

Selecione **Cliente**, use o IP `127.0.0.1` e clique em **Conectar**.

## Executar em dois computadores

Os dois devem estar na mesma rede.

1. No primeiro computador, inicie como servidor.
2. Copie o IP exibido na barra de conexão.
3. No segundo computador, escolha cliente e informe esse IP.
4. Use a mesma porta nos dois, por padrão `5000`.

Talvez seja necessário autorizar o Python no firewall.

## Tipos de mensagem

- `ready`
- `chat`
- `move_request`
- `finish_chain_request`
- `surrender_request`
- `state`
- `error`

## Estrutura

```text
fanorona_network_game/
├── main.py
├── game/
│   ├── board.py
│   ├── game.py
│   ├── models.py
│   └── rules.py
├── network/
│   └── connection.py
└── ui/
    └── main_window.py
```

## Dependências

Não há dependências externas. O projeto usa somente bibliotecas padrão do Python, incluindo `socket`, `threading`, `json` e `tkinter`.
