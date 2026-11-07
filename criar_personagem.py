# -*- coding: utf-8 -*-
"""Tenta criar um Orc homem no WoW Forever quando o servidor recusa por população.

A classe e os nomes ficam em personagem.txt. As classes prontas são Guerreiro
e Bruxo. O jogo precisa estar em português, em janela ou janela sem bordas,
na resolução em que o script foi medido: 1920x1080.

Para parar: Ctrl+C, ou jogue o mouse no canto superior esquerdo da tela.
"""

from __future__ import annotations

import argparse
import ctypes
import sys
import time
import unicodedata
import winsound
from ctypes import wintypes
from dataclasses import dataclass, field
from pathlib import Path

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

import numpy as np
import pyautogui
import winocr
from PIL import Image

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05

PASTA = Path(__file__).resolve().parent
ARQUIVO_LOG = PASTA / "tentativas.log"
ARQUIVO_PERSONAGEM = PASTA / "personagem.txt"
INTERVALO_PADRAO = 5
RESOLUCAO = "1920x1080"
ICONES_CLASSE = {
    "guerreiro": (0.244, 0.903),
    "bruxo": (0.566, 0.925),
}
ROTULO_CLASSE = {"guerreiro": "Guerreiro", "bruxo": "Bruxo"}
ESPERA_RESPOSTA = 4
PAUSA_ENTRE_OLHADAS = 0.45

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
user32.GetWindowTextLengthW.restype = ctypes.c_int
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowTextW.restype = ctypes.c_int
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.IsWindowVisible.restype = wintypes.BOOL
user32.IsWindow.argtypes = [wintypes.HWND]
user32.IsWindow.restype = wintypes.BOOL
user32.IsIconic.argtypes = [wintypes.HWND]
user32.IsIconic.restype = wintypes.BOOL
user32.GetForegroundWindow.restype = wintypes.HWND
user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.GetClientRect.restype = wintypes.BOOL
user32.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]
user32.ClientToScreen.restype = wintypes.BOOL
user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.ShowWindow.restype = wintypes.BOOL
user32.SetForegroundWindow.argtypes = [wintypes.HWND]
user32.SetForegroundWindow.restype = wintypes.BOOL
user32.BringWindowToTop.argtypes = [wintypes.HWND]
user32.BringWindowToTop.restype = wintypes.BOOL
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD
kernel32.GetCurrentThreadId.restype = wintypes.DWORD
user32.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]
user32.AttachThreadInput.restype = wintypes.BOOL
user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.PostMessageW.restype = wintypes.BOOL
kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
kernel32.TerminateProcess.restype = wintypes.BOOL
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL

SW_RESTORE = 9


@dataclass
class Captura:
    imagem: np.ndarray
    esquerda: int
    topo: int
    hwnd: int


@dataclass
class Leitura:
    estado: str
    texto: str = ""
    concluir: tuple | None = None
    ok: tuple | None = None
    dourado: float = 0.0
    cinza: float = 0.0
    alvos: dict = field(default_factory=dict)


@dataclass
class Personagem:
    classe: str
    primeiro: str
    segundo: str

    @property
    def rotulo(self) -> str:
        return ROTULO_CLASSE[self.classe]


personagem = Personagem("guerreiro", "Binlone", "Tankudo")


def nome_valido(nome: str) -> bool:
    return nome.isascii() and nome.isalpha() and 2 <= len(nome) <= 12


def ler_personagem(caminho: Path) -> Personagem:
    dados = {"classe": personagem.classe, "primeiro_nome": personagem.primeiro, "segundo_nome": personagem.segundo}
    if caminho.exists():
        for linha in caminho.read_text(encoding="utf-8").splitlines():
            texto = linha.split("#", 1)[0].strip()
            if not texto or "=" not in texto:
                continue
            chave, valor = texto.split("=", 1)
            dados[chave.strip().lower()] = valor.strip()
    classe = normalizar(dados["classe"])
    if classe not in ICONES_CLASSE:
        raise SystemExit(f"Classe inválida em {caminho.name}: {dados['classe']!r}. Use guerreiro ou bruxo.")
    primeiro = dados["primeiro_nome"]
    segundo = dados["segundo_nome"]
    if not nome_valido(primeiro) or not nome_valido(segundo):
        raise SystemExit("Os nomes precisam ter de 2 a 12 letras, sem espaço, número ou acento.")
    return Personagem(classe, primeiro, segundo)


def log(mensagem: str) -> None:
    linha = f"[{time.strftime('%H:%M:%S')}] {mensagem}"
    print(linha, flush=True)
    with ARQUIVO_LOG.open("a", encoding="utf-8") as arquivo:
        arquivo.write(linha + "\n")


def normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFD", texto)
    sem_acento = "".join(c for c in sem_acento if unicodedata.category(c) != "Mn")
    return sem_acento.lower()


def eh_controle_populacional(texto: str) -> bool:
    tratado = normalizar(texto)
    return "populacional" in tratado or "desequilibrio" in tratado


def eh_conectando(texto: str) -> bool:
    tratado = normalizar(texto)
    if any(chave in tratado for chave in ("excluir", "deseja", "populacional", "desequilibrio", "muitas tentativas")):
        return False
    if any(chave in tratado for chave in ("conectando", "servidor", "carregando", "obtendo", "obtend", "informac", "serv")):
        return True
    # O leitor às vezes devolve o texto da conexão ilegível, mas o botão continua sendo só Cancelar.
    return "cancelar" in tratado and " ok " not in f" {tratado} "


def eh_limite_de_tentativas(texto: str) -> bool:
    tratado = normalizar(texto)
    return "muitas tentativas" in tratado or "curto periodo" in tratado or "feche o cliente" in tratado


