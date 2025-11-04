import pygame
from constants import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    PLAYER_WIDTH,
    PLAYER_HEIGHT,
    BUTTON_WIDTH,
    BUTTON_HEIGHT,
)

import player
import game_state
import helpers

pygame.init()
pygame.display.set_caption("prisoners dilemma")
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
running = True
clock = pygame.time.Clock()
dt = 0

font = pygame.font.SysFont("Arial", 12)
text_simulate_surface = font.render("simulate", False, "black")


p1 = player.Unconditional_Coopearator()
p2 = player.Unconditional_Defector()
game = game_state.Game(p1, p2, 20)

print("start game...")


text_player1_score = 0
text_player1_score = 0
scores = ()

helpers.initialize_assets(screen)

while running:
    screen.fill("black")

    # poll for events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONUP:
            mos_pos = pygame.mouse.get_pos()
            if helpers.in_button(mos_pos):
                test = game.play_round()
                if test:
                    print("true")
                else:
                    print("false")

    text_player1_score = font.render(str(game.player_1.score), False, "blue")
    text_player2_score = font.render(str(game.player_2.score), False, "red")

    screen.blit(text_player1_score, (100, 100))
    screen.blit(text_player2_score, (800, 100))
    # screen.blit(text_simulate_surface, sim_button.center)

    pygame.display.flip()

    dt = clock.tick(60) / 1000

pygame.quit()
