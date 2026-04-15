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
        self.width, self.height = window_width, window_height

        self.font = pygame.font.Font(font_path, 24)
        self.bg_pattern = self.create_bg_pattern()

        self.dark_overlay = pygame.Surface((self.width, self.height))
        self.dark_overlay.fill((0, 0, 0))
        self.dark_overlay.set_alpha(150)

        self.available_levels = []
        if os.path.exists("levels/test.txt"):
            self.available_levels.append('test')
        
        idx = 0
        while os.path.exists(f"levels/{idx}.txt"):
            self.available_levels.append(idx)
            idx += 1
            
        if not self.available_levels:
            self.available_levels = [0]

        self.current_level_idx = 0
        self.current_level = self.available_levels[self.current_level_idx]
        self.selected_level = None

        self.level_cache = {}

        self._setup_ui()
        self.level_ref = None
        self.box_positions = []
        self.target_positions = []

        self._load_level_preview()

        # Hover Highlight Assets
        self.box_red_img = pygame.transform.scale(
            pygame.image.load(textures['red_box']).convert_alpha(),
            (scaled_tile, scaled_tile)
        )
        self.target_red_img = pygame.transform.scale(
            pygame.image.load(textures['red_target']).convert_alpha(),
            (scaled_tile, scaled_tile)
        )

        # Level Search Bar State
        self.input_active = False
        self.input_text = ""
        self.cursor_timer = 0
        self.cursor_visible = True
        self.title_rect = pygame.Rect(0, 0, 0, 0)
        
        # Smooth Juice: Hover Scale
        self.hover_scale = 1.0
        self.target_scale = 1.0

    def _setup_ui(self):
        btn_w = 80
        btn_h = 250
        margin = 70

        center_y = (window_height - btn_h) // 2

        # Home / Settings Tray - Shifted by 5px for border padding
        tray_w, tray_h = 280, 100
        tray_x, tray_y = 15, window_height - tray_h - 10
        self.tray_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(tray_x, tray_y, tray_w, tray_h),
            starting_height=2,
            manager=self.manager,
            object_id="#tray_bg"
        )
        
        # Tray Background Image
        pygame_gui.elements.UIImage(
            relative_rect=pygame.Rect(0, 0, tray_w, tray_h),
            image_surface=pygame.image.load("assets/graphics/Buttons/InGameMenu/HomeSettingsTray5x.png").convert_alpha(),
            manager=self.manager,
            container=self.tray_panel
        )
        
        self.home_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(40, 10, 80, 80),
            text="", manager=self.manager, container=self.tray_panel,
            object_id="#tray_home"
        )
        self.settings_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(160, 10, 80, 80),
            text="", manager=self.manager, container=self.tray_panel,
            object_id="#tray_settings"
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
        curr_w, curr_h = window_width, window_height
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
        self.current_level = self.available_levels[self.current_level_idx]
        if self.current_level not in self.level_cache:
            if not os.path.exists(f"levels/{self.current_level}.txt"):
                self.current_level_idx = 0
                self.current_level = self.available_levels[self.current_level_idx]

            if self.current_level not in self.level_cache:
                self.level_cache[self.current_level] = Level(self.current_level)

        level = self.level_cache[self.current_level]
        self.box_count = len(level.boxes)

        map_width = level.columns * scaled_tile
        map_height = level.rows * scaled_tile

        surface = pygame.Surface((map_width, map_height), pygame.SRCALPHA)
        level.draw(surface)

        player_img = pygame.image.load(textures['player']).convert_alpha()
        player_img = pygame.transform.scale(player_img, (scaled_tile, scaled_tile))

        player_x = level.player_start_x * scaled_tile
        player_y = level.player_start_y * scaled_tile

        self.box_positions = level.boxes.copy()
        self.target_positions = list(level.targets)
        self.level_ref = level

        surface.blit(player_img, (player_x, player_y))

        # Consistent 3x scaling for EVERY map
        target_tile = 48 

        preview_w = level.columns * target_tile
        preview_h = level.rows * target_tile

        self.preview_img = pygame.transform.scale(surface, (preview_w, preview_h))

        TOP_OFFSET = 230

        self.preview_rect = pygame.Rect(
            (self.width - preview_w) // 2,
            TOP_OFFSET,
            preview_w,
            preview_h
        )

    def shift_focus(self, offset):
        old_idx = self.current_level_idx
        self.current_level_idx = max(0, min(len(self.available_levels) - 1, self.current_level_idx + offset))
        if old_idx != self.current_level_idx:
            self._load_level_preview()

    def handle_events(self, event):
        self.manager.process_events(event)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_pos = event.pos
                if self.preview_rect.collidepoint(mouse_pos):
                    return "START", self.current_level
                
                # Check for click on Level title to search
                if self.title_rect.collidepoint(mouse_pos):
                    self.input_active = True
                    self.input_text = ""
                else:
                    self.input_active = False

        if event.type == pygame.KEYDOWN:
            if self.input_active:
                if event.key == pygame.K_RETURN:
                    if self.input_text.isdigit():
                        new_level = int(self.input_text) - 1
                        # Find index of requested level if it exists
                        if new_level in self.available_levels:
                            self.current_level_idx = self.available_levels.index(new_level)
                            self._load_level_preview()
                    self.input_active = False
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self.input_active = False
                else:
                    if event.unicode.isdigit() and len(self.input_text) < 3: # Limit to 3 digits
                        self.input_text += event.unicode
                return None, None # Prevent normal navigation while typing

            # Normal navigation
            alt_pressed = bool(pygame.key.get_mods() & (pygame.KMOD_LALT | pygame.KMOD_RALT))
            nav_left = (event.key == pygame.K_a) or (event.key == pygame.K_LEFT)
            nav_right = (event.key == pygame.K_d) or (event.key == pygame.K_RIGHT)
            
            if nav_left: # Shifts on A, Left, or Alt+A, Alt+Left
                self.shift_focus(-1)
            elif nav_right: # Shifts on D, Right, or Alt+D, Alt+Right
                self.shift_focus(1)
            elif event.key == pygame.K_RETURN:
                return "START", self.current_level

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.left_btn:
                self.shift_focus(-1)
            elif event.ui_element == self.right_btn:
                self.shift_focus(1)
            elif event.ui_element == self.home_btn:
                return "HOME", self.current_level
            elif event.ui_element == self.settings_btn:
                return "SETTINGS", self.current_level
        return None, None

    def draw(self):
        self.screen.blit(self.bg_pattern, (0, 0))
        self.screen.blit(self.dark_overlay, (0, 0))

        # --- NEW: Map Selection Highlight & Zoom Logic ---
        mouse_pos = pygame.mouse.get_pos()
        hover = self.preview_rect.collidepoint(mouse_pos)
        
        # Smoothly interpolate scale (Juice!)
        self.target_scale = 1.15 if hover else 1.0
        self.hover_scale += (self.target_scale - self.hover_scale) * 0.15
        
        # Calculate zoomed dimensions
        scaled_w = int(self.preview_rect.width * self.hover_scale)
        scaled_h = int(self.preview_rect.height * self.hover_scale)
        
        # Center the zoomed image on the original rect's center
        draw_x = self.preview_rect.centerx - scaled_w // 2
        draw_y = self.preview_rect.centery - scaled_h // 2
        
        # Draw the (potentially zoomed) base preview
        # We use smoothscale for the animation to prevent pixel-jittering while zooming
        zoomed_img = pygame.transform.smoothscale(self.preview_img, (scaled_w, scaled_h))
        self.screen.blit(zoomed_img, (draw_x, draw_y))

        if hover and self.level_ref:
            # Draw red border (zoomed)
            border_thickness = 5
            pygame.draw.rect(
                self.screen,
                (233, 79, 53), # Highlighting color
                pygame.Rect(draw_x - border_thickness, draw_y - border_thickness, 
                           scaled_w + border_thickness*2, scaled_h + border_thickness*2),
                border_thickness
            )
            
            # --- Draw red boxes and targets (at correct zoomed scale) ---
            # Calculate total scale factor relative to level map coordinates
            map_w = self.level_ref.columns * scaled_tile
            draw_scale = (self.preview_rect.width * self.hover_scale) / map_w
            
            tile_size = int(scaled_tile * draw_scale)
            
            # Scale red textures to current zoomed tile size
            scaled_box_red = pygame.transform.smoothscale(self.box_red_img, (tile_size, tile_size))
            scaled_target_red = pygame.transform.smoothscale(self.target_red_img, (tile_size, tile_size))
            
            for col, row in self.target_positions:
                tx = int(draw_x + col * scaled_tile * draw_scale)
                ty = int(draw_y + row * scaled_tile * draw_scale)
                self.screen.blit(scaled_target_red, (tx, ty))
                
            for col, row in self.box_positions:
                bx = int(draw_x + col * scaled_tile * draw_scale)
                by = int(draw_y + row * scaled_tile * draw_scale)
                self.screen.blit(scaled_box_red, (bx, by))
        # ------------------------------------------------

        # Handle search bar cursor blinking
        self.cursor_timer += 0.016
        if self.cursor_timer >= 0.5:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0

        font = pygame.font.Font(font_path, 80)
        
        # Decide what text to show
        if self.input_active:
            display_digits = self.input_text
            base_text = "LEVEL "
        else:
            display_digits = str(self.current_level + 1) if self.current_level != 'test' else ""
            base_text = "TEST LEVEL" if self.current_level == 'test' else "LEVEL "

        # --- Stationary Text Fix ---
        # Calculate X based on a fixed "LEVEL " part to prevent jumping
        temp_base = font.render("LEVEL ", False, (0, 0, 0))
        fixed_center_x = self.preview_rect.centerx
        # We want the "total" expected text to be roughly centered, 
        # but the "LEVEL " part's start position should stay stable.
        # We'll anchor "LEVEL " 50 pixels to the left of center.
        level_x = fixed_center_x - (temp_base.get_width() // 2) - 30 
        level_y = 80

        # Render background/shadow for the whole string
        full_string = base_text + display_digits
        txt = font.render(full_string, False, (0, 255, 127))
        shadow = font.render(full_string, False, (0, 50, 0))
        
        # Define interaction rect (make it slightly bigger for easier clicking)
        self.title_rect = txt.get_rect(topleft=(level_x, level_y)).inflate(20, 20)

        self.screen.blit(shadow, (level_x + 5, level_y + 5))
        self.screen.blit(txt, (level_x, level_y))

        # Render Cursor
        if self.input_active and self.cursor_visible:
            cursor_surf = font.render("_", False, (0, 255, 127))
            cursor_x = level_x + txt.get_width() + 5
            self.screen.blit(cursor_surf, (cursor_x, level_y))

        box_font = pygame.font.Font(font_path, 50)

        box_text = box_font.render(
            f"Boxes: {self.box_count}", False, (0, 255, 127)
        )
        shadow = box_font.render(
            f"Boxes: {self.box_count}", False, (0, 50, 0)
        )

        BOX_Y = 800
        box_x = self.preview_rect.centerx - box_text.get_width() // 2
        box_y = BOX_Y

        self.screen.blit(shadow, (box_x + 2, box_y + 2))
        self.screen.blit(box_text, (box_x, box_y))

        self.manager.update(0.016)
        self.manager.draw_ui(self.screen)
        
        # UI Border Padding
        pygame.draw.rect(self.screen, BORDER_COLOR, (0, 0, window_width, window_height), BORDER_WIDTH)