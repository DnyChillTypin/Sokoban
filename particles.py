import pygame
import random
import math

PASTELS = [
    (255, 182, 193), # Pink
    (173, 216, 230), # Blue
    (152, 251, 152), # Green
    (253, 253, 150), # Yellow
    (221, 160, 221), # Lavender
    (255, 218, 185)  # Peach
]

class ConfettiParticle:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        
        # Outward burst velocity
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(200, 400)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - random.uniform(100, 200) # Initial upward boost
        
        self.color = random.choice(PASTELS)
        self.size = random.randint(4, 6)
        self.original_size = self.size
        
        self.lifetime = random.uniform(1.0, 1.5)
        self.max_lifetime = self.lifetime
        
        self.gravity = 600 # Gravity strength
        self.friction = 0.95 # Air friction

    def update(self, time_delta):
        # Apply air friction to horizontal velocity
        self.vx *= self.friction
        
        # Apply gravity to vertical velocity
        self.vy += self.gravity * time_delta
        
        # Update position
        self.x += self.vx * time_delta
        self.y += self.vy * time_delta
        
        # Decay lifetime
        self.lifetime -= time_delta
        
        # Shrink based on lifetime
        life_ratio = self.lifetime / self.max_lifetime
        self.size = max(1, int(self.original_size * life_ratio))

    def draw(self, surface):
        if self.lifetime > 0:
            rect = pygame.Rect(
                int(self.x - self.size / 2),
                int(self.y - self.size / 2),
                self.size,
                self.size
            )
            pygame.draw.rect(surface, self.color, rect)

class ParticleManager:
    def __init__(self):
        self.particles = []

    def burst(self, x, y, count=30):
        for _ in range(count):
            self.particles.append(ConfettiParticle(x, y))

    def update(self, time_delta):
        # Update and filter out dead particles (Memory Safe Culling)
        self.particles = [p for p in self.particles if p.lifetime > 0]
        for p in self.particles:
            p.update(time_delta)

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)
