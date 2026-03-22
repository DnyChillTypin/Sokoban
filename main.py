import pygame
import sys
import os
from settings import *
from level import Level
from player import Player

class Game:
    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode((default_window_width, default_window_height))
        pygame.display.set_caption('Sokoban AI')
        
        self.clock = pygame.time.Clock()
        self.running = True

        self.current_level_num = 0
        self.load_current_level()

    def load_current_level(self):
        self.level = Level(self.current_level_num)
        
        new_width = self.level.columns * scaled_tile
        new_height = self.level.rows * scaled_tile
        self.screen = pygame.display.set_mode((new_width, new_height))
        
        self.player = Player(
            self.level.player_start_x,
            self.level.player_start_y,
            self.level.images['player']
        )


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
        self.screen.fill(bg_color)
        self.level.draw(self.screen)
        self.player.draw(self.screen)
        pygame.display.update()

if __name__ == '__main__':
    sokoban = Game()
    sokoban.run()
