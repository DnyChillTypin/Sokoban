import pygame
import pygame_gui
import math
import random
from settings import *
from settings import window_width, window_height
import os

class SokobanMenu:
    def __init__(self, screen):
        self.window = screen
        self.manager = pygame_gui.UIManager((window_width, window_height), UI_THEME)
        self.state = "MAIN"
        
        self.TITLE_MAIN = (249, 194, 43) # #f9c22b
        self.TITLE_YELLOW = (255, 255, 0)
        self.DARK_SHADOW = (0, 50, 0)
        
        # Dimming Overlay matching other menus
        self.dark_overlay = pygame.Surface((window_width, window_height))
        self.dark_overlay.fill((0, 0, 0))
        self.dark_overlay.set_alpha(150)
        
        pygame.mixer.init()
        try:
            self.music = pygame.mixer.Sound('assets/Music.mp3')
            self.sfx = pygame.mixer.Sound('assets/SoundEffect.wav')
            self.music_channel = self.music.play(-1)
            self.is_music_on = True
            self.is_sfx_on = True
        except:
            self.is_music_on = self.is_sfx_on = False

        self.bg_pattern = self.create_bg_pattern()
        
        # --- NEW: Pool-based Animation State ---
        self.anim_time = 0
        self.floating_objs = []
        self.max_objs = 3
        self.margin = 150 # Safety margin to keep resets invisible 
        self.fly_speed = 120
        # --------------------------------------

        self.load_assets()
        
        # Initial spawn of our pool
        for i in range(self.max_objs):
            self.spawn_object(i, initial=True)
            
        self.setup_ui()

    def create_bg_pattern(self):
        curr_w = window_width
        curr_h = window_height
        dark_tile = pygame.image.load(textures['menu_dark']).convert_alpha()
        light_tile = pygame.image.load(textures['menu_light']).convert_alpha()
        tw, th = dark_tile.get_size()
        pattern = pygame.Surface((curr_w, curr_h))
        for y in range(0, curr_h, th):
            for x in range(0, curr_w, tw):
                tile = light_tile if ((x // tw) + (y // th)) % 2 == 0 else dark_tile
                pattern.blit(tile, (x, y))
        return pattern

    def load_assets(self):
        self.anim_assets = {}
        # Size mapping for consistency
        sizes = {'player': (144, 144), 'box': (144, 144), 'box_on_target': (144, 144), 
                 'FlowerBlue': (250, 250), 'FlowerWhite': (250, 250)}
        
        asset_map = {
            'player': textures['player'],
            'box_yellow': textures['box'],
            'box_green': textures['box_on_target'],
            'flower_blue': textures['FlowerBlue'],
            'flower_white': textures['FlowerWhite']
        }

        for key, path in asset_map.items():
            try:
                raw = pygame.image.load(path).convert_alpha()
                # Determine which size category to use
                size_key = 'player' if key == 'player' else \
                           'FlowerBlue' if 'flower' in key else 'box'
                scaled = pygame.transform.scale(raw, sizes[size_key])
                self.anim_assets[key] = scaled
            except:
                print(f"Failed to load menu asset: {key}")
                self.anim_assets[key] = None

    def setup_ui(self):
        """Tính toán vị trí dựa trên phần trăm hoặc khoảng cách từ cạnh dưới"""
        self.manager.clear_and_reset()
        curr_w = window_width
        curr_h = window_height
        self.manager.set_window_resolution((curr_w, curr_h))
        
        btn_w, btn_h = 336, 112
        cx = curr_w // 2 - btn_w // 2
        
        if self.state == "MAIN":
            start_y = curr_h // 2 - 160
            self.play_btn = self._create_btn(cx, start_y, btn_w, btn_h, "", "#menu_play")
            self.instr_btn = self._create_btn(cx, start_y + 135, btn_w, btn_h, "", "#menu_instr")
            self.setting_btn = self._create_btn(cx, start_y + 270, btn_w, btn_h, "", "#menu_settings")
            self.quit_btn = self._create_btn(cx, start_y + 405, btn_w, btn_h, "", "#menu_quit")


        elif self.state == "OPTIONS":
            # Đẩy các option lên cao hơn
            self.music_btn = self._create_btn(cx, 280, btn_w, btn_h, 
                                            f"MUSIC: {'ON' if self.is_music_on else 'OFF'}", "#ai_btn")
            self.sfx_btn = self._create_btn(cx, 385, btn_w, btn_h, 
                                           f"SOUND FX: {'ON' if self.is_sfx_on else 'OFF'}", "#ai_btn")
            
            # Side-by-side Resolution Buttons
            small_btn_w = (btn_w - 20) // 2
            self.res_1600_btn = self._create_btn(cx, 500, small_btn_w, btn_h, "1600x900", "#ai_btn")
            self.res_full_btn = self._create_btn(cx + small_btn_w + 20, 500, small_btn_w, btn_h, "FULLSCREEN", "#ai_btn")
            
            # QUAN TRỌNG: Nút BACK luôn cách cạnh dưới 120 pixel
            self.back_btn = self._create_btn(cx, curr_h - 120, btn_w, btn_h, "BACK", "#algo_btn")

    def _create_btn(self, x, y, w, h, text, obj_id):
        return pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((x, y), (w, h)),
            text=text, manager=self.manager, object_id=obj_id)

    def change_resolution(self, resolution_str):
        """
        Switch between fullscreen and windowed 1600x900.
        Nearest-neighbor scaling (SDL_RENDER_SCALE_QUALITY=0) is used to
        keep pixel fonts crisp and tear-free when GPU-scaled to fullscreen.
        """
        if resolution_str == "Fullscreen":
            # Force nearest-neighbor scaling BEFORE creating fullscreen mode
            # so pixel art and text scale with hard edges, not blurry bilinear
            os.environ['SDL_RENDER_SCALE_QUALITY'] = '0'
            pygame.display.set_mode((window_width, window_height), pygame.FULLSCREEN | pygame.SCALED)
        else:
            os.environ['SDL_RENDER_SCALE_QUALITY'] = '0'
            pygame.display.set_mode((window_width, window_height))

    def handle_events(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if self.is_sfx_on: self.sfx.play()
            ui = event.ui_element
            if self.state == "MAIN":
                if ui == self.play_btn: return "START_GAME"
                if ui == self.instr_btn: return "START_TUTORIAL"
                if ui == self.setting_btn: self.state = "OPTIONS"; self.setup_ui()
                if ui == self.quit_btn: return "QUIT"
            elif ui == getattr(self, 'back_btn', None):
                self.state = "MAIN"; self.setup_ui()
            elif self.state == "OPTIONS":
                if ui == self.music_btn:
                    self.is_music_on = not self.is_music_on
                    if self.is_music_on: self.music_channel.unpause()
                    else: self.music_channel.pause()
                    self.setup_ui()
                if ui == self.sfx_btn:
                    self.is_sfx_on = not self.is_sfx_on
                    self.setup_ui()
                if ui == getattr(self, 'res_1600_btn', None):
                    self.change_resolution("1600x900")
                if ui == getattr(self, 'res_full_btn', None):
                    self.change_resolution("Fullscreen")

        self.manager.process_events(event)
        return None

    def get_random_edge_pos(self, curr_w, curr_h):
        side = random.choice(["top", "bottom", "left", "right"])
        if side == "top": return random.randint(0, curr_w), -100
        elif side == "bottom": return random.randint(0, curr_w), curr_h + 100
        elif side == "left": return -100, random.randint(0, curr_h)
        else: return curr_w + 100, random.randint(0, curr_h)

    def spawn_object(self, idx, initial=False):
        curr_w, curr_h = window_width, window_height
        
        # 1. Choose random edge with a safe margin
        side = random.choice(["top", "bottom", "left", "right"])
        if side == "top": x, y = random.randint(0, curr_w), -self.margin
        elif side == "bottom": x, y = random.randint(0, curr_w), curr_h + self.margin
        elif side == "left": x, y = -self.margin, random.randint(0, curr_h)
        else: x, y = curr_w + self.margin, random.randint(0, curr_h)
        
        # 2. Randomize direction towards screen
        dx, dy = random.uniform(-1, 1), random.uniform(-1, 1)
        length = math.sqrt(dx*dx + dy*dy) or 1
        dx, dy = dx/length, dy/length
        
        if x < 0: dx = abs(dx)
        elif x > curr_w: dx = -abs(dx)
        if y < 0: dy = abs(dy)
        elif y > curr_h: dy = -abs(dy)
        
        # 3. Randomize properties (Ensure uniqueness)
        used_types = {o['type'] for i, o in enumerate(self.floating_objs) if i != idx}
        available_types = [t for t in self.anim_assets.keys() if t not in used_types]
        
        obj_type = random.choice(available_types) if available_types else random.choice(list(self.anim_assets.keys()))
        rot_speed = random.uniform(20, 60) * random.choice([-1, 1])
        speed_mod = random.uniform(0.8, 1.2)
        
        # 4. Construct object
        obj_data = {
            'pos': [x, y],
            'dir': [dx, dy],
            'type': obj_type,
            'rot': random.randint(0, 360),
            'rot_speed': rot_speed,
            'speed': self.fly_speed * speed_mod
        }
        
        if initial:
            self.floating_objs.append(obj_data)
        else:
            self.floating_objs[idx] = obj_data

    def draw(self, time_delta):
        self.window.blit(self.bg_pattern, (0, 0))
        self.window.blit(self.dark_overlay, (0, 0))
        
        curr_w, curr_h = window_width, window_height
        
        self.anim_time += time_delta

        if self.state == "MAIN":
            out_margin = 400 # Margin for deletion/reset
            
            for i, obj in enumerate(self.floating_objs):
                # Update Position
                obj['pos'][0] += obj['dir'][0] * obj['speed'] * time_delta
                obj['pos'][1] += obj['dir'][1] * obj['speed'] * time_delta
                
                # Update Rotation
                obj['rot'] += obj['rot_speed'] * time_delta
                
                # Check for reset (if too far off screen)
                if (obj['pos'][0] < -out_margin or obj['pos'][0] > curr_w + out_margin or 
                    obj['pos'][1] < -out_margin or obj['pos'][1] > curr_h + out_margin):
                    self.spawn_object(i)
                
                # Render
                asset = self.anim_assets.get(obj['type'])
                if asset:
                    rotated = pygame.transform.rotate(asset, obj['rot'])
                    rect = rotated.get_rect(center=(int(obj['pos'][0]), int(obj['pos'][1])))
                    self.window.blit(rotated, rect)

        # --- Draw UI Overlay ---
        font_title = pygame.font.Font(font_path, int(130 * (curr_h/900)))
        title_surf = font_title.render("SOKOBAN", False, self.TITLE_MAIN)
        title_rect = title_surf.get_rect(center=(curr_w // 2, curr_h * 0.2))
        shadow = font_title.render("SOKOBAN", False, self.DARK_SHADOW)
        self.window.blit(shadow, (title_rect.x + 6, title_rect.y + 6))
        self.window.blit(title_surf, title_rect)
        
        self.manager.update(time_delta)
        self.manager.draw_ui(self.window)

        # UI Border Padding
        pygame.draw.rect(self.window, BORDER_COLOR, (0, 0, curr_w, curr_h), BORDER_WIDTH)