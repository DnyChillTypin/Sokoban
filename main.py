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
from particles import ParticleManager
from tween import TweenManager, ease_out_bounce, ease_out_quad

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((window_width, window_height))
        pygame.display.set_caption('Sokoban AI')
        
        self.bg_image = pygame.image.load(textures['bg_image_path']).convert_alpha()
        self.bg_rect = self.bg_image.get_rect(midbottom=self.screen.get_rect().midbottom)
        self.clock = pygame.time.Clock()
        self.running = True

        self.tween_manager = TweenManager()
        self.menu_button_rect = pygame.Rect(300, -100, 200, 50)

        self.start_menu = SokobanMenu(self.screen)

        self.manager = pygame_gui.UIManager((window_width, window_height))
        self.level_selector = LevelSelection(self.screen, self.manager)
        
        self.game_state = "MAIN_MENU"

        self.menu = GameMenu()
        
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
        
        self.particle_manager = ParticleManager()
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
    def trigger_menu_animation(self):
        # 2. Add a tween! 
        # Move menu_button_rect.y to 250, over 0.8 seconds, with a bounce effect.
        self.tween_manager.add_tween(
            target=self.menu_button_rect, 
            attribute='y', 
            end_val=250, 
            duration=0.8, 
            easing_func=ease_out_bounce
        )

    def run(self):
        running = True
        
        # Trigger it right as the game starts for testing
        self.trigger_menu_animation()

        while running:
            # Get delta time in seconds
            dt = self.clock.tick(60) / 1000.0 
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # 3. Update the manager every frame BEFORE drawing
            self.tween_manager.update(dt)

            # --- DRAWING ---
            self.screen.fill((30, 30, 30))
            
            # Draw the button. You will see it smoothly bounce into place!
            pygame.draw.rect(self.screen, (200, 50, 50), self.menu_button_rect)
            
            pygame.display.flip()
            
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
            
            pushed_box_pos = self.player.move(dx, dy, self.level)
            
            if self.player.x != old_x or self.player.y != old_y:
                self.history.append({'player': (old_x, old_y), 'boxes': old_boxes})
                self.moves_count += 1
                self.menu.update_moves(self.moves_count, self.current_level_num)

                # Confetti Burst Trick: If a box was pushed onto a target, trigger burst
                if pushed_box_pos and pushed_box_pos in self.level.targets:
                    bx, by = pushed_box_pos
                    pixel_x = bx * scaled_tile + (scaled_tile // 2) + self.map_rect.x
                    pixel_y = by * scaled_tile + (scaled_tile // 2) + self.map_rect.y
                    self.particle_manager.burst(pixel_x, pixel_y, count=30)
                    
            return True 
        return False

    def execute_hint(self):
        solver = SokobanSolver(self.level)
        current_state = solver.get_initial_state(self.player, self.level)
        
        # Hyper-fast Weighted A* exclusively for hints
        result = solver.solve_fast_hint(current_state, weight=5.0, timeout=2.0)

        if result['path']:
            self.dead_state_active = False
            px, py = self.player.x, self.player.y
            boxes = [list(b) for b in self.level.boxes]
            move_map = {'U': (0, -1), 'D': (0, 1), 'L': (-1, 0), 'R': (1, 0)}

            # Find the first box that is pushed in the suggested path
            for move in result['path']:
                dx, dy = move_map[move]
                px += dx; py += dy
                
                if [px, py] in boxes:
                    self.hint_box_pos = (px, py)
                    self.hint_timer = 2.0 
                    break
        else:
            print("Hint Unavailable!")
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
            self.menu.radar_chart.trigger_replay(cached_algos)
            self.menu.is_playing = False
            self.menu.play_btn.unselect()
            self.menu.play_btn.update(0)
            self.menu.hint_btn.enable() 
            return

        print(f"\n{'='*95}\nInitializing Multitasking Solver Engine...\n{'-'*95}")
        print(f"{'Algorithm':<12} | Status")
        print(f"{'-'*95}")
        
        self.saved_solver_state = {
            'player': (self.player.x, self.player.y),
            'boxes': [list(box) for box in self.level.boxes]
        }
        
        solver = SokobanSolver(self.level)
        current_state = solver.get_initial_state(self.player, self.level)
        
        num_algos = len(self.menu.selected_algos)
        for i, algo in enumerate(self.menu.selected_algos):
            # Calculate offset from the bottom of the "Initializing..." block
            # Each algo prints one line, then a footer of 2 lines is added.
            # Offset = (Total Algos - current index) + 1
            offset = (num_algos - i) + 1
            
            # Initialize Generator with line offset
            gen = None
            if algo == 'BFS': gen = solver.solve_bfs(current_state, line_offset=offset)
            elif algo == 'DFS': gen = solver.solve_dfs(current_state, line_offset=offset)
            elif algo == 'A*': gen = solver.solve_astar(current_state, line_offset=offset)
            elif algo == 'BestFS': gen = solver.solve_best_first(current_state, line_offset=offset)
            elif algo == 'Dijkstra': gen = solver.solve_dijkstra(current_state, line_offset=offset)
            
            if gen:
                self.menu.active_solvers[algo] = gen
                self.menu.algo_custom_btns[algo].is_loading = True
                self.menu.algo_btns[algo].disable() # Disable interaction while running
                print(f"{algo:<12} | RUNNING (Cooperative Mode)")
        
        print(f"{'='*95}\n")

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
                result = self.menu.execution_cache.get(algo)
                if result and result.get('path'):
                    if self.saved_solver_state:
                        self.player.x, self.player.y = self.saved_solver_state['player']
                        self.level.boxes = [list(box) for box in self.saved_solver_state['boxes']]
                    
                    self.playback_path = result['path'].copy()
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
                    if self.menu.active_solvers:
                        self.menu.active_solvers.clear()
                        for btn in self.menu.algo_custom_btns.values(): btn.is_loading = False
                        for btn in self.menu.algo_btns.values(): btn.enable()
                        print("Execution Aborted globally via ESC!")
                    else:
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
        self.particle_manager.update(time_delta)
        
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
        self.particle_manager.draw(self.screen)
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