def ler_palavras(imagem: np.ndarray) -> list[dict]:
    resultado = winocr.recognize_pil_sync(Image.fromarray(imagem), "pt-BR")
    palavras = []
    for linha in (resultado or {}).get("lines") or []:
        for palavra in linha.get("words") or []:
            caixa = palavra.get("bounding_rect") or {}
            texto = palavra.get("text") or ""
            if not texto or "x" not in caixa:
                continue
            palavras.append(
                {
                    "texto": texto,
                    "norm": normalizar(texto),
                    "x": float(caixa["x"]),
                    "y": float(caixa["y"]),
                    "w": float(caixa["width"]),
                    "h": float(caixa["height"]),
                }
            )
    return palavras


def centro_da_palavra(palavra: dict) -> tuple[float, float]:
    return palavra["x"] + palavra["w"] / 2, palavra["y"] + palavra["h"] / 2


def texto_das_palavras(palavras: list[dict]) -> str:
    return " ".join(palavra["norm"] for palavra in palavras)


def achar_jogar(imagem: np.ndarray) -> tuple[int, int, int, int] | None:
    altura, largura = imagem.shape[:2]
    topo = int(0.18 * altura)
    base = int(0.62 * altura)
    recorte = imagem[topo:base]
    vermelho = recorte[:, :, 0].astype(np.int16)
    verde = recorte[:, :, 1].astype(np.int16)
    azul = recorte[:, :, 2].astype(np.int16)
    mascara = (vermelho < 40) & (verde > 95) & (verde < 165) & (azul > 175) & (azul > verde + 40)
    projecao = mascara.sum(axis=0)
    melhor = None
    for xs, xe in _corridas(projecao >= 4, max(2, int(largura * 0.008))):
        bw = xe - xs + 1
        if not (0.08 * largura <= bw <= 0.28 * largura):
            continue
        colunas = mascara[:, xs : xe + 1]
        linhas = np.flatnonzero(colunas.sum(axis=1) >= max(3, int(bw * 0.25)))
        if len(linhas) == 0:
            continue
        ys, ye = int(linhas.min()), int(linhas.max())
        bh = ye - ys + 1
        if bh > 0.12 * altura or bw < bh * 2:
            continue
        area = int(colunas[ys : ye + 1].sum())
        if melhor is None or area > melhor[0]:
            melhor = (area, xs, topo + ys, bw, bh)
    if melhor is None:
        return None
    _, x, y, bw, bh = melhor
    return int(x), int(y), int(bw), int(bh)


def montar_alvos(imagem: np.ndarray, palavras: list[dict], estado: str) -> dict:
    altura, largura = imagem.shape[:2]
    alvos: dict[str, tuple[float, float]] = {}
    if estado == "regras":
        normal = next((p for p in palavras if p["norm"] == "normal"), None)
        interpretacoes = [p for p in palavras if p["norm"].startswith("interpret")]
        interpretacoes.sort(key=lambda p: p["x"])
        if normal and interpretacoes:
            esquerda = centro_da_palavra(normal)
            direita = centro_da_palavra(interpretacoes[0])
            alvos["jxj"] = ((esquerda[0] + direita[0]) / 2, esquerda[1] + altura * 0.08)
        selecionar = next((p for p in palavras if p["norm"] == "selecionar"), None)
        if selecionar:
            alvos["selecionar"] = centro_da_palavra(selecionar)
    elif estado == "raca":
        alvos["horda"] = (largura * 0.181, altura * 0.040)
        alvos["orc"] = (largura * 0.182, altura * 0.236)
        alvos["corpo"] = (largura * 0.481, altura * 0.055)
        for classe, (frac_x, frac_y) in ICONES_CLASSE.items():
            alvos[classe] = (largura * frac_x, altura * frac_y)
        personalizar = next((p for p in palavras if p["norm"] == "personalizar"), None)
        if personalizar:
            alvos["personalizar"] = centro_da_palavra(personalizar)
    elif estado in {"digitar", "pronto"}:
        digites = [p for p in palavras if p["norm"] == "digite"]
        digites.sort(key=lambda p: p["x"])
        if len(digites) >= 2:
            alvos["nome1"] = centro_da_palavra(digites[0])
            alvos["nome2"] = centro_da_palavra(digites[1])
        else:
            alvos["nome1"] = (largura * 0.345, altura * 0.064)
            alvos["nome2"] = (largura * 0.563, altura * 0.064)
    return alvos


def titulo_da_janela(hwnd: int) -> str:
    tamanho = user32.GetWindowTextLengthW(hwnd)
    if tamanho <= 0:
        return ""
    buffer = ctypes.create_unicode_buffer(tamanho + 1)
    user32.GetWindowTextW(hwnd, buffer, tamanho + 1)
    return buffer.value


def listar_janelas() -> list[tuple[int, str, int]]:
    encontradas: list[tuple[int, str, int]] = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def visitar(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd) or user32.IsIconic(hwnd):
            return True
        titulo = titulo_da_janela(hwnd)
        if not titulo.strip():
            return True
        rect = wintypes.RECT()
        if not user32.GetClientRect(hwnd, ctypes.byref(rect)):
            return True
        area = max(0, rect.right) * max(0, rect.bottom)
        if area > 0:
            encontradas.append((hwnd, titulo, area))
        return True

    user32.EnumWindows(visitar, 0)
    return encontradas


def pontuar_titulo(titulo: str, filtro: str | None) -> int:
    nome = titulo.lower()
    if filtro:
        return 100 if filtro.lower() in nome else 0
    if "world of warcraft" in nome:
        return 100
    if "wow forever" in nome or "wowforever" in nome:
        return 90
    if "warcraft" in nome:
        return 80
    return 0


def achar_jogo(filtro: str | None) -> tuple[int, str] | None:
    candidatas = []
    for hwnd, titulo, area in listar_janelas():
        pontos = pontuar_titulo(titulo, filtro)
        if pontos:
            candidatas.append((pontos, area, hwnd, titulo))
    if not candidatas:
        return None
    candidatas.sort(reverse=True)
    _, _, hwnd, titulo = candidatas[0]
    return hwnd, titulo


