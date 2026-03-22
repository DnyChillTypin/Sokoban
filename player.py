import pygame
from settings import *

class Player:
    def __init__(self, x, y, image):
        self.x = x
        self.y = y
        self.image = image

    def move(self, dx, dy, level):
        target_x = self.x + dx
        target_y = self.y + dy

        if level.is_wall(target_y, target_x):
            return
        
        box_to_push = None
        for box in level.boxes:
            if box[0] == target_x and box[1] == target_y:
                box_to_push = box
                break

        if box_to_push:
            box_target_x = box_to_push[0] + dx
            box_target_y = box_to_push[1] + dy

            if level.is_wall(box_target_y, box_target_x):
                return

            for other_box in level.boxes:
                if other_box[0] == box_target_x and other_box[1] == box_target_y:
                    return
            
            box_to_push[0] = box_target_x
            box_to_push[1] = box_target_y

        self.x = target_x
        self.y = target_y

    def draw(self,surface):
        pixel_x = self.x * scaled_tile
        pixel_y = self.y * scaled_tile
        surface.blit(self.image, (pixel_x, pixel_y))