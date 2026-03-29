import pygame
import pygame_gui
from settings import *

class GameMenu:
    def __init__(self):
        self.manager = pygame_gui.UIManager((window_width, window_height), 'theme.json')
        self.ai_dropdown_open = False
        self.expanded = False
        self.selected_algos = set() 
        self.is_playing = False 
        
        self.algo_results = {algo: None for algo in ['BFS', 'DFS', 'BestFS', 'Dijkstra', 'A*']}
        
        self.custom_font = pygame.font.Font('assets/PIXY.ttf', 24)
        
        self.current_move_text = "Moves: 0"
        
        self.dim_surf = pygame.Surface((window_width, window_height))
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
        dark_filter.set_alpha(150) 
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
        
        # 1. Move Panel 
        move_y = 20
        self.move_display = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(btn_x, move_y, btn_width, btn_height),
            text="", 
            manager=self.manager,
            container=self.panel,
            object_id='#move_panel' 
        )

        # 2. AI Solver Button 
        ai_y = move_y + btn_height + 10 
        self.ai_toggle_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(btn_x, ai_y, btn_width, btn_height),
            text="", 
            manager=self.manager,
            container=self.panel,
            object_id='#ai_btn' 
        )

        # 3. Hint Button 
        # --- CHANGED: Visible is now True by default (removed visible=False) ---
        hint_y = ai_y + btn_height + 10
        self.hint_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(btn_x, hint_y, btn_width, btn_height),
            text="", 
            manager=self.manager,
            container=self.panel,
            object_id='#hint_btn' 
        )

        # 4. Play Button 
        play_x = btn_x + btn_width + 10 
        play_width = 80
        
        self.play_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(play_x, ai_y, play_width, btn_height), 
            text="", 
            manager=self.manager,
            container=self.panel,
            visible=False,
            object_id='#play_btn'
        )

        # 5. Dropdown Background 
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

        # 6. Algorithm Toggle Buttons & Result Buttons
        self.algo_btns = {}
        self.result_btns = {} 
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
            
            res_btn = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(play_x + 20, current_y, play_width, btn_height),
                text="", 
                manager=self.manager,
                container=self.panel,
                visible=False, 
                object_id='#result_btn'
            )
            self.result_btns[algo] = res_btn
            
            current_y += btn_height + 15 

        # 7. Expansion Toggle
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

        # --- CHANGED: Cleaned out the hint hiding logic from here! ---
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
            self.play_btn.show()
            
            # Hide the Hint Button when the dropdown falls over it
            self.hint_btn.hide() 
            
            for name, btn in self.algo_btns.items():
                btn.show()
                if name in self.selected_algos:
                    btn.select()
                    
            for name, res_btn in self.result_btns.items():
                if self.algo_results[name] is not None and name in self.selected_algos:
                    res_btn.show()
        else:
            self.dropdown_bg.hide()
            self.ai_toggle_btn.unselect() 
            self.play_btn.hide()
            
            # --- CHANGED: Always show the hint button when dropdown is closed ---
            self.hint_btn.show()
            
            for btn in self.algo_btns.values():
                btn.hide()
            for res_btn in self.result_btns.values():
                res_btn.hide()

    def update_moves(self, count, level_num):
        self.current_move_text = f"Moves: {count}"

    def reset_ai_menu(self):
        self.algo_results = {algo: None for algo in ['BFS', 'DFS', 'BestFS', 'Dijkstra', 'A*']}
        self.is_playing = False
        self.play_btn.unselect()
        for res_btn in self.result_btns.values():
            res_btn.hide()

    def show_results(self, results_dict):
        for algo, path in results_dict.items():
            if path is not None:
                self.algo_results[algo] = len(path)
            else:
                self.algo_results[algo] = "FAIL"
                
            if self.ai_dropdown_open and algo in self.selected_algos:
                self.result_btns[algo].show()

    def process_events(self, event):
        self.manager.process_events(event)

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.play_btn:
                self.is_playing = not self.is_playing
                if self.is_playing:
                    self.play_btn.select()
                else:
                    self.play_btn.unselect()
                return "PLAY_CLICKED"
            
            elif event.ui_element == self.hint_btn:
                return "HINT_CLICKED"
                
            elif event.ui_element in self.result_btns.values():
                clicked_algo = None
                for name, res_btn in self.result_btns.items():
                    if res_btn == event.ui_element:
                        clicked_algo = name
                        break
                if clicked_algo and self.algo_results[clicked_algo] != "FAIL":
                    return f"PLAYBACK_{clicked_algo}"
                
            elif event.ui_element == self.ai_toggle_btn:
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
                    self.result_btns[clicked_algo].hide()
                else:
                    self.selected_algos.add(clicked_algo)
                    self.algo_btns[clicked_algo].select() 
                    if self.algo_results[clicked_algo] is not None:
                        self.result_btns[clicked_algo].show()

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

        if self.hint_btn.visible:
            hint_surf = self.custom_font.render("Hint", True, (0, 0, 0))
            hint_rect = hint_surf.get_rect(centerx=self.hint_btn.rect.centerx, centery=self.hint_btn.rect.y + 32)
            if self.hint_btn.hovered and mouse_down:
                hint_rect.y += 5 
            surface.blit(hint_surf, hint_rect)
        
        if self.ai_dropdown_open:
            for algo, btn in self.algo_btns.items():
                
                color = (150, 150, 150) if algo == 'Dijkstra' else (255, 255, 255)
                algo_surf = self.custom_font.render(algo, True, color)
                algo_rect = algo_surf.get_rect(centerx=btn.rect.centerx, centery=btn.rect.y + 32)
                
                if algo in self.selected_algos or (btn.hovered and mouse_down):
                    algo_rect.y += 5
                surface.blit(algo_surf, algo_rect)
                
                res_btn = self.result_btns[algo]
                if res_btn.visible:
                    res_text = str(self.algo_results[algo])
                    res_surf = self.custom_font.render(res_text, True, (255, 255, 255))
                    res_rect = res_surf.get_rect(centerx=res_btn.rect.centerx, centery=res_btn.rect.y + 32)
                    
                    if res_btn.hovered and mouse_down:
                        res_rect.y += 5
                    surface.blit(res_surf, res_rect)