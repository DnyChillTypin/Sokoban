import pygame
import sys
import os
import time
from settings import *
from level import Level
from player import Player
from gameMenu import GameMenu
from solver import SokobanSolver

class Game:
    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode((window_width, window_height))
        pygame.display.set_caption('Sokoban AI')
        
        self.bg_image = pygame.image.load(bg_image_path).convert_alpha()
        self.bg_rect = self.bg_image.get_rect(midbottom=self.screen.get_rect().midbottom)
        self.clock = pygame.time.Clock()
        self.running = True

        self.menu = GameMenu()
        
        self.solver_results = {}
        self.is_playing_back = False
        self.playback_path = []
        self.playback_timer = 0
        self.playback_speed = 100 
        self.saved_solver_state = None 

        self.level_complete_waiting = False
        self.font_large = pygame.font.Font('assets/PIXY.ttf', 100) 
        self.font_small = pygame.font.Font('assets/PIXY.ttf', 60)  
        self.win_overlay = pygame.Surface((window_width, window_height), pygame.SRCALPHA)
        self.win_overlay.fill((0, 0, 0, 128)) 

        self.current_level_num = 0
        self.moves_count = 0
        self.load_current_level()

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
        
        self.level_complete_waiting = False
        self.menu.reset_ai_menu() 
        self.menu.update_moves(self.moves_count, self.current_level_num)

    def handle_movement_input(self, key):
        directions = {
            pygame.K_UP: (0, -1), pygame.K_w: (0, -1),
            pygame.K_DOWN: (0, 1), pygame.K_s: (0, 1),
            pygame.K_LEFT: (-1, 0), pygame.K_a: (-1, 0),
            pygame.K_RIGHT: (1, 0), pygame.K_d: (1, 0)
        }

        if key in directions:
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

    def execute_solvers(self):
        if len(self.menu.selected_algos) == 0:
            print("\nPlease select at least one algorithm first!")
            return

        print(f"\n{'='*95}")
        print(f"Executing Solver Engine...")
        print(f"{'='*95}")
        
        self.menu.run_solver_btn.set_text("Running...")
        self.menu.update(0.016) 
        self.draw()             
        
        self.saved_solver_state = {
            'player': (self.player.x, self.player.y),
            'boxes': [list(box) for box in self.level.boxes]
        }
        
        solver = SokobanSolver(self.level)
        current_state = solver.get_initial_state(self.player, self.level)
        self.solver_results.clear()
        
        # --- NEW: Formatted Header for all 8 metrics ---
        print(f"{'Algorithm':<12} | {'Time (s)':<10} | {'Visited':<10} | {'Generated':<10} | {'Max Mem':<10} | {'Pruned':<8} | {'Pushes':<8} | {'Moves':<8}")
        print("-" * 95)
        
        for algo in self.menu.selected_algos:
            if algo == 'BFS': result = solver.solve_bfs(current_state)
            elif algo == 'DFS': result = solver.solve_dfs(current_state)
            elif algo == 'A*': result = solver.solve_astar(current_state)
            elif algo == 'Best-FS': result = solver.solve_best_first(current_state)
                
            self.solver_results[algo] = result['path']
            
            # --- NEW: Extracting the new data ---
            time_val = f"{result['time']:.4f}"
            visited = result['visited']
            generated = result['generated']
            max_mem = result['max_fringe']
            pruned = result['pruned']
            
            if result['path'] is not None:
                moves = len(result['path'])
                pushes = result['pushes']
            else:
                moves = "FAIL"
                pushes = "FAIL"
                
            print(f"{algo:<12} | {time_val:<10} | {visited:<10} | {generated:<10} | {max_mem:<10} | {pruned:<8} | {pushes:<8} | {moves:<8}")
            
        print(f"{'='*95}\n")
        
        self.menu.run_solver_btn.set_text("Run Solver")
        self.menu.show_results(self.solver_results)

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

            action = self.menu.process_events(event)

            if self.level_complete_waiting:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    self.current_level_num += 1
                    next_level_path = f'levels/{self.current_level_num}.txt'
                    if os.path.exists(next_level_path):
                        self.load_current_level()
                    else:
                        print("All levels cleared!")
                        self.quit_game()
                continue 
            
            if action == "RUN_SOLVER":
                self.execute_solvers() 

            if action and action.startswith("PLAYBACK_"):
                algo = action.split("_")[1]
                
                if self.solver_results[algo] is None:
                    continue
                
                if self.saved_solver_state:
                    self.player.x, self.player.y = self.saved_solver_state['player']
                    self.level.boxes = [list(box) for box in self.saved_solver_state['boxes']]
                
                self.playback_path = self.solver_results[algo].copy()
                self.is_playing_back = True
                self.playback_timer = pygame.time.get_ticks()
                if self.menu.expanded: self.menu.toggle_expansion() 

            if event.type == pygame.KEYDOWN:
                if self.is_playing_back:
                    self.is_playing_back = False
                    print("Playback Interrupted!")

                if self.handle_movement_input(event.key):
                    continue

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

    def update(self, time_delta):
        self.menu.update(time_delta)
        
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

        if self.level.is_completed():
            self.is_playing_back = False 
            if not self.level_complete_waiting:
                self.level_complete_waiting = True
                print(f"Level {self.current_level_num} cleared! Waiting for SPACE...")

    def draw(self):
        self.screen.fill((0, 0, 0))
        self.screen.blit(self.bg_image, self.bg_rect)
        
        self.map_surface.fill((0, 0, 0, 0))
        self.level.draw(self.map_surface)
        self.player.draw(self.map_surface)
        self.screen.blit(self.map_surface, self.map_rect)

        self.menu.draw(self.screen)
        
        if self.level_complete_waiting:
            self.screen.blit(self.win_overlay, (0, 0))
            
            text_congrats = self.font_large.render("Congrats !!!", True, (255, 255, 255))
            text_space = self.font_small.render("Press SPACE to continue", True, (200, 200, 200))
            
            rect_congrats = text_congrats.get_rect(center=(window_width // 2, (window_height // 2) - 40))
            rect_space = text_space.get_rect(center=(window_width // 2, (window_height // 2) + 40))
            
            self.screen.blit(text_congrats, rect_congrats)
            self.screen.blit(text_space, rect_space)

        pygame.display.update()

if __name__ == '__main__':
    sokoban = Game()
    sokoban.run()