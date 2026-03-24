import pygame
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

        self.current_level_num = 0
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

        self.history = []

    def quit_game(self):
        pygame.quit()
        sys.exit()

    def run(self):
        while self.running:
            self.event()
            self.update()
            self.draw()
            self.clock.tick(fps)

    def event(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.quit_game()

                elif event.key == pygame.K_r:
                    print(f'restarting Level {self.current_level_num}...')
                    self.load_current_level()
                
                elif event.key == pygame.K_n:
                    next_level_path = f'levels/{self.current_level_num + 1}.txt'
                    if os.path.exists(next_level_path):
                        self.current_level_num += 1
                        print(f'Skipping to Level {self.current_level_num}')
                        self.load_current_level()
                    else:
                        print('Next: last level reached')

                elif event.key == pygame.K_p:
                    if self.current_level_num > 0:
                        self.current_level_num -= 1
                        print(f'Going back to Level {self.current_level_num}')
                        self.load_current_level()
                    else:
                        print('Previous: First level reached')

                elif event.key == pygame.K_z:
                    if len(self.history) > 0:
                        last_state = self.history.pop()

                        self.player.x, self.player.y = last_state['player']
                        self.level.boxes = [list(box) for box in last_state['boxes']]
                    else:
                        print('Undo: First state reached')
                elif event.key in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]:
                    old_x, old_y = self.player.x, self.player.y
                    old_boxes = [list(box) for box in self.level.boxes]
                    
                    if event.key == pygame.K_UP:
                        self.player.move(0, -1, self.level)
                    elif event.key == pygame.K_DOWN:
                        self.player.move(0, 1, self.level)
                    elif event.key == pygame.K_LEFT:
                        self.player.move(-1, 0, self.level)
                    elif event.key == pygame.K_RIGHT:
                        self.player.move(1, 0, self.level)

                    if self.player.x != old_x or self.player.y != old_y:
                        self.history.append({
                            'player': (old_x, old_y),
                            'boxes': old_boxes
                        })
    def update(self):
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
        
        menu_surface = pygame.Surface((menu_width, window_height))
        menu_surface.fill(menu_bg_color)
        self.screen.blit(menu_surface, (0, 0))

        self.map_surface.fill((0, 0, 0, 0))

        self.level.draw(self.map_surface)
        self.player.draw(self.map_surface)

        game_rect = pygame.Rect(menu_width, 0, game_width, window_height)
        map_rect = self.map_surface.get_rect(center=game_rect.center)
        self.screen.blit(self.map_surface, map_rect)
        
        pygame.display.update()

if __name__ == '__main__':
    sokoban = Game()
    sokoban.run()