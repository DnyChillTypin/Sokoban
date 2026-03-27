tile_size = 16
scale = 5
scaled_tile = tile_size * scale

window_width = 1600
window_height = 900
fps = 60

menu_width = int(window_width * 0.2)
game_width = window_width - menu_width

bg_image_path = 'assets/graphics/WallpaperScifi.png'

tile_mapping = {
    '0': 'ground',
    '1': 'wall',
    '2': 'box',
    '3': 'target',
    '4': 'box_on_target',
    '5': 'shield',
    '6': 'bomb'
}

textures = {
    'ground_dark': 'assets/graphics/wallsFloors/FloorDark.png',
    'ground_light': 'assets/graphics/wallsFloors/FloorLight.png',
    'box': 'assets/graphics/interactables/BoxYallow.png',
    'target': 'assets/graphics/interactables/ButtonUpYallow.png',
    'box_on_target': 'assets/graphics/interactables/BoxGreen.png', 
    'player': 'assets/graphics/ScotterBlue.png',
    'bg_image_path': 'assets/graphics/WallpaperScifi.png',
    'shield': 'assets/graphics/items/Shield.png',
    'bomb': 'assets/graphics/items/Bomb.png',
    'bomb_tini': 'assets/graphics/items/BombTini.png',
    'Bomb_white': 'assets/graphics/items/BombWhite.png',
    'Bomb_explode_1': 'assets/graphics/items/Explode1.png',
    'Bomb_explode_2': 'assets/graphics/items/Explode2.png',
    'Bomb_explode_3': 'assets/graphics/items/Explode3.png'
}

'''
nodes generated
nodes visited 
'''