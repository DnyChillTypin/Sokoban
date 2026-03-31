import pygame
import pygame_gui
import os
from settings import *

class SokobanMenu:
    def __init__(self, screen):
        self.window = screen
        self.manager = pygame_gui.UIManager((window_width, window_height), UI_THEME)
        self.state = "MAIN"
        
        self.TITLE_GREEN = (0, 255, 127) 
        self.DARK_SHADOW = (0, 50, 0)
        
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
        self.load_assets()
        self.setup_ui()

    def create_bg_pattern(self):
        curr_w, curr_h = self.window.get_size()
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
        try:
            orig_char = pygame.image.load(textures['player']).convert_alpha()
            self.char_img = pygame.transform.scale(orig_char, (350, 350))
            orig_box = pygame.image.load(textures['box_on_target']).convert_alpha()
            self.box_img = pygame.transform.scale(orig_box, (350, 350))
            self.box_img = pygame.transform.rotate(self.box_img, -15)
        except:
            self.char_img = self.box_img = None

    def setup_ui(self):
        """Tính toán vị trí dựa trên phần trăm hoặc khoảng cách từ cạnh dưới"""
        self.manager.clear_and_reset()
        curr_w, curr_h = self.window.get_size()
        self.manager.set_window_resolution((curr_w, curr_h))
        
        btn_w, btn_h = 420, 95
        cx = curr_w // 2 - btn_w // 2
        
        if self.state == "MAIN":
            # Căn giữa theo chiều dọc dựa trên curr_h
            start_y = curr_h // 2 - 100
            self.play_btn = self._create_btn(cx, start_y, btn_w, btn_h, "START GAME", "#ai_btn")
            self.instr_btn = self._create_btn(cx, start_y + 110, btn_w, btn_h, "INSTRUCTION", "#ai_btn")
            self.setting_btn = self._create_btn(cx, start_y + 220, btn_w, btn_h, "GAME OPTIONS", "#ai_btn")
            self.quit_btn = self._create_btn(cx, start_y + 330, btn_w, btn_h, "EXIT GAME", "#algo_btn")

        elif self.state == "INSTRUCTION":
            # Tính toán kích thước hộp văn bản linh hoạt
            box_w, box_h = int(curr_w * 0.6), int(curr_h * 0.4)
            box_x = curr_w // 2 - box_w // 2
            box_y = curr_h // 2 - box_h // 2
            
            # Nội dung hướng dẫn cho người chơi
            text = ("<font color='#FFFFFF' size=5><b>HƯỚNG DẪN CHƠI:</b><br><br>"
                    "- <b>Di chuyển:</b> Sử dụng các phím mũi tên hoặc W, A, S, D.<br>"
                    "- <b>Mục tiêu:</b> Đẩy tất cả các thùng vào vị trí đánh dấu X.<br>"
                    "- <b>Chơi lại:</b> Nhấn phím <b>R</b> nếu bạn bị kẹt.<br>"
                    "- <b>Hoàn tác:</b> Nhấn phím <b>Z</b> để lùi lại một bước.<br>"
                    "- <b>Gợi ý:</b> Nhấn nút <b>HINT</b> để xem AI chỉ cách di chuyển.</font>")
            
            self.help_box = pygame_gui.elements.UITextBox(
                html_text=text, 
                manager=self.manager,
                relative_rect=pygame.Rect((box_x, box_y), (box_w, box_h)))
            
            # Nút BACK luôn nằm dưới hộp văn bản và cách cạnh dưới an toàn
            self.back_btn = self._create_btn(cx, curr_h - 120, btn_w, btn_h, "BACK", "#algo_btn")

        elif self.state == "OPTIONS":
            # Đẩy các option lên cao hơn
            self.music_btn = self._create_btn(cx, 280, btn_w, btn_h, 
                                            f"MUSIC: {'ON' if self.is_music_on else 'OFF'}", "#ai_btn")
            self.sfx_btn = self._create_btn(cx, 385, btn_w, btn_h, 
                                           f"SOUND FX: {'ON' if self.is_sfx_on else 'OFF'}", "#ai_btn")
            
            self.res_label = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect((cx, 500), (btn_w, 40)),
                text="RESOLUTION", manager=self.manager, object_id="#ai_btn")
            
            self.res_drop = pygame_gui.elements.UIDropDownMenu(
                options_list=["1600x900", "1280x720", "Fullscreen"],
                starting_option=f"{curr_w}x{curr_h}" if not (self.window.get_flags() & pygame.FULLSCREEN) else "Fullscreen",
                relative_rect=pygame.Rect((cx, 550), (btn_w, 50)), manager=self.manager)
            
            # QUAN TRỌNG: Nút BACK luôn cách cạnh dưới 120 pixel
            self.back_btn = self._create_btn(cx, curr_h - 120, btn_w, btn_h, "BACK", "#algo_btn")

    def _create_btn(self, x, y, w, h, text, obj_id):
        return pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((x, y), (w, h)),
            text=text, manager=self.manager, object_id=obj_id)

    def change_resolution(self, resolution_str):
        if resolution_str == "Fullscreen":
            pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            w, h = map(int, resolution_str.split('x'))
            os.environ['SDL_VIDEO_CENTERED'] = '1' # Đảm bảo ra giữa màn hình
            pygame.display.set_mode((w, h))
        
        self.bg_pattern = self.create_bg_pattern()
        self.setup_ui()

    def handle_events(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if self.is_sfx_on: self.sfx.play()
            ui = event.ui_element
            if self.state == "MAIN":
                if ui == self.play_btn: return "START_GAME"
                if ui == self.instr_btn: self.state = "INSTRUCTION"; self.setup_ui()
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

        if event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            if event.ui_element == self.res_drop:
                self.change_resolution(event.text)

        self.manager.process_events(event)
        return None

    def draw(self, time_delta):
        self.window.blit(self.bg_pattern, (0, 0))
        curr_w, curr_h = self.window.get_size()
        
        font_title = pygame.font.Font(font_path, int(130 * (curr_h/900))) # Co giãn font theo màn hình
        title_surf = font_title.render("SOKOBAN", True, self.TITLE_GREEN)
        title_rect = title_surf.get_rect(center=(curr_w // 2, curr_h * 0.2)) # Tiêu đề luôn ở 20% chiều cao
        shadow = font_title.render("SOKOBAN", True, self.DARK_SHADOW)
        self.window.blit(shadow, (title_rect.x + 6, title_rect.y + 6))
        self.window.blit(title_surf, title_rect)

        if self.state == "MAIN":
            if self.char_img: 
                # Icon tự động lùi ra xa nếu màn hình hẹp
                self.window.blit(self.char_img, (curr_w * 0.1, curr_h * 0.4))
            if self.box_img: 
                self.window.blit(self.box_img, (curr_w * 0.7, curr_h * 0.4))
        
        self.manager.update(time_delta)
        self.manager.draw_ui(self.window)