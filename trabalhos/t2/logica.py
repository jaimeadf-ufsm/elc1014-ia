from config import TAMANHO_TABULEIRO

def criar_tabuleiro():
    tabuleiro = [[0] * TAMANHO_TABULEIRO for _ in range(TAMANHO_TABULEIRO)]
    
    meio = TAMANHO_TABULEIRO // 2
    a = meio - 1
    
    tabuleiro[a][a] = 2  # Branca
    tabuleiro[meio][meio] = 2  # Branca
    tabuleiro[a][meio] = 1  # Preta
    tabuleiro[meio][a] = 1  # Preta
    
    return tabuleiro

def obter_capturas(tabuleiro, linha, coluna, jogador):
    oponente = 3 - jogador
    capturas_total = []
    
    # As 8 direções (vert, hor e diags)
    direcoes = [
        (-1, 0), (1, 0), (0, -1), (0, 1),   # cima, baixo, esquerda, direita
        (-1, -1), (-1, 1), (1, -1), (1, 1)  # diags
    ]

    for dl, dc in direcoes:
        caminho_direcao = []
        passo = 1
        nova_l = linha + dl
        nova_c = coluna + dc

        # Caminha enquanto encontrar peças do oponente dentro do tabuleiro
        while 0 <= nova_l < TAMANHO_TABULEIRO and 0 <= nova_c < TAMANHO_TABULEIRO and tabuleiro[nova_l][nova_c] == oponente:
            caminho_direcao.append((nova_l, nova_c))
            passo += 1
            nova_l = linha + passo * dl
            nova_c = coluna + passo * dc

        # Se o loop parou e encontrou uma peça do jogador atual, fechou o oponente
        if 0 <= nova_l < TAMANHO_TABULEIRO and 0 <= nova_c < TAMANHO_TABULEIRO:
            if tabuleiro[nova_l][nova_c] == jogador and len(caminho_direcao) > 0:
                capturas_total.extend(caminho_direcao)

    return capturas_total

def executar_jogada(tabuleiro, linha, coluna, jogador):
    # A casa deve estar vazia
    if tabuleiro[linha][coluna] != 0:
        return False

    # Lista de todas as peças que seriam capturadas
    pecas_para_virar = obter_capturas(tabuleiro, linha, coluna, jogador)

    # Se a lista estiver vazia, a jogada é inválida
    if not pecas_para_virar:
        return False

    # Colocamos a peça nova e viramos as capturadas
    tabuleiro[linha][coluna] = jogador
    for l, c in pecas_para_virar:
        tabuleiro[l][c] = jogador
        
    return True