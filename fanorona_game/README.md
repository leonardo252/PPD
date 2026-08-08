# Fanorona em Python

Implementação inicial do Fanorona usando Tkinter.

## Recursos

- Tabuleiro tradicional 5×9
- 22 peças para cada jogador
- Movimentos nas linhas horizontais, verticais e diagonais
- Captura por aproximação
- Captura por afastamento
- Escolha do tipo de captura quando ambas são possíveis
- Sequência de capturas com a mesma peça
- Captura obrigatória
- Controle de turnos
- Desistência
- Identificação do vencedor
- Interface gráfica com destaque de movimentos válidos

## Executar

Na raiz do projeto:

```bash
python3 main.py
```

Tkinter normalmente já acompanha o Python.

No macOS, caso o Tkinter não esteja disponível no Python instalado via Homebrew, use uma distribuição de Python que inclua Tcl/Tk ou instale a dependência correspondente.

## Organização

```text
fanorona_game/
├── main.py
├── game/
│   ├── board.py
│   ├── game.py
│   ├── models.py
│   └── rules.py
└── ui/
    └── main_window.py
```

A camada `game` não depende da interface. Isso facilita conectar o jogo à camada de sockets posteriormente.
