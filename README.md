# Automação para criar personagem no WoW Forever

Script de Windows que cria um **Orc homem da Horda** quando o servidor recusa a criação por desequilíbrio populacional. Ele clica em Concluir, fecha o aviso e tenta de novo. Se o cliente pedir para ser fechado, o script reabre o jogo pelo Battle.net e monta o personagem outra vez.

A raça e o sexo são fixos: **Horda, Orc, homem**. A classe e os nomes ficam salvos para você escolher.

## Resolução

Os cliques foram medidos e testados com a área do cliente do jogo em **1920×1080**.

Use o jogo em **modo janela** ou **janela sem bordas** nessa resolução. Tela cheia exclusiva sai preta na captura e o script não enxerga os botões. O cliente do jogo precisa estar em **português**.

## O que você pode escolher

Abra `personagem.txt` e edite estas três linhas:

```
classe=guerreiro
primeiro_nome=Binlone
segundo_nome=Tankudo
```

| Campo | Valores |
| --- | --- |
| `classe` | `guerreiro` ou `bruxo` |
| `primeiro_nome` | 2 a 12 letras, sem espaço, número ou acento |
| `segundo_nome` | 2 a 12 letras, sem espaço, número ou acento |

Exemplos que já funcionaram neste script:

```
classe=guerreiro
primeiro_nome=Binlone
segundo_nome=Tankudo
```

```
classe=bruxo
primeiro_nome=Crow
segundo_nome=TheKing
```

A escolha do arquivo vale para as próximas execuções. Para uma execução só, sem mudar o arquivo:

```
python criar_personagem.py --classe bruxo --primeiro Crow --segundo TheKing
```

## O que o script faz

1. Confirma Horda, o primeiro retrato (Orc) e o primeiro quadrado de corpo (homem).
2. Confirma o quadro amarelo na classe escolhida: Guerreiro é o primeiro ícone da barra, Bruxo é o sexto.
3. Só então clica em Personalizar. Se a tela de nome abrir sem essa confirmação, ele volta e corrige.
4. Preenche o primeiro e o segundo nome.
5. Clica em Concluir a cada 5 segundos.
6. No aviso de população, clica em Ok e espera o intervalo.
7. No aviso de muitas tentativas, fecha o jogo, abre de novo pelo Battle.net, escolhe JxJ e refaz o personagem.

Ele não cria mulher, não escolhe Aliança e não confirma uma classe diferente da que está no arquivo.

## Como parar

- Ctrl+C na janela do script, ou
- jogue o mouse no canto superior esquerdo da tela.

## Instalação

Windows 10 ou 11, Python 3.12 e o pacote de idioma **Português (Brasil)** do reconhecimento de texto do Windows.

```
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Deixe o Battle.net aberto e logado, com o WoW Forever pronto para jogar. O ícone do Battle.net precisa estar acessível para o script achar o botão Jogar quando o cliente for fechado.

## Como usar

1. Ajuste `personagem.txt`.
2. Abra o jogo em 1920×1080, janela ou janela sem bordas.
3. Pode deixar o jogo na escolha de regras, na escolha de raça ou na tela de nome.
4. Dê dois cliques em `iniciar.bat`, ou rode:

```
.venv\Scripts\python.exe criar_personagem.py
```

O script espera 8 segundos antes do primeiro clique. Deixe a janela do jogo visível.

Para só ler a tela, sem clicar:

```
.venv\Scripts\python.exe criar_personagem.py --testar
```

O registro de cada tentativa fica em `tentativas.log`. Se aparecer um aviso que o script não conhece, ele para e salva `mensagem_inesperada.png`.