def focar(hwnd: int) -> bool:
    if user32.GetForegroundWindow() == hwnd:
        return True
    user32.ShowWindow(hwnd, SW_RESTORE)
    primeiro_plano = user32.GetForegroundWindow()
    thread_atual = kernel32.GetCurrentThreadId()
    thread_frente = user32.GetWindowThreadProcessId(primeiro_plano, ctypes.byref(wintypes.DWORD()))
    thread_alvo = user32.GetWindowThreadProcessId(hwnd, ctypes.byref(wintypes.DWORD()))
    user32.AttachThreadInput(thread_atual, thread_frente, True)
    user32.AttachThreadInput(thread_atual, thread_alvo, True)
    user32.BringWindowToTop(hwnd)
    user32.SetForegroundWindow(hwnd)
    user32.AttachThreadInput(thread_atual, thread_frente, False)
    user32.AttachThreadInput(thread_atual, thread_alvo, False)
    time.sleep(0.25)
    return user32.GetForegroundWindow() == hwnd


def capturar(hwnd: int) -> Captura | None:
    rect = wintypes.RECT()
    if not user32.GetClientRect(hwnd, ctypes.byref(rect)):
        return None
    largura, altura = int(rect.right), int(rect.bottom)
    if largura < 200 or altura < 200:
        return None
    canto = wintypes.POINT(0, 0)
    if not user32.ClientToScreen(hwnd, ctypes.byref(canto)):
        return None
    import mss

    with mss.MSS() as sct:
        bruto = sct.grab({"left": int(canto.x), "top": int(canto.y), "width": largura, "height": altura})
        imagem = np.array(bruto, dtype=np.uint8)[:, :, :3][:, :, ::-1]
    return Captura(imagem=imagem, esquerda=int(canto.x), topo=int(canto.y), hwnd=hwnd)


def _faixa(imagem: np.ndarray, x0: float, y0: float, x1: float, y1: float) -> np.ndarray:
    altura, largura = imagem.shape[:2]
    esquerda = max(0, min(largura - 1, int(x0 * largura)))
    direita = max(esquerda + 1, min(largura, int(x1 * largura)))
    topo = max(0, min(altura - 1, int(y0 * altura)))
    base = max(topo + 1, min(altura, int(y1 * altura)))
    return imagem[topo:base, esquerda:direita]


def _corridas(ativos: np.ndarray, folga: int) -> list[tuple[int, int]]:
    indices = np.flatnonzero(ativos)
    if len(indices) == 0:
        return []
    corridas: list[tuple[int, int]] = []
    inicio = anterior = int(indices[0])
    for valor in indices[1:]:
        atual = int(valor)
        if atual - anterior <= folga:
            anterior = atual
        else:
            corridas.append((inicio, anterior))
            inicio = anterior = atual
    corridas.append((inicio, anterior))
    return corridas


def achar_botao(
    imagem: np.ndarray,
    regiao: tuple[float, float, float, float],
    largura_minima: float,
    altura_maxima: float,
    centro_x: tuple[float, float],
    centro_y: tuple[float, float],
    largura_maxima: float = 1.0,
    preferir_direita: bool = False,
) -> tuple[int, int, int, int] | None:
    altura, largura = imagem.shape[:2]
    x0, y0, x1, y1 = regiao
    esquerda = int(x0 * largura)
    direita = int(x1 * largura)
    topo = int(y0 * altura)
    base = int(y1 * altura)
    recorte = imagem[topo:base, esquerda:direita]
    if recorte.size == 0:
        return None
    vermelho = recorte[:, :, 0].astype(np.int16)
    verde = recorte[:, :, 1].astype(np.int16)
    azul = recorte[:, :, 2].astype(np.int16)
    mascara = (vermelho >= 80) & (verde < 42) & (azul < 32) & ((vermelho - verde) > 48) & (vermelho > azul)

    # Soma as colunas para o texto claro no meio do botão não partir o retângulo.
    # A folga é curta de propósito, para não grudar o botão no vermelho do personagem.
    projecao = mascara.sum(axis=0)
    folga = max(1, int(largura * 0.002))
    minimo = max(8, int(largura_minima * largura))
    teto = max(minimo, int(largura_maxima * largura))
    limite_altura = max(6, int(altura_maxima * altura))
    melhor = None
    for xs, xe in _corridas(projecao >= 2, folga):
        bw = xe - xs + 1
        if bw < minimo or bw > teto:
            continue
        sub = mascara[:, xs : xe + 1]
        fortes = np.flatnonzero(sub.sum(axis=1) >= max(3, int(bw * 0.18)))
        if len(fortes) == 0:
            continue
        # O texto do botão abre um vão no meio; junta as faixas de cima e de baixo.
        folga_vertical = max(2, int(altura * 0.016))
        grupos: list[list[int]] = [[int(fortes[0])]]
        for linha in fortes[1:]:
            linha = int(linha)
            if linha - grupos[-1][-1] <= folga_vertical:
                grupos[-1].append(linha)
            else:
                grupos.append([linha])
        for grupo in grupos:
            ys, ye = grupo[0], grupo[-1]
            bh = ye - ys + 1
            if bh > limite_altura or bw < bh * 3:
                continue
            cx = (esquerda + (xs + xe) / 2) / largura
            cy = (topo + (ys + ye) / 2) / altura
            if not (centro_x[0] <= cx <= centro_x[1] and centro_y[0] <= cy <= centro_y[1]):
                continue
            area = int(sub[ys : ye + 1].sum())
            chave = esquerda + xe if preferir_direita else area
            if melhor is None or chave > melhor[0]:
                melhor = (chave, esquerda + xs, topo + ys, bw, bh)
    if melhor is None:
        return None
    _, x, y, bw, bh = melhor
    return int(x), int(y), int(bw), int(bh)


