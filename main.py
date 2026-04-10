import pygame
import sys
import os
import time
import pygame_gui

from settings import *
from level import Level
from player import Player
from GameMenu import GameMenu
from menu import SokobanMenu
from selectLevels import LevelSelection
from solver import SokobanSolver

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((window_width, window_height))
        pygame.display.set_caption('Sokoban AI')
        
        self.bg_image = pygame.image.load(textures['bg_image_path']).convert_alpha()
        self.bg_rect = self.bg_image.get_rect(midbottom=self.screen.get_rect().midbottom)
        self.clock = pygame.time.Clock()
        self.running = True

        self.start_menu = SokobanMenu(self.screen)
        
        self.manager = pygame_gui.UIManager((window_width, window_height))
        self.level_selector = LevelSelection(self.screen, self.manager)
        
        self.game_state = "MAIN_MENU"

        self.menu = GameMenu()
        self.solver_results = {}
        
        # Playback Variables
        self.is_playing_back = False
        self.playback_path = []
        self.playback_timer = 0
        self.playback_speed = 100 
        self.saved_solver_state = None 

        # Hint & Dead State Variables
        self.hint_timer = 0
        self.hint_box_pos = None
        self.dead_state_active = False 
        
        self._load_scaled_textures()

        # UI Overlays
        self.font_large = pygame.font.Font(font_path, 100) 
        self.font_small = pygame.font.Font(font_path, 60)  
        self.font_tiny = pygame.font.Font(font_path, 30)
        self.win_overlay = pygame.Surface((window_width, window_height), pygame.SRCALPHA)
        self.win_overlay.fill((0, 0, 0, 128)) 

        if os.path.exists('levels/test.txt'):
            self.current_level_num = 'test'
            print("Notice: Booting in Sandbox Mode (test.txt found!)")
        else:
            self.current_level_num = 0

        self.moves_count = 0
        self.load_current_level()

    def _load_scaled_textures(self):
        """Helper to scale UI images cleanly"""
        def scale_img(path):
            raw = pygame.image.load(path).convert_alpha()
            return pygame.transform.scale(raw, (scaled_tile, scaled_tile))
            
        self.red_box_img = scale_img(textures['red_box'])
        self.blue_box_img = scale_img(textures['blue_box'])
        self.blue_target_img = scale_img(textures['blue_target'])

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
        
        self.game_rect = pygame.Rect(menu_width, 0, game_width, window_height)
        self.map_rect = self.map_surface.get_rect(center=self.game_rect.center)
        
        self.history = []
        self.moves_count = 0
        self.is_playing_back = False 
        self.saved_solver_state = None
        self._reset_hint_state()
        
        self.level_complete_waiting = False
        self.menu.reset_ai_menu() 
        self.menu.update_moves(self.moves_count, self.current_level_num)

    def _reset_hint_state(self):
        self.dead_state_active = False
        self.hint_timer = 0
        self.hint_box_pos = None

    def handle_movement_input(self, key):
        directions = {
            pygame.K_UP: (0, -1), pygame.K_w: (0, -1),
            pygame.K_DOWN: (0, 1), pygame.K_s: (0, 1),
            pygame.K_LEFT: (-1, 0), pygame.K_a: (-1, 0),
            pygame.K_RIGHT: (1, 0), pygame.K_d: (1, 0)
        }

        if key in directions:
            self._reset_hint_state()
            dx, dy = directions[key]
            old_x, old_y = self.player.x, self.player.y
            old_boxes = [list(box) for box in self.level.boxes] 
            
            self.player.move(dx, dy, self.level)
            
            if self.player.x != old_x or self.player.y != old_y:
                self.history.append({'player': (old_x, old_y), 'boxes': old_boxes})
                self.moves_count += 1
                self.menu.update_moves(self.moves_count, self.current_level_num)
            return True 
        return False

    def execute_hint(self):
        solver = SokobanSolver(self.level)
        current_state = solver.get_initial_state(self.player, self.level)
        result = solver.solve_astar(current_state)

        if result['path']:
            self.dead_state_active = False
            px, py = self.player.x, self.player.y
            boxes = [list(b) for b in self.level.boxes]
            move_map = {'U': (0, -1), 'D': (0, 1), 'L': (-1, 0), 'R': (1, 0)}

            for move in result['path']:
                dx, dy = move_map[move]
                px += dx; py += dy
                
                if [px, py] in boxes:
                    self.hint_box_pos = (px, py)
                    self.hint_timer = 2.0 
                    break
        else:
            self.dead_state_active = True 

    def execute_solvers(self):
        if len(self.menu.selected_algos) == 0:
            self.menu.is_playing = False
            self.menu.play_btn.unselect()
            return
            
        # --- REPLAY LOGIC ---
        # If all selected algorithms already have cached results, just replay the animation
        cached_algos = {algo: self.menu.execution_cache[algo] for algo in self.menu.selected_algos if algo in self.menu.execution_cache}
        if len(cached_algos) == len(self.menu.selected_algos) and len(cached_algos) > 0:
            print(f"Replaying cached results for: {', '.join(cached_algos.keys())}")
            self.menu.radar_chart.trigger_replay(cached_algos)
            self.menu.is_playing = False
            self.menu.play_btn.unselect()
            self.menu.play_btn.update(0)
            self.menu.hint_btn.enable() # RE-ENABLE HINT BUTTON
            return

        print(f"\n{'='*95}\nExecuting Solver Engine...\n{'-'*95}")
        
        self.saved_solver_state = {
            'player': (self.player.x, self.player.y),
            'boxes': [list(box) for box in self.level.boxes]
        }
        
        solver = SokobanSolver(self.level)
        current_state = solver.get_initial_state(self.player, self.level)
        self.solver_results.clear()
        full_metrics = {}
        
        print(f"{'Algorithm':<12} | {'Time (s)':<10} | {'Visited':<10} | {'Generated':<10} | {'Max Mem':<10} | {'Pruned':<8} | {'Pushes':<8} | {'Moves':<8}\n{'-'*95}")
        
        for algo in self.menu.selected_algos:
            # Custom Button State for Animation
            btn = self.menu.algo_custom_btns[algo]
            solver_start_time = time.time()
            
            # Capture the button's visual frame (border/bg) WITHOUT text
            btn.show_text = False
            self.menu.draw(self.screen)
            button_snapshot = self.screen.subsurface(btn.rect).copy()
            btn.show_text = True 
            
            def tick():
                # Only show the loading spinner if calculation takes > 1 second
                if time.time() - solver_start_time > 1.0:
                    btn.is_loading = True
                    # Restore the CLEAN button frame (no text) before drawing spinner
                    self.screen.blit(button_snapshot, btn.rect)
                    btn.draw(self.screen)
                    pygame.display.update(btn.rect)

            if algo == 'BFS': result = solver.solve_bfs(current_state, tick_callback=tick)
            elif algo == 'DFS': result = solver.solve_dfs(current_state, tick_callback=tick)
            elif algo == 'A*': result = solver.solve_astar(current_state, tick_callback=tick)
            elif algo == 'BestFS': result = solver.solve_best_first(current_state, tick_callback=tick)
            elif algo == 'Dijkstra': result = solver.solve_dijkstra(current_state, tick_callback=tick)
                
            btn.is_loading = False
            # Restore final UI state (puts text back)
            self.menu.draw(self.screen)
            pygame.display.update(btn.rect)
                
            self.solver_results[algo] = result['path']
            full_metrics[algo] = result
            
            moves, pushes = ("FAIL", "FAIL") if not result['path'] else (len(result['path']), result['pushes'])
            print(f"{algo:<12} | {result['time']:.4f}   | {result['visited']:<10} | {result['generated']:<10} | {result['max_fringe']:<10} | {result['pruned']:<8} | {pushes:<8} | {moves:<8}")
            
            # Incremental Results Update (Animations are now non-blocking)
            self.menu.show_results(self.solver_results, full_metrics)
            
            if result.get('aborted'):
                print(f"Batch Execution Aborted by User!")
                break
            
        print(f"{'='*95}\n")
        
        self.menu.is_playing = False
        self.menu.play_btn.unselect()
        self.menu.play_btn.update(0)
        self.menu.hint_btn.enable()

    def run(self):
        while self.running:
            time_delta = self.clock.tick(fps) / 1000.0

            if self.game_state == "MAIN_MENU":
                for event in pygame.event.get():
                    if event.type == pygame.QUIT: self.game_state = "QUIT_PROMPT"
                    elif event.type == pygame.KEYDOWN:
                        if (event.key == pygame.K_q) and (event.mod & pygame.KMOD_SHIFT): self.quit_game()
                        elif event.key == pygame.K_ESCAPE: self.game_state = "QUIT_PROMPT"
                        
                    menu_action = self.start_menu.handle_events(event)
                    
                    if menu_action == "START_GAME":
                        self.game_state = "LEVEL_SELECT"
                    elif menu_action == "QUIT":
                        self.game_state = "QUIT_PROMPT"
                
                self.start_menu.draw(time_delta)
                pygame.display.update()
            
            elif self.game_state == "LEVEL_SELECT":
                for event in pygame.event.get():
                    if event.type == pygame.QUIT: self.game_state = "QUIT_PROMPT"
                    elif event.type == pygame.KEYDOWN:
                        if (event.key == pygame.K_q) and (event.mod & pygame.KMOD_SHIFT): self.quit_game()
                        elif event.key == pygame.K_ESCAPE: self.game_state = "MAIN_MENU"
                        
                    action, level = self.level_selector.handle_events(event)
                    if action == "START":
                        self.current_level_num = level
                        self.load_current_level()
                        self.game_state = "GAMEPLAY"
                    elif action == "HOME":
                        self.game_state = "MAIN_MENU"
                
                self.manager.update(time_delta)
                self.level_selector.draw()
                self.manager.draw_ui(self.screen)
                pygame.display.update()

            elif self.game_state == "GAMEPLAY":
                self.event()
                self.update(time_delta)
                self.draw()

            elif self.game_state == "QUIT_PROMPT":
                for event in pygame.event.get():
                    if event.type == pygame.QUIT: self.quit_game()
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self.quit_game()
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        mouse_pos = event.pos
                        if getattr(self, 'yes_rect', pygame.Rect(0,0,0,0)).collidepoint(mouse_pos):
                            self.quit_game()
                        elif getattr(self, 'no_rect', pygame.Rect(0,0,0,0)).collidepoint(mouse_pos):
                            self.game_state = "MAIN_MENU"

                self.draw_quit_prompt()
                pygame.display.update()

    def draw_quit_prompt(self):
        self.start_menu.draw(0)
        overlay = pygame.Surface((window_width, window_height))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        txt = self.font_large.render("Are you sure?", True, (255, 255, 255))
        rect = txt.get_rect(center=(window_width // 2, window_height // 2 - 100))
        self.screen.blit(txt, rect)

        yes_txt = self.font_small.render("Yes", True, (255, 100, 100))
        self.yes_rect = yes_txt.get_rect(center=(window_width // 2 - 150, window_height // 2 + 100))
        
        mouse_pos = pygame.mouse.get_pos()
        if self.yes_rect.collidepoint(mouse_pos):
            pygame.draw.rect(self.screen, (50, 0, 0), self.yes_rect.inflate(40, 20), border_radius=10)
        self.screen.blit(yes_txt, self.yes_rect)

        no_txt = self.font_small.render("No", True, (100, 255, 100))
        self.no_rect = no_txt.get_rect(center=(window_width // 2 + 150, window_height // 2 + 100))
        
        if self.no_rect.collidepoint(mouse_pos):
            pygame.draw.rect(self.screen, (0, 50, 0), self.no_rect.inflate(40, 20), border_radius=10)
        self.screen.blit(no_txt, self.no_rect)

    def quit_game(self):
        pygame.quit()
        sys.exit()

    def event(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game()
            
            if event.type == pygame.KEYDOWN and event.key == pygame.K_q and (event.mod & pygame.KMOD_SHIFT):
                self.quit_game()

            action = self.menu.process_events(event)

            if self.level_complete_waiting:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        if self.current_level_num == 'test':
                            self.current_level_num = 0
                        else:
                            self.current_level_num += 1

                        if os.path.exists(f'levels/{self.current_level_num}.txt'):
                            self.load_current_level()
                        else:
                            print("All levels cleared!")
                            self.quit_game()
                    elif event.key == pygame.K_r:
                        self.load_current_level()
                    elif event.key == pygame.K_ESCAPE:
                        self.game_state = "LEVEL_SELECT"
                continue 
            
            if action == "RUN_SOLVER": self.execute_solvers() 
            elif action == "PLAY_CLICKED": self.execute_solvers()
            elif action == "HINT_CLICKED": self.execute_hint()
            elif action == "UNDO_CLICKED":
                if len(self.history) > 0:
                    last_state = self.history.pop()
                    self.player.x, self.player.y = last_state['player']
                    self.level.boxes = [list(box) for box in last_state['boxes']]
                    self._reset_hint_state()
            elif action == "RESET_CLICKED": 
                self.load_current_level()

            if action and action.startswith("PLAYBACK_"):
                algo = action.split("_")[1]
                if self.solver_results[algo]:
                    if self.saved_solver_state:
                        self.player.x, self.player.y = self.saved_solver_state['player']
                        self.level.boxes = [list(box) for box in self.saved_solver_state['boxes']]
                    
                    self.playback_path = self.solver_results[algo].copy()
                    self.is_playing_back = True
                    self.playback_timer = pygame.time.get_ticks()
                    if self.menu.expanded: self.menu.toggle_expansion() 

            if event.type == pygame.KEYDOWN:
                alt_pressed = bool(pygame.key.get_mods() & (pygame.KMOD_LALT | pygame.KMOD_RALT))

                if self.is_playing_back:
                    self.is_playing_back = False
                    self.menu.hint_btn.enable()
                    print("Playback Interrupted!")

                # Alt + Navigation keybinds for Level Selection
                if alt_pressed:
                    nav_left = (event.key == pygame.K_a) or (event.key == pygame.K_LEFT)
                    nav_right = (event.key == pygame.K_d) or (event.key == pygame.K_RIGHT)
                    if nav_left:
                        self.level_selector.shift_focus(-1)
                        self.game_state = "LEVEL_SELECT"
                        continue
                    elif nav_right:
                        self.level_selector.shift_focus(1)
                        self.game_state = "LEVEL_SELECT"
                        continue

                if self.handle_movement_input(event.key): continue

                if event.key == pygame.K_ESCAPE: 
                    self.game_state = "LEVEL_SELECT"
                    continue
                elif event.key == pygame.K_r: 
                    self.load_current_level()
                
                elif event.key == pygame.K_TAB:
                    self.menu.toggle_expansion()
                
                elif event.key == pygame.K_z:
                    if len(self.history) > 0:
                        last_state = self.history.pop()
                        self.player.x, self.player.y = last_state['player']
                        self.level.boxes = [list(box) for box in last_state['boxes']]
                        self._reset_hint_state()

    def update(self, time_delta):
        self.menu.update(time_delta)
        
        if self.hint_timer > 0:
            self.hint_timer -= time_delta
            if self.hint_timer <= 0: self.hint_box_pos = None 

        if self.is_playing_back:
            current_time = pygame.time.get_ticks()
            if current_time - self.playback_timer > self.playback_speed:
                if self.playback_path:
                    move = self.playback_path.pop(0)
                    move_map = {'U': pygame.K_UP, 'D': pygame.K_DOWN, 'L': pygame.K_LEFT, 'R': pygame.K_RIGHT}
                    self.handle_movement_input(move_map[move])
                    self.playback_timer = current_time
                else:
                    self.is_playing_back = False 
                    self.menu.hint_btn.enable()

        if self.level.is_completed():
            self.is_playing_back = False 
            if not self.level_complete_waiting:
                self.level_complete_waiting = True

    def draw(self):
        self.screen.fill((0, 0, 0))
        self.screen.blit(self.bg_image, self.bg_rect)
        
        self.map_surface.fill((0, 0, 0, 0))
        self.level.draw(self.map_surface)
        
        # Draw Dead State / Targets
        if getattr(self, 'dead_state_active', False):
            for row_idx, row in enumerate(self.level.grid):
                for col_idx, val in enumerate(row):
                    if val in ['3', '4']: 
                        self.map_surface.blit(self.blue_target_img, (col_idx * scaled_tile, row_idx * scaled_tile))
            for box in self.level.boxes:
                self.map_surface.blit(self.blue_box_img, (box[0] * scaled_tile, box[1] * scaled_tile))

        self.player.draw(self.map_surface)
        
        # Draw Hint Box
        if self.hint_timer > 0 and self.hint_box_pos:
            elapsed = 2.0 - self.hint_timer 
            if (0 <= elapsed < 0.5) or (1.0 <= elapsed < 1.5):
                px, py = self.hint_box_pos
                self.map_surface.blit(self.red_box_img, (px * scaled_tile, py * scaled_tile))

        self.screen.blit(self.map_surface, self.map_rect)
        self.menu.draw(self.screen)
        
        if self.level_complete_waiting:
            self.screen.blit(self.win_overlay, (0, 0))
            
            # Render Congrats Text
            congrats_surf = self.font_large.render("!!! Congrats !!!", True, (255, 255, 255))
            self.screen.blit(congrats_surf, congrats_surf.get_rect(center=(window_width // 2, (window_height // 2) - 100)))
            
            # Helper to draw action box
            def draw_shortcut_box(center_x, center_y, key_txt, action_txt):
                box_w, box_h = 240, 140
                box_rect = pygame.Rect(0, 0, box_w, box_h)
                box_rect.center = (center_x, center_y)
                
                # Draw box border only
                pygame.draw.rect(self.screen, (200, 200, 200), box_rect, 3, border_radius=15)
                
                # Render Key (Top)
                key_surf = self.font_small.render(key_txt, True, (255, 255, 255))
                key_rect = key_surf.get_rect(center=(center_x, center_y - 25))
                self.screen.blit(key_surf, key_rect)
                
                # Render Action (Bottom)
                action_surf = self.font_tiny.render(action_txt, True, (180, 180, 180))
                action_rect = action_surf.get_rect(center=(center_x, center_y + 35))
                self.screen.blit(action_surf, action_rect)

            # Draw boxes side by side
            box_spacing = 150
            draw_shortcut_box(window_width // 2 - box_spacing, (window_height // 2) + 60, "R", "restart")
           
            draw_shortcut_box(window_width // 2 + box_spacing, (window_height // 2) + 60, "SPACE", "continue")

        pygame.display.update()

if __name__ == '__main__':
    sokoban = Game()
    sokoban.run()
    import pygame

