import pygame

from config import *

def desenhar_tabuleiro(tela):
    tela.fill(COR_FELTRO)
    for i in range(TAMANHO_TABULEIRO + 1):
        pos = i * TAMANHO_QUADRADO
        # Linhas verticais
        pygame.draw.line(tela, COR_LINHAS_FELTRO, (pos, 0), (pos, ALTURA_TABULEIRO))
        # Linhas horizontais
        pygame.draw.line(tela, COR_LINHAS_FELTRO, (0, pos), (LARGURA_TABULEIRO, pos))

def desenhar_pecas(tela, tabuleiro):
    raio = 25
    for linha in range(TAMANHO_TABULEIRO):
        for coluna in range(TAMANHO_TABULEIRO):
            # Centro da casa
            pos_x = coluna * TAMANHO_QUADRADO + (TAMANHO_QUADRADO // 2)
            pos_y = linha * TAMANHO_QUADRADO + (TAMANHO_QUADRADO // 2)
            
            # Desenha peças com base na matriz
            if tabuleiro[linha][coluna] == 1: # Peça preta
                pygame.draw.circle(tela, COR_PRETA, (pos_x, pos_y), raio)
            elif tabuleiro[linha][coluna] == 2: # Peça branca
                pygame.draw.circle(tela, COR_BRANCA, (pos_x, pos_y), raio)