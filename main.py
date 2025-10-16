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

pygame.init()
pygame.display.set_caption("prisoners dilemma")
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
running = True
clock = pygame.time.Clock()
dt = 0

font = pygame.font.SysFont("Arial", 12)
text_surface = font.render("simulate", False, "black")

colors = ["red", "blue", "green", "purple"]

button_dimensions = (
    (SCREEN_WIDTH / 2) - PLAYER_WIDTH,
    50,
    BUTTON_WIDTH,
    BUTTON_HEIGHT,
)


player_1 = player.TitForTat(0)
player_2 = player.Random(0)

game = game_state.Game(player_1, player_2, 20)

print("start game...")
game.play_round()
game.play_round()
game.play_round()
game.play_round()
game.play_round()
game.play_round()
game.play_round()
game.play_round()
game.play_round()
game.play_round()
game.play_round()


def in_button(mos_pos, button_dimensions):
    mos_x, mos_y = mos_pos

    but_x, but_y, but_w, but_h = button_dimensions

    if but_x <= mos_x <= but_x + but_w and but_y <= mos_y <= but_y + but_h:
        return True
    else:
        return False


while running:
    # poll for events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONUP:
            mos_pos = pygame.mouse.get_pos()
            if in_button(mos_pos, button_dimensions):
                print("simulate")

    player1 = pygame.draw.rect(
        screen,
        "blue",
        (20, (SCREEN_HEIGHT / 2) - PLAYER_HEIGHT, PLAYER_WIDTH, PLAYER_HEIGHT),
    )

    player2 = pygame.draw.rect(
        screen,
        "red",
        (
            SCREEN_WIDTH - (20 + PLAYER_WIDTH),
            (SCREEN_HEIGHT / 2) - PLAYER_HEIGHT,
            PLAYER_WIDTH,
            PLAYER_HEIGHT,
        ),
    )

    sim_button = pygame.draw.rect(
        screen,
        "white",
        (
            (SCREEN_WIDTH / 2) - PLAYER_WIDTH,
            50,
            BUTTON_WIDTH,
            BUTTON_HEIGHT,
        ),
    )

    screen.blit(text_surface, sim_button.center)
    pygame.display.flip()

    dt = clock.tick(60) / 1000

pygame.quit()
