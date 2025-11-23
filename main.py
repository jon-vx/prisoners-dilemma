import pygame
from constants import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
)

import player
import game_state
from helpers import initialize_assets, in_button

import numpy as np

pygame.init()

pygame.display.set_caption("prisoners dilemma")
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
running = True
clock = pygame.time.Clock()
dt = 0

font = pygame.font.SysFont("Arial", 12)
text_simulate_surface = font.render("simulate", False, "black")


p1 = player.Random(20)
p2 = player.Pavlov(20)

game = game_state.Game(p1, p2, 20)

print("\n-----------\nstart game\n-----------\n")

game.init_log()


text_player1_score = 0
text_player1_score = 0
scores = ()

initialize_assets(screen)

while running:
    screen.fill("black")

    # poll for events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONUP:
            mos_pos = pygame.mouse.get_pos()
            if in_button(mos_pos):
                game_over = game.play_round()
                if game_over:
                    print("game over")
                    running = False

    text_player1_score = font.render(str(game.player_1.score), False, "blue")
    text_player2_score = font.render(str(game.player_2.score), False, "red")
    p1_rect, p2_rect, sim_button = initialize_assets(screen)

    screen.blit(text_player1_score, (100, 100))
    screen.blit(text_player2_score, (800, 100))
    screen.blit(text_simulate_surface, sim_button.center)

    pygame.display.flip()

    dt = clock.tick(60) / 1000

pygame.quit()