def fracao_dourada(imagem: np.ndarray) -> float:
    recorte = _faixa(imagem, 0.28, 0.40, 0.72, 0.53)
    vermelho = recorte[:, :, 0].astype(np.int16)
    verde = recorte[:, :, 1].astype(np.int16)
    azul = recorte[:, :, 2].astype(np.int16)
    dourado = (vermelho > 150) & (verde > 105) & (verde < 230) & (azul < 120) & ((verde - azul) > 25)
    return float(dourado.mean())


def fracao_cinza_concluir(imagem: np.ndarray) -> float:
    recorte = _faixa(imagem, 0.82, 0.90, 0.96, 0.955)
    vermelho = recorte[:, :, 0].astype(np.int16)
    verde = recorte[:, :, 1].astype(np.int16)
    azul = recorte[:, :, 2].astype(np.int16)
    cinza = (np.abs(vermelho - verde) < 18) & (np.abs(verde - azul) < 18) & (vermelho > 18) & (vermelho < 95)
    return float(cinza.mean())


def tela_preta(imagem: np.ndarray) -> bool:
    return float(imagem.mean()) < 8


def ler_dialogo(imagem: np.ndarray) -> str:
    altura, largura = imagem.shape[:2]
    recorte = imagem[int(0.38 * altura) : int(0.56 * altura), int(0.20 * largura) : int(0.80 * largura)]
    resultado = winocr.recognize_pil_sync(Image.fromarray(recorte), "pt-BR")
    if isinstance(resultado, dict):
        return (resultado.get("text") or "").strip()
    return str(resultado or "").strip()


def classificar(imagem: np.ndarray, ler_texto: bool = True, completo: bool = False) -> Leitura:
    if tela_preta(imagem):
        return Leitura("preta")

    ok = achar_botao(
        imagem,
        regiao=(0.34, 0.50, 0.66, 0.60),
        largura_minima=0.09,
        altura_maxima=0.045,
        centro_x=(0.42, 0.58),
        centro_y=(0.51, 0.59),
    )
    concluir = achar_botao(
        imagem,
        regiao=(0.70, 0.900, 0.995, 0.962),
        largura_minima=0.10,
        largura_maxima=0.22,
        altura_maxima=0.06,
        centro_x=(0.82, 0.96),
        centro_y=(0.90, 0.96),
        preferir_direita=True,
    )
    dourado = fracao_dourada(imagem) if ok is not None else 0.0
    cinza = fracao_cinza_concluir(imagem)

    if ok is not None and dourado >= 0.008:
        texto = ler_dialogo(imagem) if ler_texto else ""
        letras = sum(caractere.isalpha() for caractere in texto)
        if eh_conectando(texto):
            return Leitura("conectando", texto, concluir, ok, dourado, cinza)
        if eh_limite_de_tentativas(texto):
            return Leitura("popup_limite", texto, concluir, ok, dourado, cinza)
        if letras >= 12 and not eh_controle_populacional(texto):
            return Leitura("popup_outro", texto, concluir, ok, dourado, cinza)
        if letras < 12:
            return Leitura("popup_ilegivel", texto, concluir, ok, dourado, cinza)
        return Leitura("popup_populacao", texto, concluir, ok, dourado, cinza)

    if not completo:
        if concluir is not None:
            return Leitura("pronto", "", concluir, ok, dourado, cinza)
        if cinza >= 0.35:
            return Leitura("concluir_indisponivel", "", None, ok, dourado, cinza)
        return Leitura("fora", "", None, ok, dourado, cinza)

    palavras = ler_palavras(imagem) if ler_texto else []
    texto_tela = texto_das_palavras(palavras)
    if "conjunto de regras" in texto_tela or ("selecionar" in texto_tela and "normal" in texto_tela):
        estado = "regras"
    elif any(p["norm"] == "personalizar" for p in palavras):
        estado = "raca"
    elif "nome completo" in texto_tela:
        nomes_prontos = normalizar(personagem.primeiro) in texto_tela and "digite" not in texto_tela and concluir is not None
        estado = "pronto" if nomes_prontos else "digitar"
    elif any(p["norm"] == "concluir" for p in palavras) and concluir is not None:
        estado = "pronto"
    elif cinza >= 0.35:
        estado = "concluir_indisponivel"
    else:
        estado = "fora"
    return Leitura(estado, texto_tela[:400], concluir, ok, dourado, cinza, montar_alvos(imagem, palavras, estado))


def descrever(leitura: Leitura) -> str:
    nomes = {
        "pronto": "Concluir está disponível",
        "popup_populacao": "aviso de controle populacional",
        "conectando": "o jogo está conectando",
        "popup_limite": "muitas tentativas, precisa reabrir o jogo",
        "popup_outro": "aviso diferente do controle populacional",
        "popup_ilegivel": "aviso no centro, mas o texto não foi lido",
        "regras": "escolha do conjunto de regras",
        "raca": "escolha de raça e classe",
        "digitar": "tela de nome, ainda falta preencher",
        "concluir_indisponivel": "Concluir está apagado e não há aviso no centro",
        "fora": "não estou na tela de criação",
        "preta": "a captura veio preta",
    }
    return nomes.get(leitura.estado, leitura.estado)


def clicar_ponto(captura: Captura, ponto: tuple[float, float]) -> None:
    pyautogui.moveTo(captura.esquerda + ponto[0], captura.topo + ponto[1], duration=0.15)
    time.sleep(0.05)
    pyautogui.click()


def clicar_botao(captura: Captura, botao: tuple[int, int, int, int]) -> None:
    x, y, largura, altura = botao
    destino_x = captura.esquerda + x + largura / 2
    destino_y = captura.topo + y + altura / 2
    pyautogui.moveTo(destino_x, destino_y, duration=0.18)
    time.sleep(0.06)
    pyautogui.click()


