import os 
import pygame
import random
from settings import *

class Level:
    def __init__(self, level_number):
        self.level_number = level_number
        self.grid = []
        self.boxes = []
        self.columns = 0
        self.rows = 0
        self.targets = set() # Store target grid coords (x, y)

        self. player_start_x = 0
        self.player_start_y = 0
        
        self.images = {}

        self.load_level()
        self.load_graphics()

        # --- NEW: Random Flower Generation ---
        self.flowers = {} 
        
        # Load and scale the images to match your tile size
        flower_imgs = [
            pygame.transform.scale(pygame.image.load('assets/graphics/props/FlowerWhite.png').convert_alpha(), (scaled_tile, scaled_tile)),
            pygame.transform.scale(pygame.image.load('assets/graphics/props/FlowerBlue.png').convert_alpha(), (scaled_tile, scaled_tile))
        ]
        
        # 1. Find all the empty floor tiles ('0')
        floor_tiles = []
        for row in range(self.rows):
            for col in range(self.columns):
                if self.grid[row][col] == '0':
                    floor_tiles.append((col, row))
        
        # 2. Calculate how many flowers we need (2 to 3 per 10 tiles)
        num_flowers = int((len(floor_tiles) / 20) * random.uniform(2, 3))
        
        # 3. Pick random spots and assign a random flower color!
        if num_flowers > 0 and floor_tiles:
            chosen_tiles = random.sample(floor_tiles, min(num_flowers, len(floor_tiles)))
            for tile in chosen_tiles:
                self.flowers[tile] = random.choice(flower_imgs)

    def load_level(self):
        file_path = f'levels/{self.level_number}.txt'

        if not os.path.exists(file_path):
            print(f'Error: Level file {file_path} not found')
            return
        
        with open(file_path, 'r') as file:
            lines = file.readlines()

        lines = [line.strip() for line in lines if line.strip()]
        
        # --- NEW: Defensive check for empty or corrupted files ---
        if not lines:
            print(f"Warning: Level file {file_path} is empty. Using default 1x1 grid.")
            self.columns, self.rows = 1, 1
            self.grid = [['1']]
            return

        #line 0
        dimensions = lines[0].split()
        if len(dimensions) < 2:
            print(f"Warning: Malformed dimensions in {file_path}")
            self.columns, self.rows = 1, 1
            self.grid = [['1']]
            return

        self.columns = int(dimensions[0])
        self.rows = int(dimensions[1])

        #line 1
        if len(lines) < 2:
            print(f"Warning: No player position in {file_path}")
            self.player_start_x, self.player_start_y = 0, 0
        else:
            player_pos = lines[1].split()
            if len(player_pos) >= 2:
                self.player_start_x = int(player_pos[0])
                self.player_start_y = int(player_pos[1])
            else:
                self.player_start_x, self.player_start_y = 0, 0

        for row_index, row_string in enumerate(lines[2:]):
            row_data = row_string.split()
            clean_row = []

            for col_index, tile_val in enumerate(row_data):
                if tile_val == '2':
                    self.boxes.append([col_index, row_index])
                    clean_row.append('0')

                elif tile_val == '4':
                    self.boxes.append([col_index, row_index])
                    clean_row.append('3')

                elif tile_val == '3':
                    self.targets.add((col_index, row_index))
                    clean_row.append(tile_val)

                else:
                    clean_row.append(tile_val)
            self.grid.append(clean_row)

    def load_graphics(self):
        for name, path in textures.items():
            img = pygame.image.load(path).convert_alpha()
            self.images[name] = pygame.transform.scale(img, (scaled_tile, scaled_tile))
        for up in ['0', '1']:
            for down in ['0', '1']:
                for left in ['0', '1']:
                    for right in ['0', '1']:
                        wall_name = f'Wall_{up}{down}{left}{right}'
                        file_name = wall_name

                        path = f'assets/graphics/wallsFloors/{file_name}.png'

                        if os.path.exists(path):
                            img = pygame.image.load(path).convert_alpha()
                            self.images[wall_name] = pygame.transform.scale(img, (scaled_tile, scaled_tile))

    def is_wall(self, row, col):
        if 0 <= row < self.rows and 0 <= col < self.columns:
            return self.grid[row][col] == '1'
        return False

    def get_wall_texture_name(self, row, col):
        up = '1' if self.is_wall(row - 1, col) else '0'
        down = '1' if self.is_wall(row + 1, col) else '0'
        left = '1' if self.is_wall(row, col - 1) else '0'
        right = '1' if self.is_wall(row, col + 1) else '0'
        
        return f"Wall_{up}{down}{left}{right}"

    def draw(self, surface):
        for row_index, row in enumerate(self.grid):
            for col_index, tile_val in enumerate(row):
                
                x = col_index * scaled_tile
                y = row_index * scaled_tile
                
                if (row_index + col_index) % 2 == 0:
                    surface.blit(self.images['ground_dark'], (x, y))
                else:
                    surface.blit(self.images['ground_light'], (x, y))

                if (col_index, row_index) in self.flowers:
                    surface.blit(self.flowers[(col_index, row_index)], (x, y))

                if tile_val == '1':
                    specific_wall = self.get_wall_texture_name(row_index, col_index)
                    surface.blit(self.images[specific_wall], (x, y))
                    
                elif tile_val == '3':
                    surface.blit(self.images['target'], (x, y))
                
        for box in self.boxes:
            box_col = box[0]
            box_row = box[1]
            x = box_col * scaled_tile
            y = box_row * scaled_tile

            if self.grid[box_row][box_col] == '3':
                surface.blit(self.images['box_on_target'], (x, y))
            else:
                surface.blit(self.images['box'], (x, y))

    def is_completed(self):
        if len(self.boxes) == 0:
            return False
        
        for box in self.boxes:
            box_col = box[0]
            box_row = box[1]

            if self.grid[box_row][box_col] != '3':
                return False
        
        return True
    