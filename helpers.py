from constants import (
    BUTTON_DIMENSIONS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    PLAYER_HEIGHT,
    PLAYER_WIDTH,
    BUTTON_HEIGHT,
    BUTTON_WIDTH,
)
import pygame


def initialize_assets(screen):
    player_1 = pygame.draw.rect(
        screen,
        "blue",
        (20, (SCREEN_HEIGHT / 2) - PLAYER_HEIGHT, PLAYER_WIDTH, PLAYER_HEIGHT),
    )

    player_2 = pygame.draw.rect(
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

    assets = player_1, player_2, sim_button

    return assets


def in_button(mos_pos):
    mos_x, mos_y = mos_pos

    but_x, but_y, but_w, but_h = BUTTON_DIMENSIONS

    if but_x <= mos_x <= but_x + but_w and but_y <= mos_y <= but_y + but_h:
        return True
    else:
        return False