def esperar(segundos: float, rotulo: str) -> None:
    fim = time.monotonic() + segundos
    ultimo_marco = None
    while True:
        falta = fim - time.monotonic()
        if falta <= 0:
            return
        marco = int(round(falta))
        if marco > 0 and marco % 10 == 0 and marco != ultimo_marco:
            log(f"{rotulo} Próxima tentativa em {marco}s.")
            ultimo_marco = marco
        time.sleep(min(0.5, falta))


def salvar_tela(imagem: np.ndarray, nome: str) -> Path:
    destino = PASTA / nome
    Image.fromarray(imagem).save(destino)
    return destino


def observar(hwnd: int) -> Leitura:
    seguidas_fora = 0
    fim = time.monotonic() + ESPERA_RESPOSTA
    ultima = Leitura("indefinido")
    while time.monotonic() < fim:
        if user32.GetForegroundWindow() != hwnd:
            seguidas_fora = 0
            time.sleep(PAUSA_ENTRE_OLHADAS)
            continue
        captura = capturar(hwnd)
        if captura is None:
            time.sleep(PAUSA_ENTRE_OLHADAS)
            continue
        ultima = classificar(captura.imagem)
        if ultima.estado == "popup_limite":
            return ultima
        if ultima.estado in {"popup_populacao", "popup_outro", "popup_ilegivel"}:
            if ultima.estado == "popup_populacao" and ultima.ok is not None:
                clicar_botao(captura, ultima.ok)
                time.sleep(0.4)
            else:
                salvar_tela(captura.imagem, "mensagem_inesperada.png")
            return ultima
        if ultima.estado == "fora":
            seguidas_fora += 1
            if seguidas_fora >= 3:
                return ultima
        else:
            seguidas_fora = 0
        time.sleep(PAUSA_ENTRE_OLHADAS)
    return ultima


def tocar(sucesso: bool) -> None:
    if sucesso:
        for _ in range(3):
            winsound.Beep(880, 180)
            time.sleep(0.08)
    else:
        winsound.Beep(440, 700)


def validar_imagens(caminhos: list[str]) -> None:
    for caminho in caminhos:
        imagem = np.array(Image.open(caminho).convert("RGB"))
        leitura = classificar(imagem, completo=True)
        print(caminho)
        print(
            f"  estado={leitura.estado} | {descrever(leitura)}\n"
            f"  texto={leitura.texto[:180]!r}\n"
            f"  alvos={ {chave: (round(valor[0], 1), round(valor[1], 1)) for chave, valor in leitura.alvos.items()} }"
        )


def testar_ao_vivo(filtro: str | None, apontar: bool) -> None:
    jogo = achar_jogo(filtro)
    if jogo is None:
        print("Não encontrei a janela do jogo. Janelas visíveis:")
        for _, titulo, _ in listar_janelas():
            print(f"  - {titulo}")
        return
    hwnd, titulo = jogo
    print(f"Janela: {titulo}")
    if user32.GetForegroundWindow() != hwnd:
        print("A janela do jogo não está na frente. O resultado pode ser de outra janela por cima.")
    captura = capturar(hwnd)
    if captura is None:
        print("Não consegui capturar a janela. Se o jogo estiver minimizado, restaure-o.")
        return
    leitura = classificar(captura.imagem, completo=True)
    print(f"Estado: {leitura.estado} — {descrever(leitura)}")
    if leitura.texto:
        print(f"Texto lido: {leitura.texto}")
    print(f"Concluir: {leitura.concluir} | Ok: {leitura.ok}")
    print(f"Dourado: {leitura.dourado:.4f} | Cinza: {leitura.cinza:.4f} | Tamanho: {captura.imagem.shape[1]}x{captura.imagem.shape[0]}")
    destino = salvar_tela(captura.imagem, "ultima_leitura.png")
    print(f"Captura salva em {destino}")
    if apontar:
        botao = leitura.ok or leitura.concluir
        if botao is None:
            print("Não há botão para apontar.")
            return
        if not focar(hwnd):
            print("Não consegui trazer o jogo para a frente.")
            return
        captura = capturar(hwnd)
        if captura is None:
            return
        leitura = classificar(captura.imagem)
        botao = leitura.ok or leitura.concluir
        if botao is None:
            print("O botão sumiu antes de apontar.")
            return
        x, y, largura, altura = botao
        pyautogui.moveTo(captura.esquerda + x + largura / 2, captura.topo + y + altura / 2, duration=0.2)
        print("Mouse posicionado. Nenhum clique foi feito.")


def achar_battle() -> tuple[int, str] | None:
    candidatas = []
    for hwnd, titulo, area in listar_janelas():
        if "battle.net" in titulo.lower():
            candidatas.append((area, hwnd, titulo))
    if not candidatas:
        return None
    candidatas.sort(reverse=True)
    _, hwnd, titulo = candidatas[0]
    return hwnd, titulo


def fechar_jogo(hwnd: int) -> None:
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    user32.PostMessageW(hwnd, 0x0010, 0, 0)
    limite = time.monotonic() + 6
    while time.monotonic() < limite:
        if not user32.IsWindow(hwnd):
            log("Jogo fechado.")
            return
        time.sleep(0.3)
    handle = kernel32.OpenProcess(1, False, pid.value)
    if handle:
        kernel32.TerminateProcess(handle, 0)
        kernel32.CloseHandle(handle)
        log("Jogo encerrado.")
    else:
        log("Não consegui encerrar o jogo. Feche a janela do WoW manualmente.")


