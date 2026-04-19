import pygame
from config import *
from logica import criar_tabuleiro, executar_jogada
from interface import desenhar_tabuleiro, desenhar_pecas

def main():
    pygame.init()
    tela = pygame.display.set_mode((LARGURA_TABULEIRO, ALTURA_TABULEIRO))
    pygame.display.set_caption("Othello")
    
    jogo = criar_tabuleiro()
    
    rodando = True
    jogador = 1
    while rodando:
        # Escuta de eventos
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False
            
            if evento.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos() # Pega a posição (x, y) em pixels
                coluna = x // TAMANHO_QUADRADO
                linha = y // TAMANHO_QUADRADO
                print(f"Clicou na célula: [{linha}][{coluna}]")
                if(executar_jogada(jogo, linha, coluna, jogador) == True):
                    jogador = 3 - jogador
        
        # Desenha o estado atual
        tela.fill(COR_FELTRO)
        desenhar_tabuleiro(tela)
        desenhar_pecas(tela, jogo)
        
        # Atualiza a tela
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()