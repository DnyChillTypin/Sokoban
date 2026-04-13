import pygame
import math
import time

class Button:
    def __init__(self, rect, text, font, color=(255, 255, 255)):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.color = color
        self.is_loading = False
        self.show_text = True
        
    def draw(self, surface):
        if self.is_loading:
            # Draw 16x16 pixel-grid style spinner (Classic rotating cross)
            ticks = pygame.time.get_ticks() // 150
            pixel_size = 5 # Game's 5x scale
            center = self.rect.center
            
            # Pattern: 4 rotating arms of a cross
            # Each arm is 2 blocks long from center
            frame = ticks % 4
            rotations = [
                [(0,-1), (0,-2)], # Up
                [(1,0), (2,0)],   # Right
                [(0,1), (0,2)],   # Down
                [(-1,0), (-2,0)]  # Left
            ]
            
            # Draw center block (always there)
            pygame.draw.rect(surface, self.color, (center[0]-pixel_size//2, center[1]-pixel_size//2, pixel_size, pixel_size))
            
            # Draw rotating arms
            for i in range(4):
                is_active = (i == frame)
                color = self.color if is_active else (80, 80, 80)
                for ox, oy in rotations[i]:
                    px = center[0] + (ox * pixel_size) - pixel_size//2
                    py = center[1] + (oy * pixel_size) - pixel_size//2
                    pygame.draw.rect(surface, color, (px, py, pixel_size, pixel_size))

        elif self.show_text:
            # Render normal text centered
            text_surf = self.font.render(self.text, True, self.color)
            text_rect = text_surf.get_rect(center=self.rect.center)
            surface.blit(text_surf, text_rect)