def abrir_pelo_battle(intervalo_espera: float = 90) -> None:
    battle = achar_battle()
    if battle is None:
        log("Não encontrei a janela do Battle.net. Deixe o launcher aberto.")
        time.sleep(3)
        return
    hwnd, titulo = battle
    log(f"Abrindo o jogo por {titulo}.")
    if not focar(hwnd):
        log("Não consegui trazer o Battle.net para a frente.")
        time.sleep(2)
        return
    captura = capturar(hwnd)
    if captura is None:
        return
    botao = achar_jogar(captura.imagem)
    if botao is None:
        log("Não achei o botão Jogar. Se o jogo já estiver abrindo, vou esperar.")
    else:
        clicar_botao(captura, botao)
        log("Cliquei em Jogar.")
    fim = time.monotonic() + intervalo_espera
    while time.monotonic() < fim:
        if achar_jogo(None):
            log("O jogo abriu.")
            time.sleep(2)
            return
        time.sleep(2)
    log("O jogo não apareceu a tempo. Vou tentar de novo.")


def preencher_nomes(captura: Captura, leitura: Leitura) -> None:
    for chave, nome in (("nome1", personagem.primeiro), ("nome2", personagem.segundo)):
        ponto = leitura.alvos.get(chave)
        if ponto is None:
            log(f"Não achei o campo {chave}.")
            return
        clicar_ponto(captura, ponto)
        time.sleep(0.25)
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.05)
        pyautogui.press("backspace")
        pyautogui.typewrite(nome, interval=0.04)
        time.sleep(0.15)
    log(f"Preenchi os nomes {personagem.primeiro} e {personagem.segundo}.")


def agir_regras(hwnd: int, captura: Captura, leitura: Leitura) -> None:
    if "jxj" in leitura.alvos:
        log("Selecionando JxJ.")
        clicar_ponto(captura, leitura.alvos["jxj"])
        time.sleep(0.7)
        nova = capturar(hwnd)
        if nova is not None:
            captura = nova
            leitura = classificar(captura.imagem, completo=True)
    if "selecionar" in leitura.alvos:
        log("Clicando em Selecionar.")
        clicar_ponto(captura, leitura.alvos["selecionar"])
        time.sleep(1.2)


RACAS = {"orc", "orquisa", "draenor", "humano", "humana", "elfo", "elfa", "anao", "ana", "troll", "troli", "morto-vivo", "renegado", "renegada", "tauren", "goblin", "nightborne"}
CLASSES = {"bruxo", "bruxa", "guerreiro", "guerreira", "cacador", "cacadora", "mago", "maga", "ladino", "ladina", "sacerdote", "sacerdotisa", "paladino", "paladina", "druida", "druidesa", "xama"}


def titulos_do_painel(imagem: np.ndarray) -> tuple[str, str]:
    altura, largura = imagem.shape[:2]
    direita = [p for p in ler_palavras(imagem) if p["x"] > 0.74 * largura]

    def primeiro(inicio: float, fim: float, aceitas: set[str]) -> str:
        candidatos = [p for p in direita if inicio * altura <= p["y"] <= fim * altura and p["norm"] in aceitas]
        if not candidatos:
            return ""
        return min(candidatos, key=lambda p: p["y"])["norm"]

    return primeiro(0.28, 0.45, RACAS), primeiro(0.55, 0.70, CLASSES)


def corpo_e_homem(imagem: np.ndarray) -> bool | None:
    altura, largura = imagem.shape[:2]
    vermelho = imagem[:, :, 0].astype(np.int16)
    verde = imagem[:, :, 1].astype(np.int16)
    azul = imagem[:, :, 2].astype(np.int16)
    dourado = (vermelho > 155) & (verde > 105) & (azul < 145) & (verde > azul + 25)
    topo, base = int(0.005 * altura), int(0.11 * altura)
    faixa_homem = dourado[topo:base, int(0.45 * largura) : int(0.505 * largura)]
    faixa_mulher = dourado[topo:base, int(0.512 * largura) : int(0.57 * largura)]
    homem = int(faixa_homem.sum())
    mulher = int(faixa_mulher.sum())
    if homem < 25 and mulher < 25:
        return None
    if homem > mulher * 1.35:
        return True
    if mulher > homem * 1.35:
        return False
    return None


def classe_com_quadro(imagem: np.ndarray) -> str | None:
    altura, largura = imagem.shape[:2]
    vermelho = imagem[:, :, 0].astype(np.int16)
    verde = imagem[:, :, 1].astype(np.int16)
    azul = imagem[:, :, 2].astype(np.int16)
    dourado = (vermelho > 150) & (verde > 100) & (azul < 160) & (verde > azul + 20)
    topo, base = int(0.84 * altura), int(0.96 * altura)
    bruxo = int(dourado[topo:base, int(0.53 * largura) : int(0.62 * largura)].sum())
    guerreiro = int(dourado[topo:base, int(0.18 * largura) : int(0.28 * largura)].sum())
    if bruxo < 20 and guerreiro < 20:
        return None
    if guerreiro > bruxo * 1.2 and guerreiro >= 40:
        return "guerreiro"
    if bruxo > guerreiro * 1.2 and bruxo >= 40:
        return "bruxo"
    return None


def atualizar_captura(hwnd: int, captura: Captura) -> Captura:
    nova = capturar(hwnd)
    return nova if nova is not None else captura


def orc_destacado(imagem: np.ndarray) -> bool | None:
    altura, largura = imagem.shape[:2]
    vermelho = imagem[:, :, 0].astype(np.int16)
    verde = imagem[:, :, 1].astype(np.int16)
    azul = imagem[:, :, 2].astype(np.int16)
    dourado = (vermelho > 160) & (verde > 120) & (azul < 130) & (verde > azul + 30)
    esquerda, direita = int(0.145 * largura), int(0.215 * largura)
    primeiro = int(dourado[int(0.13 * altura) : int(0.30 * altura), esquerda:direita].sum())
    segundo = int(dourado[int(0.30 * altura) : int(0.46 * altura), esquerda:direita].sum())
    if primeiro < 40 and segundo < 40:
        return None
    if primeiro > segundo * 2 and primeiro >= 80:
        return True
    if segundo > primeiro * 1.5:
        return False
    return None


