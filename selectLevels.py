import pygame
import pygame_gui
import os
from level import Level
from settings import *


class LevelSelection:
    def __init__(self, screen, manager):
        self.screen = screen
        self.manager = pygame_gui.UIManager(
            (window_width, window_height), UI_THEME
        )
        self.width, self.height = screen.get_size()

        self.font = pygame.font.SysFont(font_path, 24)
        self.bg_pattern = self.create_bg_pattern()

        self.dark_overlay = pygame.Surface((self.width, self.height))
        self.dark_overlay.fill((0, 0, 0))
        self.dark_overlay.set_alpha(150)

        self.current_level = 0
        self.selected_level = None

        self.level_cache = {}

        self._setup_ui()
        self._load_level_preview()

        self.hover_scale = 1.0

        self.box_red_img = pygame.image.load(
            "assets/graphics/interactables/BoxRed.png"
        ).convert_alpha()

        self.box_red_img = pygame.transform.scale(
            self.box_red_img, (scaled_tile, scaled_tile)
        )

        self.target_red_img = pygame.image.load(
            "assets/graphics/interactables/ButtonUpRed.png"
        ).convert_alpha()

        self.target_red_img = pygame.transform.scale(
            self.target_red_img, (scaled_tile, scaled_tile)
        )

        self.input_active = False
        self.input_text = ""

        self.cursor_timer = 0
        self.cursor_visible = True

    def _setup_ui(self):
        btn_w = 80
        btn_h = 250
        margin = 70

        center_y = (window_height - btn_h) // 2

        self.home_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((90, 60), (80, 80)),
            text='',
            manager=self.manager,
            object_id="#home_btn"
        )

        self.left_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((margin, center_y), (btn_w, btn_h)),
            text='', manager=self.manager,
            object_id="#left_btn"
        )

        self.right_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((window_width - margin - btn_w, center_y), (btn_w, btn_h)),
            text='', manager=self.manager,
            object_id="#right_btn"
        )

    def create_bg_pattern(self):
        curr_w, curr_h = self.screen.get_size()
        dark_tile = pygame.image.load(textures['menu_dark']).convert_alpha()
        light_tile = pygame.image.load(textures['menu_light']).convert_alpha()
        tw, th = dark_tile.get_size()

        pattern = pygame.Surface((curr_w, curr_h))

        for y in range(0, curr_h, th):
            for x in range(0, curr_w, tw):
                tile = light_tile if ((x // tw) + (y // th)) % 2 == 0 else dark_tile
                pattern.blit(tile, (x, y))

        return pattern

    def _load_level_preview(self):
        if self.current_level not in self.level_cache:
            if not os.path.exists(f"levels/{self.current_level}.txt"):
                self.current_level = 0

            if self.current_level not in self.level_cache:
                self.level_cache[self.current_level] = Level(self.current_level)

        level = self.level_cache[self.current_level]
        self.box_count = len(level.boxes)

        map_width = level.columns * scaled_tile
        map_height = level.rows * scaled_tile

        surface = pygame.Surface((map_width, map_height), pygame.SRCALPHA)
        level.draw(surface)

        self.box_positions = level.boxes.copy()
        self.target_positions = level.targets.copy()
        self.level_ref = level

        player_img = pygame.image.load(textures['player']).convert_alpha()
        player_img = pygame.transform.scale(player_img, (scaled_tile, scaled_tile))

        player_x = level.player_start_x * scaled_tile
        player_y = level.player_start_y * scaled_tile

        surface.blit(player_img, (player_x, player_y))

        DESIRED_TILE = 64

        current_tile = scaled_tile

        scale = DESIRED_TILE / current_tile

        preview_w = int(map_width * scale)
        preview_h = int(map_height * scale)

        self.preview_img = pygame.transform.smoothscale(surface, (preview_w, preview_h))

        TOP_OFFSET = 200

        self.preview_rect = pygame.Rect(
            (self.width - preview_w) // 2,
            TOP_OFFSET,
            preview_w,
            preview_h
        )

    def handle_events(self, event):
        self.manager.process_events(event)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_pos = event.pos
                if self.preview_rect.collidepoint(mouse_pos):
                    return "START", self.current_level
                if hasattr(self, "title_rect") and self.title_rect.collidepoint(mouse_pos):
                    self.input_active = True
                    self.input_text = ""

        if event.type == pygame_gui.UI_BUTTON_PRESSED:

            if event.ui_element == self.left_btn:
                self.current_level = max(0, self.current_level - 1)
                self._load_level_preview()

            elif event.ui_element == self.right_btn:
                self.current_level += 1
                self._load_level_preview()

            elif event.ui_element == self.home_btn:
                return "HOME", self.current_level

        if event.type == pygame.KEYDOWN and self.input_active:

            if event.key == pygame.K_RETURN:
                if self.input_text.isdigit():
                    new_level = int(self.input_text) - 1

                    if os.path.exists(f"levels/{new_level}.txt"):
                        self.current_level = new_level
                        self._load_level_preview()

                self.input_active = False

            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]

            else:
                if event.unicode.isdigit():
                    self.input_text += event.unicode
        return None, None

    def draw(self):
        self.screen.blit(self.bg_pattern, (0, 0))
        self.screen.blit(self.dark_overlay, (0, 0))

        self.cursor_timer += 0.016

        if self.cursor_timer >= 0.5:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0

        mouse_pos = pygame.mouse.get_pos()
        hover = self.preview_rect.collidepoint(mouse_pos)

        scaled_w = int(self.preview_rect.width * self.hover_scale)
        scaled_h = int(self.preview_rect.height * self.hover_scale)

        scaled_img = pygame.transform.smoothscale(self.preview_img, (scaled_w, scaled_h))

        draw_x = self.preview_rect.centerx - scaled_w // 2
        draw_y = self.preview_rect.centery - scaled_h // 2

        self.screen.blit(scaled_img, (draw_x, draw_y))

        if hover:
            scale = scaled_w / (self.level_ref.columns * scaled_tile)

            for box in self.box_positions:
                col, row = box

                x = int(draw_x + col * scaled_tile * scale)
                y = int(draw_y + row * scaled_tile * scale)

                size = int(scaled_tile * scale)

                box_img = pygame.transform.smoothscale(self.box_red_img, (size, size))

                self.screen.blit(box_img, (x, y))

            for col, row in self.target_positions:
                x = int(draw_x + col * scaled_tile * scale)
                y = int(draw_y + row * scaled_tile * scale)

                size = int(scaled_tile * scale)
                target_img = pygame.transform.smoothscale(self.target_red_img, (size, size))

                self.screen.blit(target_img, (x, y))

        if hover:
            border_thickness = 5
            offset = border_thickness

            pygame.draw.rect(
                self.screen,
                (233, 79, 53),
                (
                    draw_x - offset,
                    draw_y - offset,
                    scaled_w + offset * 2,
                    scaled_h + offset * 2
                ),
                border_thickness
            )

        font = pygame.font.Font(font_path, 80)

        if self.input_active:
            display_text = f"LEVEL {self.input_text}" if self.input_text else "LEVEL"
        else:
            display_text = f"LEVEL {self.current_level + 1}"

        txt = font.render(display_text, True, (0, 255, 127))

        shadow = font.render(display_text, True, (0, 50, 0))

        TITLE_Y = 80
        level_x = self.preview_rect.centerx - txt.get_width() // 2
        level_y = TITLE_Y

        self.title_rect = pygame.Rect(
            level_x,
            level_y,
            txt.get_width(),
            txt.get_height()
        )

        self.screen.blit(shadow, (level_x + 5, level_y + 5))

        self.screen.blit(txt, (level_x, level_y))

        if self.input_active:
            cursor = "_" if self.cursor_visible else ""

            cursor_surf = font.render(cursor, True, (0, 255, 127))

            cursor_x = level_x + txt.get_width() + 5
            cursor_y = level_y

            self.screen.blit(cursor_surf, (cursor_x, cursor_y))

        box_font = pygame.font.Font(font_path, 50)

        box_text = box_font.render(
            f"Boxes: {self.box_count}", True, (0, 255, 127)
        )
        shadow = box_font.render(
            f"Boxes: {self.box_count}", True, (0, 50, 0)
        )

        BOX_Y = 800
        box_x = self.preview_rect.centerx - box_text.get_width() // 2
        box_y = BOX_Y

        self.screen.blit(shadow, (box_x + 2, box_y + 2))
        self.screen.blit(box_text, (box_x, box_y))

        self.manager.update(0.016)
        self.manager.draw_ui(self.screen)