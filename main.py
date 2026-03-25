import pygame
import pygame_gui
import sys
import os
from settings import *
from level import Level
from player import Player

class Game:
    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode((window_width, window_height))
        pygame.display.set_caption('Sokoban AI')
        
        self.bg_image = pygame.image.load(bg_image_path).convert_alpha()
        self.clock = pygame.time.Clock()
        self.running = True

        self.ui_manager = pygame_gui.UIManager((window_width, window_height))
        self.menu_expanded = False
        self.moves_count = 0
        
        self.ai_dropdown_open = False
        # --- CHANGED: Now using a Set so we can hold multiple choices ---
        self.selected_algos = {'A*'} 
        
        self.setup_ui()

        self.current_level_num = 0
        self.load_current_level()

    def setup_ui(self):
        self.menu_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(0, 0, menu_width, window_height),
            starting_height=1,
            manager=self.ui_manager
        )

        self.move_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 20, 250, 30),
            text="Level 0 Moves: 0",
            manager=self.ui_manager,
            container=self.menu_panel
        )

        self.ai_toggle_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(10, 70, 200, 40),
            text="AI Solver ▼",
            manager=self.ui_manager,
            container=self.menu_panel
        )

        self.algo_btns = {}
        y_offset = 110
        for algo in ['A*', 'BFS', 'DFS']:
            # --- CHANGED: Check if it's in our set of selected algorithms ---
            box_text = f"[X] {algo}" if algo in self.selected_algos else f"[ ] {algo}"
            btn = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(10, y_offset, 200, 30),
                text=box_text,
                manager=self.ui_manager,
                container=self.menu_panel,
                visible=False
            )
            self.algo_btns[algo] = btn
            y_offset += 30

        self.run_solver_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(10, y_offset + 5, 200, 40),
            text="Run Solver",
            manager=self.ui_manager,
            container=self.menu_panel,
            visible=False
        )

        self.toggle_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(menu_width - 30, (window_height // 2) - 40, 30, 80),
            text=">",
            manager=self.ui_manager,
            container=self.menu_panel
        )

    def toggle_menu(self):
        self.menu_expanded = not self.menu_expanded
        target_width = (window_width // 2) if self.menu_expanded else menu_width

        self.menu_panel.set_dimensions((target_width, window_height))
        self.toggle_btn.set_relative_position((target_width - 30, (window_height // 2) - 40))
        self.toggle_btn.set_text("<" if self.menu_expanded else ">")
        
        if not self.menu_expanded and self.ai_dropdown_open:
            self.toggle_ai_dropdown()

    def toggle_ai_dropdown(self):
        self.ai_dropdown_open = not self.ai_dropdown_open
        self.ai_toggle_btn.set_text("AI Solver ▲" if self.ai_dropdown_open else "AI Solver ▼")
        
        for btn in self.algo_btns.values():
            btn.show() if self.ai_dropdown_open else btn.hide()
            
        self.run_solver_btn.show() if self.ai_dropdown_open else self.run_solver_btn.hide()

    def update_move_label(self):
        self.move_label.set_text(f"Level {self.current_level_num} Moves: {self.moves_count}")

    def load_current_level(self):
        self.level = Level(self.current_level_num)
        self.player = Player(
            self.level.player_start_x,
            self.level.player_start_y,
            self.level.images['player']
        )
        self.map_width = self.level.columns * scaled_tile
        self.map_height = self.level.rows * scaled_tile
        self.map_surface = pygame.Surface((self.map_width, self.map_height), pygame.SRCALPHA)
        
        self.history = []
        self.moves_count = 0
        if hasattr(self, 'move_label'):
            self.update_move_label()

    def quit_game(self):
        pygame.quit()
        sys.exit()

    def run(self):
        while self.running:
            time_delta = self.clock.tick(fps) / 1000.0
            self.event()
            self.update(time_delta)
            self.draw()

    def event(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game()

            self.ui_manager.process_events(event)

            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.toggle_btn:
                    self.toggle_menu()
                
                elif event.ui_element == self.ai_toggle_btn:
                    if not self.menu_expanded:
                        self.toggle_menu()
                    self.toggle_ai_dropdown()

                elif event.ui_element == self.run_solver_btn:
                    # Prints out all currently selected algorithms!
                    print(f"Executing Solver Engine with: {', '.join(self.selected_algos)}")
                
                else:
                    for algo_name, btn_element in self.algo_btns.items():
                        if event.ui_element == btn_element:
                            # --- CHANGED: True checkbox toggle logic ---
                            if algo_name in self.selected_algos:
                                self.selected_algos.remove(algo_name) # Uncheck
                            else:
                                self.selected_algos.add(algo_name)    # Check
                            
                            print(f"Currently Selected: {self.selected_algos}")
                            
                            # Update just the button that was clicked
                            btn_element.set_text(f"[X] {algo_name}" if algo_name in self.selected_algos else f"[ ] {algo_name}")

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: self.quit_game()
                elif event.key == pygame.K_r: self.load_current_level()
                elif event.key == pygame.K_n:
                    next_level_path = f'levels/{self.current_level_num + 1}.txt'
                    if os.path.exists(next_level_path):
                        self.current_level_num += 1
                        self.load_current_level()
                elif event.key == pygame.K_p:
                    if self.current_level_num > 0:
                        self.current_level_num -= 1
                        self.load_current_level()

                elif event.key == pygame.K_z:
                    if len(self.history) > 0:
                        last_state = self.history.pop()
                        self.player.x, self.player.y = last_state['player']
                        self.level.boxes = [list(box) for box in last_state['boxes']]

                elif event.key in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]:
                    old_x, old_y = self.player.x, self.player.y
                    old_boxes = [list(box) for box in self.level.boxes] 

                    if event.key == pygame.K_UP: self.player.move(0, -1, self.level)
                    elif event.key == pygame.K_DOWN: self.player.move(0, 1, self.level)
                    elif event.key == pygame.K_LEFT: self.player.move(-1, 0, self.level)
                    elif event.key == pygame.K_RIGHT: self.player.move(1, 0, self.level)

                    if self.player.x != old_x or self.player.y != old_y:
                        self.history.append({'player': (old_x, old_y), 'boxes': old_boxes})
                        self.moves_count += 1
                        self.update_move_label()

    def update(self, time_delta):
        self.ui_manager.update(time_delta)
        
        if self.level.is_completed():
            print(f'Level {self.current_level_num} cleared')
            self.current_level_num += 1

            next_level_path = f'levels/{self.current_level_num}.txt'
            if os.path.exists(next_level_path):
                self.load_current_level()
            else:
                print("All levels cleared")
                self.quit_game()

    def draw(self):
        self.screen.fill((0, 0, 0))
        screen_rect = self.screen.get_rect()
        bg_rect = self.bg_image.get_rect(midbottom=screen_rect.midbottom)
        self.screen.blit(self.bg_image, bg_rect)
        
        self.map_surface.fill((0, 0, 0, 0))
        self.level.draw(self.map_surface)
        self.player.draw(self.map_surface)
        
        game_rect = pygame.Rect(menu_width, 0, game_width, window_height)
        map_rect = self.map_surface.get_rect(center=game_rect.center)
        self.screen.blit(self.map_surface, map_rect)

        if self.menu_expanded:
            dim_surf = pygame.Surface((window_width, window_height), pygame.SRCALPHA)
            dim_surf.fill((0, 0, 0, 102)) 
            self.screen.blit(dim_surf, (0, 0))
        
        self.ui_manager.draw_ui(self.screen)
        pygame.display.update()

if __name__ == '__main__':
    sokoban = Game()
    sokoban.run()