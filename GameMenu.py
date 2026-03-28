import pygame
import pygame_gui
from settings import *

class GameMenu:
    def __init__(self):
        self.manager = pygame_gui.UIManager((window_width, window_height), 'theme.json')
        self.ai_dropdown_open = False
        self.expanded = False
        
        self.dim_surf = pygame.Surface((window_width, window_height), pygame.SRCALPHA)
        self.dim_surf.fill((0, 0, 0, 128))

        # --- NEW: Generate the checkerboard canvas! ---
        self.create_bg_pattern()
        self.setup_ui()

    def create_bg_pattern(self):
        # Load the tiles
        dark_tile = pygame.image.load('assets/graphics/Buttons/MenuFloorDark5x.png').convert_alpha()
        light_tile = pygame.image.load('assets/graphics/Buttons/MenuFloorLight5x.png').convert_alpha()
        
        # Get their dimensions dynamically so you can change the art later without breaking the math
        tile_w = dark_tile.get_width()
        tile_h = dark_tile.get_height()
        
        # We make the canvas as big as the menu's MAXIMUM expanded size
        max_width = window_width // 2
        self.bg_pattern = pygame.Surface((max_width, window_height))
        
        # Nested loop to paint the checkerboard onto our hidden canvas
        for y in range(0, window_height, tile_h):
            for x in range(0, max_width, tile_w):
                col = x // tile_w
                row = y // tile_h
                
                # If the column + row is an even number, paint light. Odd, paint dark.
                if (col + row) % 2 == 0:
                    self.bg_pattern.blit(light_tile, (x, y))
                else:
                    self.bg_pattern.blit(dark_tile, (x, y))

    def setup_ui(self):
        self.panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(0, 0, menu_width, window_height),
            starting_height=1,
            manager=self.manager
        )

        btn_width = 240
        btn_height = 80
        btn_x = 30 
        
        # 1. The Red Move Panel
        move_y = 20
        self.move_display = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(btn_x, move_y, btn_width, btn_height),
            text="Level 0 Moves: 0",
            manager=self.manager,
            container=self.panel,
            object_id='#move_panel' 
        )

        # 2. AI Solver Button
        ai_y = move_y + btn_height + 10 
        self.ai_toggle_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(btn_x, ai_y, btn_width, btn_height),
            text="AI Solver",
            manager=self.manager,
            container=self.panel,
            object_id='#ai_btn' 
        )

        # 3. Dropdown Background
        dropdown_width = 280
        dropdown_x = btn_x - 20 
        dropdown_height = 600 
        
        self.dropdown_bg = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(dropdown_x, ai_y + btn_height, dropdown_width, dropdown_height),
            text="", 
            manager=self.manager,
            container=self.panel,
            visible=False,
            object_id='#dropdown_bg' 
        )

        # 4. The Expansion Toggle Button
        self.toggle_width = 80
        self.toggle_height = 240
        toggle_x = menu_width - (self.toggle_width // 2)
        toggle_y = (window_height // 2) - (self.toggle_height // 2)

        self.toggle_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(toggle_x, toggle_y, self.toggle_width, self.toggle_height),
            text="", 
            manager=self.manager,
            object_id='#toggle_btn'
        )

    def toggle_expansion(self):
        self.expanded = not self.expanded
        target_width = (window_width // 2) if self.expanded else menu_width

        self.panel.set_dimensions((target_width, window_height))
        
        new_toggle_x = target_width - (self.toggle_width // 2)
        toggle_y = (window_height // 2) - (self.toggle_height // 2)
        self.toggle_btn.set_relative_position((new_toggle_x, toggle_y))

        if not self.expanded and self.ai_dropdown_open:
            self.toggle_ai_dropdown()

    def toggle_ai_dropdown(self):
        self.ai_dropdown_open = not self.ai_dropdown_open
        if self.ai_dropdown_open:
            self.dropdown_bg.show()
            self.ai_toggle_btn.select() 
        else:
            self.dropdown_bg.hide()
            self.ai_toggle_btn.unselect() 

    def update_moves(self, count, level_num):
        self.move_display.set_text(f"Level {level_num} Moves: {count}")

    def reset_ai_menu(self):
        pass

    def show_results(self, results_dict):
        pass

    def process_events(self, event):
        self.manager.process_events(event)

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.ai_toggle_btn:
                if not self.expanded:
                    self.toggle_expansion()
                self.toggle_ai_dropdown()
                
            elif event.ui_element == self.toggle_btn:
                self.toggle_expansion()
                
        return None

    def update(self, time_delta):
        self.manager.update(time_delta)

    def draw(self, surface):
        # 1. Draw the dimming shadow first (if expanded)
        if self.expanded:
            surface.blit(self.dim_surf, (0, 0))
            
        # 2. Draw our custom checkerboard exactly the width of the current menu
        current_width = (window_width // 2) if self.expanded else menu_width
        surface.blit(self.bg_pattern, (0, 0), area=pygame.Rect(0, 0, current_width, window_height))
            
        # 3. Draw the UI buttons on top of everything (The panel now draws your 5px border automatically!)
        self.manager.draw_ui(surface)
            
        # 2. Draw our custom checkerboard exactly the width of the current menu
        current_width = (window_width // 2) if self.expanded else menu_width
        surface.blit(self.bg_pattern, (0, 0), area=pygame.Rect(0, 0, current_width, window_height))
            
        # 3. Draw the UI buttons on top of everything
        self.manager.draw_ui(surface)