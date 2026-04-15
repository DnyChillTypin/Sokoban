import pygame
import pygame_gui
import os
import math
from settings import *

class SokobanMenu:
    def __init__(self, screen):
        self.window = screen
        # Khởi tạo Manager với file theme.json
        self.manager = pygame_gui.UIManager((window_width, window_height), UI_THEME)
        self.state = "MAIN"
        self.anim_time = 0

        self.fly_x1 = -200
        self.fly_x2 = window_width + 200
        self.fly_speed = 120
        self.box_started = False
        # Màu sắc tiêu đề
        self.TITLE_GREEN = (0, 255, 127)
        self.DARK_SHADOW = (0, 50, 0)
        self.BORDER_BROWN = (71, 45, 60) 

        curr_w, curr_h = self.window.get_size()
        self.dark_overlay = pygame.Surface((curr_w, curr_h))
        self.dark_overlay.fill((0, 0, 0))
        self.dark_overlay.set_alpha(150)

        # Audio logic
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
        """Chỉ load các nhân vật trang trí menu"""
        try:
            self.char_img = pygame.transform.scale(pygame.image.load(textures['player']).convert_alpha(), (350, 350))
            box_orig = pygame.image.load(textures['box_on_target']).convert_alpha()
            self.box_img = pygame.transform.rotate(pygame.transform.scale(box_orig, (350, 350)), -15)
        except:
            self.char_img = self.box_img = None

    def _create_btn(self, x, y, w, h, text, obj_id):
        """Hàm tạo button cơ bản"""
        return pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((x, y), (w, h)),
            text=text,
            manager=self.manager,
            object_id=obj_id
        )

    def setup_ui(self):
        self.manager.clear_and_reset()
        curr_w, curr_h = self.window.get_size()
        btn_w, btn_h = 420, 95
        cx = curr_w // 2 - btn_w // 2

        if self.state == "MAIN":
            start_y = curr_h // 2 - 100
            self.play_btn = self._create_btn(cx, start_y, btn_w, btn_h, "START GAME", "#ai_btn")
            self.instr_btn = self._create_btn(cx, start_y + 110, btn_w, btn_h, "INSTRUCTION", "#ai_btn")
            self.setting_btn = self._create_btn(cx, start_y + 220, btn_w, btn_h, "GAME OPTIONS", "#ai_btn")
            self.quit_btn = self._create_btn(cx, start_y + 330, btn_w, btn_h, "EXIT GAME", "#algo_btn")

        elif self.state == "INSTRUCTION":
            # Placeholder Instruction đẹp hơn, không có tiêu đề Sokoban đè lên
            box_w, box_h = int(curr_w * 0.75), int(curr_h * 0.65)
            box_x, box_y = (curr_w - box_w) // 2, (curr_h - box_h) // 2
            
            self.instr_panel = pygame_gui.elements.UIPanel(
                relative_rect=pygame.Rect((box_x, box_y), (box_w, box_h)),
                manager=self.manager, object_id="#instruction_panel"
            )
            
            text = ("<font color='#F0F0F0' size=5>"
                    "<br><p align='center'><font color='#00FF7F' size=7><b>HOW TO PLAY</b></font></p><br>"
                    "  • <b>MOVE:</b> Use Arrow Keys or W, A, S, D<br><br>"
                    "  • <b>GOAL:</b> Push all boxes onto the marked <b>X</b><br><br>"
                    "  • <b>RESET:</b> Press <b>R</b> if you get stuck<br><br>"
                    "  • <b>UNDO:</b> Press <b>Z</b> to go back one step<br></font>")

            self.help_box = pygame_gui.elements.UITextBox(
                html_text=text,
                relative_rect=pygame.Rect((20, 20), (box_w - 40, box_h - 40)),
                manager=self.manager, container=self.instr_panel, object_id="#instr_text"
            )
            self.back_btn = self._create_btn(cx, curr_h - 120, btn_w, btn_h, "BACK", "#algo_btn")

        elif self.state == "OPTIONS":
            self.music_btn = self._create_btn(cx, 280, btn_w, btn_h, f"MUSIC: {'ON' if self.is_music_on else 'OFF'}", "#ai_btn")
            self.sfx_btn = self._create_btn(cx, 385, btn_w, btn_h, f"SOUND FX: {'ON' if self.is_sfx_on else 'OFF'}", "#ai_btn")
            
            # Nút xoay vòng Resolution
            res_val = f"{curr_w}x{curr_h}" if not (self.window.get_flags() & pygame.FULLSCREEN) else "FULLSCREEN"
            self.res_cycle_btn = self._create_btn(cx, 490, btn_w, btn_h, f"RES: {res_val}", "#ai_btn")
            
            self.back_btn = self._create_btn(cx, curr_h - 120, btn_w, btn_h, "BACK", "#algo_btn")

    def change_resolution(self, res_str):
        if res_str == "FULLSCREEN":
            pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            w, h = map(int, res_str.split('x'))
            os.environ['SDL_VIDEO_CENTERED'] = '1'
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
            elif self.state == "OPTIONS" and ui == getattr(self, 'res_cycle_btn', None):
                res_list = ["1600x900", "1280x720", "FULLSCREEN"]
                current = ui.text.replace("RES: ", "")
                next_res = res_list[(res_list.index(current) + 1) % len(res_list)] if current in res_list else res_list[0]
                self.change_resolution(next_res)
            elif self.state == "OPTIONS":
                if ui == self.music_btn:
                    self.is_music_on = not self.is_music_on
                    if self.is_music_on: self.music_channel.unpause()
                    else: self.music_channel.pause()
                    self.setup_ui()
                if ui == self.sfx_btn:
                    self.is_sfx_on = not self.is_sfx_on
                    self.setup_ui()
        self.manager.process_events(event)
        return None

    def draw_custom_border(self):
        w, h = self.window.get_size()
        border_color = (54, 40, 48) 
        
        pygame.draw.rect(self.window, border_color, (0, 0, w, h), 5)

    def draw(self, time_delta):
        self.window.blit(self.bg_pattern, (0, 0))
        self.window.blit(self.dark_overlay, (0, 0))
        curr_w, curr_h = self.window.get_size()

        btn_w, btn_h = 420, 95
        cx = curr_w // 2 - btn_w // 2

        if self.anim_time >= 3 and not self.box_started:
            self.fly_x2 = curr_w + 200
            self.box_started = True
        self.anim_time += time_delta

        if self.fly_x1 > curr_w + 300:
            self.fly_x1 = -300

        if self.fly_x2 < -300:
            self.fly_x2 = curr_w + 300

        # Ẩn tiêu đề khi ở Instruction
        if self.state != "INSTRUCTION":
            font_title = pygame.font.Font(font_path, int(130 * (curr_h/900)))
            title_surf = font_title.render("SOKOBAN", True, self.TITLE_GREEN)
            title_rect = title_surf.get_rect(center=(curr_w // 2, curr_h * 0.2))
            shadow = font_title.render("SOKOBAN", True, self.DARK_SHADOW)
            self.window.blit(shadow, (title_rect.x + 6, title_rect.y + 6))
            self.window.blit(title_surf, title_rect)

        if self.state == "MAIN":
            curr_w, curr_h = self.window.get_size()

            # cập nhật vị trí bay ngang
            self.fly_x1 += self.fly_speed * time_delta
            if self.anim_time >= 3:
                self.fly_x2 -= self.fly_speed * time_delta

            # reset khi bay ra ngoài màn hình
            if self.fly_x1 > curr_w + 200:
                self.fly_x1 = -200

            if self.fly_x2 < -200:
                self.fly_x2 = curr_w + 200

            # thời gian
            t = self.anim_time

            # ================== PLAYER (bay trên) ==================
            if self.char_img:

                progress1 = self.fly_x1 / curr_w

                y1 = (curr_h * 0.5) - progress1 * (curr_h * 0.4)

                # thêm chút cong (parabol nhẹ)
                y1 -= 100 * (progress1 - 0.5) ** 2

                # xoay nhẹ
                angle1 = self.anim_time * 25
                rotated_char = pygame.transform.rotate(self.char_img, angle1)

                rect1 = rotated_char.get_rect(center=(self.fly_x1, y1))

                self.window.blit(rotated_char, rect1)

            # ================== BOX (bay dưới) ==================
            if self.box_img and self.anim_time >= 3:
                # lệch pha để nhìn tự nhiên
                progress2 = self.fly_x2 / curr_w

                # bay chéo xuống
                y2 = (curr_h * 0.4) + progress2 * (curr_h * 0.5)

                # cong nhẹ
                y2 -= 100 * (progress2 - 0.5) ** 2

                angle2 = -self.anim_time * 30
                rotated_box = pygame.transform.rotate(self.box_img, angle2)

                rect2 = rotated_box.get_rect(center=(self.fly_x2, y2))

                self.window.blit(rotated_box, rect2)
        
        self.manager.update(time_delta)
        self.manager.draw_ui(self.window)

        curr_w, curr_h = self.window.get_size()
        pygame.draw.rect(self.window, self.BORDER_BROWN, (0, 0, curr_w, curr_h), 5)