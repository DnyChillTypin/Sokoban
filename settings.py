tile_size = 16
scale = 5
scaled_tile = tile_size * scale

default_window_width = 1024
default_window_height = 768
fps = 60

bg_color = (255, 255, 255)

tile_mapping = {
    '0': 'ground',
    '1': 'wall',
    '2': 'box',
    '3': 'target',
    '4': 'box_on_target'
}

textures = {
    'ground_dark': 'assets/graphics/wallsFloors/FloorDark.png',
    'ground_light': 'assets/graphics/wallsFloors/FloorLight.png',
    'box': 'assets/graphics/interactables/BoxYallow.png',
    'target': 'assets/graphics/interactables/ButtonUpYallow.png',
    'box_on_target': 'assets/graphics/interactables/BoxGreen.png', 
    'player': 'assets/graphics/ScotterBlue.png'
}