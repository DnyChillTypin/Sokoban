import pygame
import pygame_gui
import json
import os

os.environ['SDL_VIDEO_CENTERED'] = '1'

class SokobanMenu:
    def __init__(self, screen):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.mixer.init()
        
        self.window = screen
        self.width, self.height = screen.get_size()
        self.manager = pygame_gui.UIManager((self.width, self.height))
        self.state = "MAIN"
        
        self.COLORS = {
            'bg': (15, 25, 45),
            'title': (255, 215, 0),
            'btn_normal': (40, 55, 80)
        }

        self.instr_frames = []
        self.current_frame = 0
        self.frame_timer = 0
        self.load_instr_animation()

        try:
            with open("env.json", "r") as f:
                self.config = json.load(f)
        except:
            self.config = {"music": "On", "sound": "On", "resolution": "1024x768"}

        self.play_bg_music()
        self.setup_ui()

    def load_instr_animation(self):
        path = "assets/instruction_anim/"
        if os.path.exists(path):
            files = sorted([f for f in os.listdir(path) if f.endswith('.png')])
            for f in files:
                img = pygame.image.load(os.path.join(path, f)).convert_alpha()
                img = pygame.transform.scale(img, (350, 350))
                self.instr_frames.append(img)

    def play_bg_music(self):
        if self.config.get('music') == "On":
            music_path = os.path.join("assets", "bg_music.mp3")
            if os.path.exists(music_path):
                try:
                    pygame.mixer.music.load(music_path)
                    pygame.mixer.music.set_volume(0.4)
                    pygame.mixer.music.play(-1)
                except: pass

    def setup_ui(self):
        self.manager.clear_and_reset()
        
        # Kích thước nút cố định nhưng căn lề động
        btn_w, btn_h = 420, 85 
        spacing = 100 
        
        if self.state == "MAIN":
            # Neo vào tâm X, căn từ trên xuống
            start_y = self.height // 2 - 100
            self.play_btn = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((self.width//2 - btn_w//2, start_y), (btn_w, btn_h)), text='PLAY', manager=self.manager)
            self.instr_btn = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((self.width//2 - btn_w//2, start_y + spacing), (btn_w, btn_h)), text='INSTRUCTION', manager=self.manager)
            self.setting_btn = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((self.width//2 - btn_w//2, start_y + spacing*2), (btn_w, btn_h)), text='SETTING', manager=self.manager)
            self.quit_btn = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((self.width//2 - btn_w//2, start_y + spacing*3), (btn_w, btn_h)), text='QUIT', manager=self.manager)

        elif self.state == "SETTINGS":
            center_y = self.height // 2 - 100
            self.music_btn = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((self.width//2 - btn_w//2, center_y), (btn_w, btn_h)), text=f"Music: {self.config['music']}", manager=self.manager)
            
            res_list = ["800x600", "1024x768", "Fullscreen"]
            drop_y = center_y + spacing
            self.res_dropdown = pygame_gui.elements.UIDropDownMenu(options_list=res_list, starting_option=self.config['resolution'], relative_rect=pygame.Rect((self.width//2 - btn_w//2, drop_y), (btn_w, btn_h)), manager=self.manager)
            
            # Nút BACK gần hơn (cách 20px)
            self.back_btn = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((self.width//2 - 100, drop_y + btn_h + 20), (200, 60)), text='BACK', manager=self.manager)

        elif self.state == "INSTR":
            box_w, box_h = 850, 480
            # Giữ box luôn ở giữa màn hình
            bx = self.width // 2 - box_w // 2
            by = self.height // 2 - box_h // 2 - 30
            
            help_text = "<font color='#FFD700' size=7><b>HOW TO PLAY</b></font><br><br>" \
                        "<font size=6>" \
                        "- ARROW KEYS: Move player around<br>" \
                        "- U KEY: Undo your last move<br>" \
                        "- R KEY: Reset current level<br>" \
                        "- ESC/Q: Quit to main menu</font>"
            
            self.help_box = pygame_gui.elements.UITextBox(
                html_text=help_text, 
                relative_rect=pygame.Rect((bx, by), (box_w, box_h)), 
                manager=self.manager)
            
            self.anim_rect = pygame.Rect(bx + box_w - 360, by + 100, 320, 320)
            
            # Nút GOT IT gần sát box (cách 10px)
            self.back_btn = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect((self.width // 2 - 100, by + box_h + 10), (200, 60)), 
                text='GOT IT!', manager=self.manager)

    def handle_events(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if self.state == "MAIN":
                if event.ui_element == self.play_btn: return "START_GAME"
                if event.ui_element == self.instr_btn: self.state = "INSTR"; self.setup_ui()
                if event.ui_element == self.setting_btn: self.state = "SETTINGS"; self.setup_ui()
                if event.ui_element == self.quit_btn: return "QUIT"
            if event.ui_element == self.back_btn:
                self.save_config(); self.state = "MAIN"; self.setup_ui()
            elif self.state == "SETTINGS" and event.ui_element == self.music_btn:
                self.config['music'] = "Off" if self.config['music'] == "On" else "On"
                if self.config['music'] == "Off": pygame.mixer.music.pause()
                else: pygame.mixer.music.unpause() if pygame.mixer.music.get_busy() else self.play_bg_music()
                self.music_btn.set_text(f"Music: {self.config['music']}")
        
        if event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            if event.ui_element == self.res_dropdown:
                self.config['resolution'] = event.text
                self.apply_video_settings()
        
        self.manager.process_events(event)
        return None

    def apply_video_settings(self):
        if self.config['resolution'] == "Fullscreen":
            info = pygame.display.Info()
            new_res = (info.current_w, info.current_h)
            flags = pygame.FULLSCREEN
        else:
            new_res = tuple(map(int, self.config['resolution'].split('x')))
            flags = pygame.RESIZABLE 
        
        self.window = pygame.display.set_mode(new_res, flags)
        self.width, self.height = new_res
        self.manager.set_window_resolution(new_res)
        pygame.display.set_caption("Sokoban Game")
        self.setup_ui()

    def draw(self, time_delta):
        self.window.fill(self.COLORS['bg']) 
        if self.state == "MAIN":
            title_font = pygame.font.SysFont("Verdana", 90, bold=True)
            title_surf = title_font.render("SOKOBAN", True, self.COLORS['title'])
            self.window.blit(title_surf, title_surf.get_rect(center=(self.width // 2, self.height // 2 - 220)))
        
        elif self.state == "INSTR":
            if self.instr_frames:
                self.frame_timer += time_delta
                if self.frame_timer > 0.1:
                    self.current_frame = (self.current_frame + 1) % len(self.instr_frames)
                    self.frame_timer = 0
                self.window.blit(self.instr_frames[self.current_frame], self.anim_rect)
        
        self.manager.update(time_delta)
        self.manager.draw_ui(self.window)

    def save_config(self):
        with open("env.json", "w") as f:
            json.dump(self.config, f)