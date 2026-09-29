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

    return player_1, player_2, sim_button


def in_button(mouse_position):
    mouse_x, mouse_y = mouse_position
    x, y, width, height = BUTTON_DIMENSIONS
    return x <= mouse_x <= x + width and y <= mouse_y <= y + height
