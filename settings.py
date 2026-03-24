tile_size = 16
scale = 5
scaled_tile = tile_size * scale

window_width = 1600
window_height = 900
fps = 60

menu_width = int(window_width * 0.2)
game_width = window_width - menu_width

menu_bg_color = ("#21c9eb")
bg_image_path = 'assets/graphics/WallpaperScifi.png'

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
    'player': 'assets/graphics/ScotterBlue.png',
    'bg_image_path': 'assets/graphics/WallpaperScifi.png'
}