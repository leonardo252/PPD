# Fanorona em Rede

Jogo Fanorona para dois usuarios, feito com Python, Tkinter e socket TCP persistente.

## Chat sem logs internos

O historico de chat mostra exclusivamente mensagens escritas pelos jogadores. Avisos de conexao, sincronizacao, jogadas recusadas, turnos e desconexao aparecem somente na area **Conexao/status**. O protocolo separa mensagens de usuario (`type: chat`) das demais mensagens internas.

## Executar

Requer Python 3 com Tkinter, sem bibliotecas externas:

```bash
python3 main.py
```

No primeiro computador, selecione **Servidor (Brancas)** e inicie. No segundo, selecione **Cliente (Pretas)**, informe o IP do servidor e conecte. Para testar na mesma maquina, use `127.0.0.1` e a mesma porta nas duas janelas.

## Testes

Na pasta do projeto:

```bash
python3 -m unittest discover -s tests -v
```

O servidor mantem o estado oficial. Chat, jogadas, estado, desistencia e erros trafegam como objetos JSON delimitados por quebra de linha, mas somente objetos `chat` sao renderizados no painel de conversa.