def raca_e_orc(imagem: np.ndarray, raca: str) -> bool:
    if raca in {"orc", "orquisa", "draenor"}:
        return True
    if raca in RACAS:
        return False
    return orc_destacado(imagem) is True


def selecao_certa(imagem: np.ndarray) -> bool:
    raca, classe = titulos_do_painel(imagem)
    quadro = classe_com_quadro(imagem)
    classe_ok = classe == personagem.classe and (quadro is None or quadro == personagem.classe)
    return raca_e_orc(imagem, raca) and classe_ok and corpo_e_homem(imagem) is True


def agir_raca(hwnd: int, captura: Captura) -> bool:
    for _ in range(5):
        raca, classe = titulos_do_painel(captura.imagem)
        homem = corpo_e_homem(captura.imagem)
        quadro = classe_com_quadro(captura.imagem)
        log(f"Seleção vista: raça={raca or '?'}, classe={classe or '?'}, homem={homem}, quadro={quadro or '?'}.")
        if selecao_certa(captura.imagem):
            leitura = classificar(captura.imagem, completo=True)
            if "personalizar" in leitura.alvos:
                log(f"Quadro amarelo no Orc homem e no {personagem.rotulo}. Clicando em Personalizar.")
                clicar_ponto(captura, leitura.alvos["personalizar"])
                time.sleep(1.2)
                return True
        altura, largura = captura.imagem.shape[:2]
        if not raca_e_orc(captura.imagem, raca):
            log("Selecionando a Horda e o retrato do Orc.")
            clicar_ponto(captura, (largura * 0.181, altura * 0.040))
            time.sleep(0.6)
            captura = atualizar_captura(hwnd, captura)
            altura, largura = captura.imagem.shape[:2]
            clicar_ponto(captura, (largura * 0.182, altura * 0.220))
            time.sleep(0.7)
            captura = atualizar_captura(hwnd, captura)
            raca, classe = titulos_do_painel(captura.imagem)
            homem = corpo_e_homem(captura.imagem)
            quadro = classe_com_quadro(captura.imagem)
            altura, largura = captura.imagem.shape[:2]
        if homem is not True:
            log("O quadro amarelo não está no primeiro quadrado. Clicando no homem.")
            clicar_ponto(captura, (largura * 0.478, altura * 0.055))
            time.sleep(0.6)
            captura = atualizar_captura(hwnd, captura)
            raca, classe = titulos_do_painel(captura.imagem)
            quadro = classe_com_quadro(captura.imagem)
            altura, largura = captura.imagem.shape[:2]
        if classe != personagem.classe or (quadro is not None and quadro != personagem.classe):
            log(f"O quadro amarelo não está no {personagem.rotulo}. Selecionando {personagem.rotulo}.")
            frac_x, frac_y = ICONES_CLASSE[personagem.classe]
            clicar_ponto(captura, (largura * frac_x, altura * frac_y))
            time.sleep(0.7)
            captura = atualizar_captura(hwnd, captura)
    log(f"Ainda não está Orc homem {personagem.rotulo}. Não vou personalizar.")
    return False


def clicar_voltar(captura: Captura) -> None:
    voltar = next((p for p in ler_palavras(captura.imagem) if p["norm"] == "voltar"), None)
    if voltar is not None:
        clicar_ponto(captura, centro_da_palavra(voltar))
        return
    altura, largura = captura.imagem.shape[:2]
    clicar_ponto(captura, (largura * 0.12, altura * 0.93))


