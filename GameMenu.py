import pygame
import pygame_gui
from settings import *

class GameMenu:
    def __init__(self):
        self.manager = pygame_gui.UIManager((window_width, window_height), 'theme.json')
        self.ai_dropdown_open = False
        self.expanded = False
        self.selected_algos = set() 
        
        self.custom_font = pygame.font.Font('assets/PIXY.ttf', 24)
        
        self.current_move_text = "Level 0 Moves: 0"
        
        self.dim_surf = pygame.Surface((window_width, window_height), pygame.SRCALPHA)
        self.dim_surf.set_alpha(204)
        self.dim_surf.fill((0, 0, 0))

        self.create_bg_pattern()
        self.setup_ui()

    def create_bg_pattern(self):
        dark_tile = pygame.image.load('assets/graphics/Buttons/MenuFloorDark5x.png').convert_alpha()
        light_tile = pygame.image.load('assets/graphics/Buttons/MenuFloorLight5x.png').convert_alpha()
        
        tile_w = dark_tile.get_width()
        tile_h = dark_tile.get_height()
        
        max_width = window_width // 2
        self.bg_pattern = pygame.Surface((max_width, window_height))
        
        for y in range(0, window_height, tile_h):
            for x in range(0, max_width, tile_w):
                col = x // tile_w
                row = y // tile_h
                
                if (col + row) % 2 == 0:
                    self.bg_pattern.blit(light_tile, (x, y))
                else:
                    self.bg_pattern.blit(dark_tile, (x, y))
        
        dark_filter = pygame.Surface((max_width, window_height))
        dark_filter.set_alpha(60) 
        dark_filter.fill((0, 0, 0))
        
        self.bg_pattern.blit(dark_filter, (0, 0))
        
    def setup_ui(self):
        self.panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(0, 0, menu_width, window_height),
            starting_height=1,
            manager=self.manager
        )

        btn_width = 240
        btn_height = 80
        btn_x = 30 
        
        move_y = 20
        self.move_display = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(btn_x, move_y, btn_width, btn_height),
            text="", 
            manager=self.manager,
            container=self.panel,
            object_id='#move_panel' 
        )

        ai_y = move_y + btn_height + 10 
        self.ai_toggle_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(btn_x, ai_y, btn_width, btn_height),
            text="", 
            manager=self.manager,
            container=self.panel,
            object_id='#ai_btn' 
        )

        dropdown_y = ai_y + btn_height
        dropdown_width = 280
        dropdown_x = btn_x - 20 
        dropdown_height = 600 
        
        self.dropdown_bg = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(dropdown_x, dropdown_y, dropdown_width, dropdown_height),
            text="", 
            manager=self.manager,
            container=self.panel,
            visible=False,
            object_id='#dropdown_bg' 
        )

        self.algo_btns = {}
        algo_names = ['BFS', 'DFS', 'BestFS', 'Dijkstra', 'A*']
        current_y = dropdown_y + 100 
        
        for algo in algo_names:
            btn = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(btn_x, current_y, btn_width, btn_height),
                text="", 
                manager=self.manager,
                container=self.panel,
                visible=False,
                object_id='#algo_btn'
            )
            self.algo_btns[algo] = btn
            current_y += btn_height + 15 

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

        if self.expanded:
            self.toggle_btn.select()
        else:
            self.toggle_btn.unselect()

        if not self.expanded and self.ai_dropdown_open:
            self.toggle_ai_dropdown()

    def toggle_ai_dropdown(self):
        self.ai_dropdown_open = not self.ai_dropdown_open
        if self.ai_dropdown_open:
            self.dropdown_bg.show()
            self.ai_toggle_btn.select() 
            
            for name, btn in self.algo_btns.items():
                btn.show()
                if name in self.selected_algos:
                    btn.select()
        else:
            self.dropdown_bg.hide()
            self.ai_toggle_btn.unselect() 
            for btn in self.algo_btns.values():
                btn.hide()

    def update_moves(self, count, level_num):
        self.current_move_text = f"Level {level_num} Moves: {count}"

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

            elif event.ui_element in self.algo_btns.values():
                clicked_algo = None
                for name, btn in self.algo_btns.items():
                    if btn == event.ui_element:
                        clicked_algo = name
                        break
                
                if clicked_algo == 'Dijkstra':
                    return None
                
                if clicked_algo in self.selected_algos:
                    self.selected_algos.remove(clicked_algo)
                    self.algo_btns[clicked_algo].unselect() 
                else:
                    self.selected_algos.add(clicked_algo)
                    self.algo_btns[clicked_algo].select() 

        return None

    def update(self, time_delta):
        self.manager.update(time_delta)

    def draw(self, surface):
        if self.expanded:
            surface.blit(self.dim_surf, (0, 0))
            
        current_width = (window_width // 2) if self.expanded else menu_width
        surface.blit(self.bg_pattern, (0, 0), area=pygame.Rect(0, 0, current_width, window_height))
            
        self.manager.draw_ui(surface)

        mouse_down = pygame.mouse.get_pressed()[0]
        
        move_surf = self.custom_font.render(self.current_move_text, True, (255, 255, 255))
        move_rect = move_surf.get_rect(centerx=self.move_display.rect.centerx, centery=self.move_display.rect.y + 32)
        surface.blit(move_surf, move_rect)

        ai_surf = self.custom_font.render("AI Solver", True, (0, 0, 0))
        ai_rect = ai_surf.get_rect(centerx=self.ai_toggle_btn.rect.centerx, centery=self.ai_toggle_btn.rect.y + 32)
        
        if self.ai_dropdown_open or (self.ai_toggle_btn.hovered and mouse_down):
            ai_rect.y += 5 
        surface.blit(ai_surf, ai_rect)
        
        if self.ai_dropdown_open:
            for algo, btn in self.algo_btns.items():
                color = (150, 150, 150) if algo == 'Dijkstra' else (255, 255, 255)
                algo_surf = self.custom_font.render(algo, True, color)
                
                algo_rect = algo_surf.get_rect(centerx=btn.rect.centerx, centery=btn.rect.y + 32)
                
                if algo in self.selected_algos or (btn.hovered and mouse_down):
                    algo_rect.y += 5
                    
                surface.blit(algo_surf, algo_rect)