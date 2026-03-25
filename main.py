import pygame
import sys
import os
from settings import *
from level import Level
from player import Player
from GameMenu import GameMenu # <-- NEW: Import your separated menu!

class Game:
    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode((window_width, window_height))
        pygame.display.set_caption('Sokoban AI')
        
        self.bg_image = pygame.image.load(bg_image_path).convert_alpha()
        self.bg_rect = self.bg_image.get_rect(midbottom=self.screen.get_rect().midbottom)
        self.clock = pygame.time.Clock()
        self.running = True

        # --- NEW: Initialize the separated Menu Object ---
        self.menu = GameMenu()

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
        self.menu.update_moves(self.moves_count, self.current_level_num)

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

            # --- Pass events to the menu, and see if it returned a command ---
            action = self.menu.process_events(event)
            if action == "RUN_SOLVER":
                # We can access the menu's selected algorithms variable directly!
                print(f"Executing Solver Engine with: {', '.join(self.menu.selected_algos)}")

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
                
                # MOVEMENT (Arrow Keys + WASD)
                elif event.key in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT, 
                                   pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d]:
                    old_x, old_y = self.player.x, self.player.y
                    old_boxes = [list(box) for box in self.level.boxes] 

                    if event.key in [pygame.K_UP, pygame.K_w]: self.player.move(0, -1, self.level)
                    elif event.key in [pygame.K_DOWN, pygame.K_s]: self.player.move(0, 1, self.level)
                    elif event.key in [pygame.K_LEFT, pygame.K_a]: self.player.move(-1, 0, self.level)
                    elif event.key in [pygame.K_RIGHT, pygame.K_d]: self.player.move(1, 0, self.level)

                    # Update history and menu move counter if the player moved
                    if self.player.x != old_x or self.player.y != old_y:
                        self.history.append({'player': (old_x, old_y), 'boxes': old_boxes})
                        self.moves_count += 1
                        self.menu.update_moves(self.moves_count, self.current_level_num)

    def update(self, time_delta):
        self.menu.update(time_delta)
        
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
        # 1. Background
        self.screen.fill((0, 0, 0))
        self.screen.blit(self.bg_image, self.bg_rect)
        
        # 2. Level and Player
        self.map_surface.fill((0, 0, 0, 0))
        self.level.draw(self.map_surface)
        self.player.draw(self.map_surface)
        self.screen.blit(self.map_surface, self.map_rect)

        # 3. Draw the newly separated menu on top of everything!
        self.menu.draw(self.screen)
        
        pygame.display.update()

if __name__ == '__main__':
    sokoban = Game()
    sokoban.run()