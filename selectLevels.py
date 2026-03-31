import pygame
import pygame_gui
import os
from level import Level
from settings import *


class LevelSelection:
    def __init__(self, screen, manager):
        self.screen = screen
        self.manager = manager
        self.width, self.height = screen.get_size()

        self.font = pygame.font.SysFont("Arial", 24)

        self.current_level = 1
        self.selected_level = None

        self.level_cache = {}

        self._setup_ui()
        self._load_level_preview()

    def _setup_ui(self):
        mid_x = self.width // 2
        mid_y = self.height // 2

        self.home_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((10, 10), (100, 40)),
            text='Home',
            manager=self.manager
        )

        self.left_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((mid_x - 200, mid_y - 25), (50, 50)),
            text='<', manager=self.manager
        )

        self.right_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((mid_x + 150, mid_y - 25), (50, 50)),
            text='>', manager=self.manager
        )

        self.play_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((mid_x - 50, mid_y + 180), (100, 50)),
            text='PLAY', manager=self.manager
        )

    def _load_level_preview(self):
        if self.current_level not in self.level_cache:
            if not os.path.exists(f"levels/{self.current_level}.txt"):
                self.current_level = 1

            if self.current_level not in self.level_cache:
                self.level_cache[self.current_level] = Level(self.current_level)

            self.level_cache[self.current_level] = Level(self.current_level)

        level = self.level_cache[self.current_level]

        map_width = level.columns * scaled_tile
        map_height = level.rows * scaled_tile

        surface = pygame.Surface((map_width, map_height), pygame.SRCALPHA)
        level.draw(surface)

        self.preview_img = pygame.transform.smoothscale(surface, (300, 300))

        self.preview_rect = self.preview_img.get_rect(
            center=(self.width // 2, self.height // 2)
        )

    def handle_events(self, event):
        self.manager.process_events(event)

        if event.type == pygame_gui.UI_BUTTON_PRESSED:

            if event.ui_element == self.left_btn:
                self.current_level = max(1, self.current_level - 1)
                self._load_level_preview()

            elif event.ui_element == self.right_btn:
                self.current_level += 1
                self._load_level_preview()

            elif event.ui_element == self.play_btn:
                return "START", self.current_level

            elif event.ui_element == self.home_btn:
                return "HOME", self.current_level
        return None, None

    def draw(self):
        self.screen.fill((200, 200, 200))

        self.screen.blit(self.preview_img, self.preview_rect)

        txt = self.font.render(
            f"LEVEL: {self.current_level}", True, (0, 0, 0)
        )
        self.screen.blit(txt, (self.width // 2 - 60, self.height // 2 - 180))