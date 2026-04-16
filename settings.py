tile_size = 16
scale = 5
scaled_tile = tile_size * scale

window_width = 1600
window_height = 900
fps = 120

menu_width = int(window_width * 0.2)
game_width = window_width - menu_width

ALGORITHMS = ['BFS', 'DFS', 'BestFS', 'Dijkstra', 'A*']
UI_THEME = 'theme.json'

font_path = 'assets/BoldPixels.ttf'
BORDER_COLOR = (71, 45, 60) # #472d3c
BORDER_WIDTH = 5

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
    # Environment
    'bg_image_path': 'assets/graphics/WallpaperScifi.png',
    'ground_dark': 'assets/graphics/wallsFloors/FloorDark.png',
    'ground_light': 'assets/graphics/wallsFloors/FloorLight.png',
    
    # Interactables
    'player': 'assets/graphics/ScotterWhite.png',
    'box': 'assets/graphics/interactables/BoxYallow.png',
    'box_on_target': 'assets/graphics/interactables/BoxGreen.png', 
    'target': 'assets/graphics/interactables/ButtonUpYallow.png',
    
    # Hint & Dead State
    'red_box': 'assets/graphics/interactables/BoxRed.png',
    'red_target': 'assets/graphics/interactables/ButtonUpRed.png',
    'blue_box': 'assets/graphics/interactables/BoxBlue.png',
    'blue_target': 'assets/graphics/interactables/ButtonUpBlue.png',
    
    # Items
    'shield': 'assets/graphics/items/Shield.png',
    'bomb': 'assets/graphics/items/Bomb.png',
    'bomb_tini': 'assets/graphics/items/BombTini.png',
    'Bomb_white': 'assets/graphics/items/BombWhite.png',
    'Bomb_explode_1': 'assets/graphics/items/Explode1.png',
    'Bomb_explode_2': 'assets/graphics/items/Explode2.png',
    'Bomb_explode_3': 'assets/graphics/items/Explode3.png',
    
    'FlowerBlue':'assets/graphics/props/FlowerBlue.png',
    'FlowerWhite':'assets/graphics/props/FlowerWhite.png',
    
    # UI & Menus
    'menu_dark': 'assets/graphics/Buttons/MenuFloorDark5x.png',
    'menu_light': 'assets/graphics/Buttons/MenuFloorLight5x.png',
    'coffee_icon': 'assets/graphics/Buttons/CoffeeIconRed.png',
}