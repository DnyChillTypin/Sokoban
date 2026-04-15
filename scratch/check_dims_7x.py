import pygame
import os

os.environ['SDL_VIDEODRIVER'] = 'dummy'
pygame.init()

paths = [
    r"w:\AI\Sokoban\assets\graphics\Buttons\LongRedPlayBtnUp7x.png",
    r"w:\AI\Sokoban\assets\graphics\Buttons\LongWhiteInstructionBtnUp7x.png",
    r"w:\AI\Sokoban\assets\graphics\Buttons\LongWhiteSettingsBtnUp7x.png",
    r"w:\AI\Sokoban\assets\graphics\Buttons\LongWhiteQuitBtnUp7x.png"
]

for p in paths:
    if os.path.exists(p):
        img = pygame.image.load(p)
        print(f"{os.path.basename(p)}: {img.get_size()}")
    else:
        print(f"{os.path.basename(p)}: NOT FOUND")
