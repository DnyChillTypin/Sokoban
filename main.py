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

        self.map_surface = pygame.Surface((self.map_width, self.map_height))

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

                elif event.key == pygame.K_UP:
                    self.player.move(0, -1, self.level)
                elif event.key == pygame.K_DOWN:
                    self.player.move(0, 1, self.level)
                elif event.key == pygame.K_LEFT:
                    self.player.move(-1, 0, self.level)
                elif event.key == pygame.K_RIGHT:
                    self.player.move(1, 0, self.level)

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
        menu_surface = pygame.Surface((menu_width, window_height))
        menu_surface.fill(menu_bg_color)

        game_surface = pygame.Surface((game_width, window_height))
        game_surface.fill(bg_color)

        self.map_surface.fill(bg_color)
        self.level.draw(self.map_surface)
        self.level.draw(self.screen)
        self.player.draw(self.map_surface)

        map_rect = self.map_surface.get_rect(center=game_surface.get_rect().center)
        game_surface.blit(self.map_surface, map_rect)

        self.screen.blit(menu_surface, (0, 0))
        self.screen.blit(game_surface, (menu_width, 0))
        
        pygame.display.update()

if __name__ == '__main__':
    sokoban = Game()
    sokoban.run()
