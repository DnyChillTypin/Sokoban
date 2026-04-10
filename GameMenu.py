import pygame
import pygame_gui
from settings import *

class GameMenu:
    def __init__(self):
        self.manager = pygame_gui.UIManager((window_width, window_height), UI_THEME)
        self.ai_dropdown_open = False
        self.expanded = False
        self.selected_algos = set() 
        self.is_playing = False 
        
        self.algo_results = {algo: None for algo in ALGORITHMS}
        self.execution_cache = {}
        
        from radar_chart import RadarChart
        color_map = {
            'A*': (255, 50, 50),       # Red
            'BFS': (50, 50, 255),      # Blue
            'DFS': (50, 255, 50),      # Green
            'BestFS': (255, 255, 50),  # Yellow
            'Dijkstra': (255, 130, 0)  # Orange
        }
        self.radar_chart = RadarChart(center=(680, 450), radius=180, font_size=20, color_map=color_map)
        
        # Load assets using settings.py
        self.custom_font = pygame.font.Font(font_path, 24)
        self.coffee_icon = pygame.image.load(textures['coffee_icon']).convert_alpha()
        
        self.current_move_text = "Moves: 0"
        
        # Screen dimming overlay
        self.dim_surf = pygame.Surface((window_width, window_height))
        self.dim_surf.set_alpha(204) 
        self.dim_surf.fill((0, 0, 0))

        self.create_bg_pattern()
        self.setup_ui()

    def create_bg_pattern(self):
        dark_tile = pygame.image.load(textures['menu_dark']).convert_alpha()
        light_tile = pygame.image.load(textures['menu_light']).convert_alpha()
        
        tile_w, tile_h = dark_tile.get_size()
        max_width = (window_width // 2) + 160
        
        self.bg_pattern = pygame.Surface((max_width, window_height)) 
        
        for y in range(0, window_height, tile_h):
            for x in range(0, max_width, tile_w):
                is_even_tile = ((x // tile_w) + (y // tile_h)) % 2 == 0
                tile = light_tile if is_even_tile else dark_tile
                self.bg_pattern.blit(tile, (x, y))
                    
        # Apply shadow
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

        btn_w, btn_h, btn_x = 240, 80, 30 
        move_y = 20
        ai_y = move_y + btn_h + 10 
        hint_y = ai_y + btn_h + 10
        play_x = btn_x + btn_w + 10 
        play_w = 80
        
        # Core Buttons
        self.move_display = self._create_btn(btn_x, move_y, btn_w, btn_h, '#move_panel')
        self.ai_toggle_btn = self._create_btn(btn_x, ai_y, btn_w, btn_h, '#ai_btn')
        self.hint_btn = self._create_btn(btn_x, hint_y, btn_w, btn_h, '#hint_btn')
        
        undo_y = hint_y + (btn_h * 2) + 20
        reset_y = undo_y + btn_h + 10
        self.undo_btn = self._create_btn(btn_x, undo_y, btn_w, btn_h, '#ai_btn')
        self.reset_btn = self._create_btn(btn_x, reset_y, btn_w, btn_h, '#ai_btn')
        self.play_btn = self._create_btn(play_x, ai_y, play_w, btn_h, '#play_btn', visible=False)

        # Dropdown Background
        self.dropdown_bg = self._create_btn(btn_x - 20, ai_y + btn_h, 280, 600, '#dropdown_bg', visible=False)

        # Algorithm & Result Buttons
        self.algo_btns = {}
        self.result_btns = {} 
        current_y = (ai_y + btn_h) + 100 
        
        for algo in ALGORITHMS:
            self.algo_btns[algo] = self._create_btn(btn_x, current_y, btn_w, btn_h, '#algo_btn', visible=False)
            self.result_btns[algo] = self._create_btn(play_x + 20, current_y, play_w, btn_h, '#result_btn', visible=False)
            current_y += btn_h + 15 

        # Expansion Toggle
        tgl_w, tgl_h = 80, 240
        self.toggle_btn = self._create_btn(menu_width - (tgl_w // 2), (window_height // 2) - (tgl_h // 2), tgl_w, tgl_h, '#toggle_btn')

    # Helper method to keep setup_ui clean
    def _create_btn(self, x, y, w, h, obj_id, visible=True):
        return pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(x, y, w, h), text="", 
            manager=self.manager, container=self.panel if obj_id != '#toggle_btn' else None,
            visible=visible, object_id=obj_id
        )

    def toggle_expansion(self):
        self.expanded = not self.expanded
        target_width = ((window_width // 2) + 160) if self.expanded else menu_width

        self.panel.set_dimensions((target_width, window_height))
        
        new_toggle_x = target_width - (self.toggle_btn.rect.width // 2)
        self.toggle_btn.set_relative_position((new_toggle_x, self.toggle_btn.rect.y))

        if self.expanded:
            self.toggle_btn.select()
            self.toggle_btn.update(0)
        else:
            self.toggle_btn.unselect()
            self.toggle_btn.update(0)

        if not self.expanded and self.ai_dropdown_open:
            self.toggle_ai_dropdown()

    def toggle_ai_dropdown(self):
        self.ai_dropdown_open = not self.ai_dropdown_open
        
        if self.ai_dropdown_open:
            self.dropdown_bg.show()
            self.ai_toggle_btn.select() 
            self.ai_toggle_btn.update(0)
            self.play_btn.show()
            self.hint_btn.hide() 
            self.undo_btn.hide()
            self.reset_btn.hide()            
            for name, btn in self.algo_btns.items():
                btn.show()
                if name in self.selected_algos:
                    btn.select()
                    if self.algo_results[name] is not None:
                        self.result_btns[name].show()
        else:
            self.dropdown_bg.hide()
            self.ai_toggle_btn.unselect() 
            self.ai_toggle_btn.update(0)
            self.play_btn.hide()
            self.hint_btn.show()
            self.undo_btn.show()
            self.reset_btn.show()            
            for btn in self.algo_btns.values(): btn.hide()
            for res_btn in self.result_btns.values(): res_btn.hide()

    def update_moves(self, count, level_num):
        self.current_move_text = f"Moves: {count}"

    def reset_ai_menu(self):
        self.algo_results = {algo: None for algo in ALGORITHMS}
        self.is_playing = False
        self.play_btn.unselect()
        self.play_btn.update(0)
        self.hint_btn.enable() 
        self.execution_cache.clear()
        self.radar_chart.update_data({}) # Clear chart snapshots
        for res_btn in self.result_btns.values(): res_btn.hide()

    def show_results(self, results_dict, full_metrics=None):
        for algo, path in results_dict.items():
            self.algo_results[algo] = len(path) if path is not None else "FAIL"
            if self.ai_dropdown_open and algo in self.selected_algos:
                self.result_btns[algo].show()
        
        if full_metrics:
            self.execution_cache.update(full_metrics)
            self.radar_chart.update_data(self.execution_cache)

    def process_events(self, event):
        self.manager.process_events(event)

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            ui = event.ui_element
            
            if ui == self.play_btn:
                self.is_playing = not self.is_playing
                if self.is_playing:
                    self.play_btn.select()
                    self.play_btn.update(0)
                    self.hint_btn.disable() 
                else:
                    self.play_btn.unselect()
                    self.play_btn.update(0)
                    self.hint_btn.enable() 
                return "PLAY_CLICKED"
            
            elif ui == self.hint_btn:
                return "HINT_CLICKED"
                
            elif ui == self.undo_btn:
                return "UNDO_CLICKED"
                
            elif ui == self.reset_btn:
                return "RESET_CLICKED"
                
            elif ui in self.result_btns.values():
                clicked_algo = next((name for name, btn in self.result_btns.items() if btn == ui), None)
                if clicked_algo and self.algo_results[clicked_algo] != "FAIL":
                    self.hint_btn.disable() 
                    return f"PLAYBACK_{clicked_algo}"
                
            elif ui == self.ai_toggle_btn:
                if not self.expanded: self.toggle_expansion()
                self.toggle_ai_dropdown()
                
            elif ui == self.toggle_btn:
                self.toggle_expansion()

            elif ui in self.algo_btns.values():
                clicked_algo = next((name for name, btn in self.algo_btns.items() if btn == ui), None)
                
                if clicked_algo in self.selected_algos:
                    self.selected_algos.remove(clicked_algo)
                    self.algo_btns[clicked_algo].unselect() 
                    self.algo_btns[clicked_algo].update(0)
                    self.result_btns[clicked_algo].hide()
                else:
                    self.selected_algos.add(clicked_algo)
                    self.algo_btns[clicked_algo].select() 
                    self.algo_btns[clicked_algo].update(0)
                    if self.algo_results[clicked_algo] is not None:
                        self.result_btns[clicked_algo].show()
        return None

    def update(self, time_delta):
        self.manager.update(time_delta)

    def draw(self, surface):
        if self.expanded:
            surface.blit(self.dim_surf, (0, 0))
            
        current_width = ((window_width // 2) + 160) if self.expanded else menu_width
        surface.blit(self.bg_pattern, (0, 0), area=pygame.Rect(0, 0, current_width, window_height))
            
        if self.ai_dropdown_open:
            self.radar_chart.draw(surface, visible_algos=self.selected_algos)
            
        self.manager.draw_ui(surface)
        
        # Render Text Helper
        def draw_text(text, btn, color=(255, 255, 255), manual_y=None):
            surf = self.custom_font.render(text, True, color)
            base_y = manual_y if manual_y is not None else (37 if btn.is_selected else 32)
            rect = surf.get_rect(centerx=btn.rect.centerx, centery=btn.rect.y + base_y)
            if btn.held and btn.is_enabled: rect.y += 5
            surface.blit(surf, rect)

        draw_text(self.current_move_text, self.move_display)
        
        # AI Solver Button Text
        draw_text("AI Solver", self.ai_toggle_btn, (0, 0, 0))

        def draw_pixel_star(surf, cx, cy, color):
            """Draws a small 5x5 pixel-art style star"""
            offsets = [(0,0), (0,-1), (0,1), (-1,0), (1,0), (0,-2), (0,2), (-2,0), (2,0), (-1,-1), (1,-1), (-1,1), (1,1)]
            for dx, dy in offsets:
                surf.set_at((cx + dx, cy + dy), color)

        # Hint Button / Coffee Icon
        if self.hint_btn.visible:
            if not self.hint_btn.is_enabled:
                icon_rect = self.coffee_icon.get_rect(centerx=self.hint_btn.rect.centerx, centery=self.hint_btn.rect.y + 35)
                self.coffee_icon.set_alpha(255)
                surface.blit(self.coffee_icon, icon_rect)
            else:
                draw_text("Hint", self.hint_btn, (0, 0, 0))
                
        if self.undo_btn.visible:
            draw_text("Undo", self.undo_btn, (0, 0, 0))
        if self.reset_btn.visible:
            draw_text("Reset", self.reset_btn, (0, 0, 0))
        
        # Dropdown Items
        if self.ai_dropdown_open:
            for algo, btn in self.algo_btns.items():
                color = (255, 255, 255)
                if algo.lower() == "a*":
                    # Special rendering for A*
                    display_name = "A"
                    draw_text(display_name, btn, color)
                    # Draw star next to A
                    y_offset = 37 if btn.is_selected else 32
                    star_x = btn.rect.centerx + 12
                    star_y = btn.rect.y + y_offset - 10
                    if btn.held and btn.is_enabled: star_y += 5
                    draw_pixel_star(surface, star_x, star_y, color)
                else:
                    draw_text(algo.upper(), btn, color)
                
                res_btn = self.result_btns[algo]
                if res_btn.visible:
                    draw_text(str(self.algo_results[algo]), res_btn)
                    
        if self.ai_dropdown_open:
            self.radar_chart.draw_tooltip(surface)