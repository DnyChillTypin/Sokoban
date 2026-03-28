import pygame
import pygame_gui
from settings import *

class GameMenu:
    def __init__(self):
        self.manager = pygame_gui.UIManager((window_width, window_height), 'theme.json')
        self.ai_dropdown_open = False
        
        self.setup_ui()

    def setup_ui(self):
        self.panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(0, 0, menu_width, window_height),
            starting_height=1,
            manager=self.manager
        )

        # --- 1. AI Solver Button (240x80) ---
        btn_width = 240
        btn_height = 80
        btn_x = 30 # Shifted the main button slightly right so the wider dropdown doesn't clip off the screen
        btn_y = 50
        
        self.ai_toggle_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(btn_x, btn_y, btn_width, btn_height),
            text="AI Solver",
            manager=self.manager,
            container=self.panel,
            object_id='#ai_btn' 
        )

        # --- 2. Dropdown Background (280x600) ---
        dropdown_width = 280
        # Center the dropdown perfectly under the button
        dropdown_x = btn_x - 20 
        
        # --- SCALED: Locked in the new 600px height ---
        dropdown_height = 600 
        
        self.dropdown_bg = pygame_gui.elements.UIButton(
            # Y position locks exactly to the bottom pixel of the button
            relative_rect=pygame.Rect(dropdown_x, btn_y + btn_height, dropdown_width, dropdown_height),
            text="", 
            manager=self.manager,
            container=self.panel,
            visible=False,
            object_id='#dropdown_bg' 
        )

    def toggle_ai_dropdown(self):
        self.ai_dropdown_open = not self.ai_dropdown_open
        if self.ai_dropdown_open:
            self.dropdown_bg.show()
            self.ai_toggle_btn.select()
        else:
            self.dropdown_bg.hide()
            self.ai_toggle_btn.unselect()

    # --- STUBS: Prevents main.py from crashing while we build ---
    def update_moves(self, count, level_num):
        pass 

    def reset_ai_menu(self):
        pass

    def show_results(self, results_dict):
        pass

    # --- CORE EVENT LOOP ---
    def process_events(self, event):
        self.manager.process_events(event)

        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.ai_toggle_btn:
                self.toggle_ai_dropdown()
        return None

    def update(self, time_delta):
        self.manager.update(time_delta)

    def draw(self, surface):
        self.manager.draw_ui(surface)