def loop(filtro: str | None, intervalo: float) -> None:
    log(
        "Personagem: %s %s, Horda, Orc homem, %s. Concluir a cada %.0fs."
        % (personagem.primeiro, personagem.segundo, personagem.rotulo, intervalo)
    )
    log("Paro se aparecer um aviso que eu não conheço. Ctrl+C também para.")
    for restante in range(8, 0, -1):
        print(f"Começando em {restante}s. Foque a janela do jogo.", flush=True)
        time.sleep(1)

    tentativa = 0
    proxima = 0.0
    titulo_visto = ""
    selecao_ok = False
    while True:
        jogo = achar_jogo(filtro)
        if jogo is None:
            abrir_pelo_battle()
            continue
        hwnd, titulo = jogo
        if titulo != titulo_visto:
            log(f"Usando a janela: {titulo}")
            titulo_visto = titulo
        if user32.IsIconic(hwnd):
            log("O jogo está minimizado. Restaure a janela.")
            time.sleep(3)
            continue
        if not focar(hwnd):
            log("Não consegui trazer o jogo para a frente. Clique na janela dele.")
            time.sleep(3)
            continue

        captura = capturar(hwnd)
        if captura is None:
            time.sleep(1)
            continue
        leitura = classificar(captura.imagem, completo=True)

        if leitura.estado in {"preta", "conectando"}:
            log("O jogo ainda está carregando ou conectando. Vou esperar.")
            time.sleep(2)
            continue
        if leitura.estado == "popup_limite":
            log(f"Limite de tentativas: {leitura.texto}")
            log("Vou fechar o jogo e abrir de novo pelo Battle.net.")
            fechar_jogo(hwnd)
            time.sleep(2)
            tentativa = 0
            proxima = 0.0
            selecao_ok = False
            continue
        if leitura.estado == "popup_outro":
            caminho = salvar_tela(captura.imagem, "mensagem_inesperada.png")
            log(f"Mensagem diferente da esperada: {leitura.texto}")
            log(f"Parei sem clicar de novo. A tela foi salva em {caminho.name}.")
            tocar(False)
            return
        if leitura.estado == "popup_ilegivel":
            caminho = salvar_tela(captura.imagem, "mensagem_inesperada.png")
            log(f"Vi um aviso, mas não consegui ler o texto ({leitura.texto!r}). Parei por segurança.")
            log(f"Tela salva em {caminho.name}.")
            tocar(False)
            return
        if leitura.estado == "popup_populacao":
            if leitura.ok is not None:
                log(f"Controle populacional. Vou fechar o aviso. Texto: {leitura.texto}")
                clicar_botao(captura, leitura.ok)
                time.sleep(0.3)
            proxima = time.monotonic() + intervalo
            falta = proxima - time.monotonic()
            if falta > 0:
                esperar(falta, "Aviso fechado.")
            continue
        if leitura.estado == "regras":
            selecao_ok = False
            agir_regras(hwnd, captura, leitura)
            continue
        if leitura.estado == "raca":
            selecao_ok = agir_raca(hwnd, captura)
            continue
        if leitura.estado in {"digitar", "pronto", "concluir_indisponivel"} and not selecao_ok:
            log(f"A tela de nome abriu sem Orc homem {personagem.rotulo} confirmado. Voltando para corrigir.")
            clicar_voltar(captura)
            time.sleep(1.0)
            continue
        if leitura.estado == "digitar":
            preencher_nomes(captura, leitura)
            time.sleep(0.8)
            continue
        if leitura.estado == "concluir_indisponivel":
            log("O botão Concluir está apagado. Vou tentar preencher o nome de novo.")
            preencher_nomes(captura, leitura)
            time.sleep(1)
            continue
        if leitura.estado == "fora":
            log("Tela ainda não reconhecida. Esperando o jogo chegar numa etapa conhecida.")
            time.sleep(2)
            continue
        if leitura.estado != "pronto" or leitura.concluir is None:
            time.sleep(1)
            continue

        falta = proxima - time.monotonic()
        if falta > 0:
            esperar(falta, "Aguardando o intervalo.")
            continue

        tentativa += 1
        log(f"Tentativa {tentativa}: clicando em Concluir.")
        clicar_botao(captura, leitura.concluir)
        instante = time.monotonic()
        time.sleep(0.25)
        resultado = observar(hwnd)
        if resultado.estado == "popup_limite":
            log(f"Limite de tentativas depois do clique: {resultado.texto}")
            log("Vou fechar o jogo e abrir de novo pelo Battle.net.")
            fechar_jogo(hwnd)
            time.sleep(2)
            tentativa = 0
            proxima = 0.0
            selecao_ok = False
            continue
        if resultado.estado == "fora":
            log(f"A tela de criação fechou na tentativa {tentativa}. Personagem aceito.")
            tocar(True)
            return
        if resultado.estado == "popup_outro":
            log(f"Mensagem diferente depois do clique: {resultado.texto}")
            log("Parei para não continuar clicando.")
            tocar(False)
            return
        if resultado.estado == "popup_ilegivel":
            log(f"Apareceu um aviso que não consegui ler ({resultado.texto!r}). Parei por segurança.")
            tocar(False)
            return
        if resultado.estado == "popup_populacao":
            log(f"Ainda bloqueado pela população. Próxima tentativa em {int(intervalo)}s.")
        else:
            log(f"O clique não abriu o aviso. Próxima tentativa em {int(intervalo)}s.")
        proxima = instante + intervalo
        falta = proxima - time.monotonic()
        if falta > 0:
            esperar(falta, "Aguardando.")


def aplicar_argumentos(args: argparse.Namespace) -> None:
    global personagem
    escolhido = ler_personagem(ARQUIVO_PERSONAGEM)
    classe = normalizar(args.classe) if args.classe else escolhido.classe
    primeiro = args.primeiro if args.primeiro else escolhido.primeiro
    segundo = args.segundo if args.segundo else escolhido.segundo
    if classe not in ICONES_CLASSE:
        raise SystemExit("Classe inválida. Use guerreiro ou bruxo.")
    if not nome_valido(primeiro) or not nome_valido(segundo):
        raise SystemExit("Os nomes precisam ter de 2 a 12 letras, sem espaço, número ou acento.")
    personagem = Personagem(classe, primeiro, segundo)


def main() -> None:
    parser = argparse.ArgumentParser(description="Tenta criar o personagem quando a facção está fechada por população.")
    parser.add_argument("--intervalo", type=float, default=INTERVALO_PADRAO, help="Segundos entre tentativas. Padrão: 5.")
    parser.add_argument("--janela", default=None, help="Parte do título da janela do jogo, se a detecção automática errar.")
    parser.add_argument("--classe", choices=["guerreiro", "bruxo"], help="Substitui a classe salva em personagem.txt nesta execução.")
    parser.add_argument("--primeiro", help="Substitui o primeiro nome salvo em personagem.txt nesta execução.")
    parser.add_argument("--segundo", help="Substitui o segundo nome salvo em personagem.txt nesta execução.")
    parser.add_argument("--testar", action="store_true", help="Só olha a tela e diz o que encontrou, sem clicar.")
    parser.add_argument("--apontar", action="store_true", help="Com --testar, move o mouse até o botão, sem clicar.")
    parser.add_argument("--validar", nargs="+", metavar="IMAGEM", help="Testa a leitura em imagens salvas, sem usar o jogo.")
    args = parser.parse_args()
    aplicar_argumentos(args)

    if args.validar:
        validar_imagens(args.validar)
        return
    if args.testar:
        testar_ao_vivo(args.janela, args.apontar)
        return
    try:
        loop(args.janela, args.intervalo)
    except pyautogui.FailSafeException:
        log("Parei porque o mouse foi para o canto superior esquerdo.")
    except KeyboardInterrupt:
        log("Parei pelo Ctrl+C.")


if __name__ == "__main__":
    main()
