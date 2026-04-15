import pygame
import os

os.environ['SDL_VIDEODRIVER'] = 'dummy'
pygame.init()

paths = [
    r"w:\AI\Sokoban\assets\graphics\Buttons\LongRedPlayBtnUp8x.png",
    r"w:\AI\Sokoban\assets\graphics\Buttons\LongWhiteInstructionBtnUp8x.png",
    r"w:\AI\Sokoban\assets\graphics\Buttons\LongWhiteSettingsBtnUp8x.png",
    r"w:\AI\Sokoban\assets\graphics\Buttons\LongWhiteQuitBtnUp8x.png",
    r"w:\AI\Sokoban\assets\graphics\Buttons\InGameMenu\HomeSettingsTray5x.png",
    r"w:\AI\Sokoban\assets\graphics\Buttons\InGameMenu\SettingsBtnUp5x.png",
    r"w:\AI\Sokoban\assets\graphics\Buttons\InGameMenu\HomeBtnUp5x.png"
]

for p in paths:
    if os.path.exists(p):
        img = pygame.image.load(p)
        print(f"{os.path.basename(p)}: {img.get_size()}")
    else:
        print(f"{os.path.basename(p)}: NOT FOUND")
