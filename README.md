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

## Como pedir uma alteração para uma IA

Nome e classe que já existem não precisam de programação. Mude `personagem.txt` ou use o comando. Peça alteração no código só quando o comportamento tiver que mudar.

Comece qualquer pedido colando o bloco abaixo. Ele impede a IA de refazer o que já funciona.

```
Projeto: criar_personagem.py do WoW Forever, no Windows, cliente em português.
Resolução obrigatória: 1920x1080, janela ou janela sem bordas. Não recalibre os cliques para outra resolução.
Raça fixa: Horda, Orc, homem. Nunca crie mulher e nunca escolha Aliança.
Antes de Personalizar, confirme o quadro amarelo no retrato do Orc, no primeiro quadrado do corpo e na classe pedida.
Classes que já funcionam e não podem quebrar:
- guerreiro, primeiro ícone da barra, fração 0.244 0.903
- bruxo, sexto ícone da barra, fração 0.566 0.925
Não mexa em JxJ, Selecionar, botão Jogar do Battle.net, Concluir, Ok da população, fechar e reabrir no limite de tentativas, nem no intervalo padrão de 5 segundos.
Os nomes continuam em personagem.txt, com --primeiro e --segundo.
Altere somente isto:
```

Na linha final, escreva uma mudança só. Exemplos do que colocar depois de "Altere somente isto":

```
Altere somente isto: o intervalo padrão passa de 5 para 8 segundos.
```

```
Altere somente isto: quando o aviso de população aparecer, espere 8 segundos em vez de 5 antes do próximo Concluir.
```

```
Altere somente isto: adicione a classe mago. O ícone é o terceiro da barra, da esquerda para a direita. A tela em anexo está em 1920x1080, com o quadro amarelo nesse ícone e o painel escrito Mago. Mantenha guerreiro e bruxo funcionando.
```

```
Altere somente isto: na tentativa 4 do tentativas.log o clique de Personalizar aconteceu com a classe errada. A imagem em anexo mostra a tela na hora da falha. Corrija a confirmação do quadro amarelo e não mude o resto.
```

### O que enviar junto

| Situação | O que anexar |
| --- | --- |
| Classe nova | Uma imagem 1920×1080 da tela de raça, com o quadro amarelo no ícone novo e o nome da classe visível no painel da direita. Diga qual é a posição do ícone, contando da esquerda para a direita. |
| Clique no lugar errado | A imagem da tela no momento do erro e o trecho do `tentativas.log` com o horário. Diga o que foi clicado e o que deveria ter sido clicado. |
| Aviso que fez o script parar | A `mensagem_inesperada.png` e as últimas linhas do `tentativas.log`. Diga se esse aviso deve ser esperado ou se o script deve parar. |
| Só nome ou classe já pronta | Nada. Não chame a IA. Edite `personagem.txt`. |

### O que pedir no fim da alteração

Termine o pedido com este bloco, para a mudança nova não apagar Guerreiro nem Bruxo:

```
Depois de alterar, confira as duas classes que já existem.
Com classe=guerreiro, uma tela de Orc homem Guerreiro tem que ser aceita e uma tela de Bruxo tem que ser recusada.
Com classe=bruxo, o contrário.
Não personalize se o quadro amarelo estiver no quadrado da mulher ou em outra classe.
Não faça commit a menos que eu peça.
```

### Pedidos que não devem ir para a IA

Estes comandos já resolvem sem mudar o código:

```
.venv\Scripts\python.exe criar_personagem.py --classe guerreiro --primeiro Binlone --segundo Tankudo
```

```
.venv\Scripts\python.exe criar_personagem.py --classe bruxo --primeiro Crow --segundo TheKing
```

```
.venv\Scripts\python.exe criar_personagem.py --intervalo 8
```

```
.venv\Scripts\python.exe criar_personagem.py --testar
```

`--testar` só lê a tela. Use antes de deixar o script clicar de verdade.
