import pygame
from .constants import VIDEO_HEIGHT, VIDEO_WIDTH
import numpy as np

class Platform:
    def __init__(self, title, window_width, window_height, texture_width, texture_height):
        pygame.init()
        self.window_width = VIDEO_WIDTH * window_width // texture_width
        self.window_height = VIDEO_HEIGHT * window_height // texture_height
        self.window = pygame.display.set_mode((window_width, window_height))
        pygame.display.set_caption(title)
        self.texture = pygame.Surface((texture_width, texture_height))

        self.key_mapping = {
            pygame.K_x: 0x0,
            pygame.K_1: 0x1,
            pygame.K_2: 0x2,
            pygame.K_3: 0x3,
            pygame.K_q: 0x4,
            pygame.K_w: 0x5,
            pygame.K_e: 0x6,
            pygame.K_a: 0x7,
            pygame.K_s: 0x8,
            pygame.K_d: 0x9,
            pygame.K_z: 0xA,
            pygame.K_c: 0xB,
            pygame.K_4: 0xC,
            pygame.K_r: 0xD,
            pygame.K_f: 0xE,
            pygame.K_v: 0xF,
        }

    def update(self, buffer):
        rgb_array = np.stack([buffer * 255]*3, axis=2).astype(np.uint8)
        rgb_array = np.transpose(rgb_array, (1, 0, 2))
        surf = pygame.surfarray.make_surface(rgb_array)
        surf = pygame.transform.scale(surf, (self.window.get_width(), self.window.get_height()))
        self.window.fill((0, 0, 0))
        self.window.blit(surf, (0, 0))
        pygame.display.flip()

    def process_input(self, keys):
        quit_game = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_game = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    quit_game = True
                self.handle_keydown(event.key, keys)
            elif event.type == pygame.KEYUP:
                self.handle_keyup(event.key, keys)
        return quit_game

    def handle_keydown(self, key, keys):
        if key in self.key_mapping:
            keys[self.key_mapping[key]] = 1
        else:
            print(f"Ignored unknown key: {pygame.key.name(key)}")

    def handle_keyup(self, key, keys):
        if key in self.key_mapping:
            keys[self.key_mapping[key]] = 0
