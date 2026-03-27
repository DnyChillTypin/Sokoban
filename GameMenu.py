import pygame
import pygame_gui
from settings import *

class GameMenu:
    def __init__(self):
        self.manager = pygame_gui.UIManager((window_width, window_height), 'theme.json')
        self.expanded = False
        self.ai_dropdown_open = False
        self.selected_algos = set() 
        
        self.playback_btns = {} 
        
        self.dim_surf = pygame.Surface((window_width, window_height), pygame.SRCALPHA)
        self.dim_surf.fill((0, 0, 0, 102))

        self.setup_ui()

    def setup_ui(self):
        self.panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(0, 0, menu_width, window_height),
            starting_height=1,
            manager=self.manager
        )

        self.move_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 20, 250, 40),
            text="Level 0 Moves: 0",
            manager=self.manager,
            container=self.panel
        )

        self.ai_toggle_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(10, 70, 250, 75),
            text="AI Solver ▼",
            manager=self.manager,
            container=self.panel,
            object_id=pygame_gui.core.ObjectID(class_id='@main_btn') 
        )

        self.algo_btns = {}
        y_offset = 155
        algos = ['BFS', 'DFS', 'A*', 'Best-FS']
        for algo in algos:
            box_text = f"[X] {algo}" if algo in self.selected_algos else f"[ ] {algo}"
            # --- NEW: Scaled up to 250x75 and tagged with @main_btn ---
            btn = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(10, y_offset, 250, 75), 
                text=box_text, manager=self.manager, container=self.panel, visible=False,
                object_id=pygame_gui.core.ObjectID(class_id='@main_btn') 
            )
            self.algo_btns[algo] = btn
            y_offset += 85 # --- NEW: Increased spacing to fit the big buttons ---

        self.run_solver_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(10, y_offset + 10, 250, 75),
            text="Run Solver", manager=self.manager, container=self.panel, visible=False,
            object_id=pygame_gui.core.ObjectID(class_id='@main_btn')
        )

        self.toggle_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(menu_width - 30, (window_height // 2) - 40, 30, 80),
            text=">", manager=self.manager, container=self.panel
        )

    def toggle_expansion(self):
        self.expanded = not self.expanded
        target_width = (window_width // 2) if self.expanded else menu_width

        self.panel.set_dimensions((target_width, window_height))
        self.toggle_btn.set_relative_position((target_width - 30, (window_height // 2) - 40))
        self.toggle_btn.set_text("<" if self.expanded else ">")
        
        if not self.expanded and self.ai_dropdown_open:
            self.toggle_ai_dropdown()

    def toggle_ai_dropdown(self):
        self.ai_dropdown_open = not self.ai_dropdown_open
        self.ai_toggle_btn.set_text("AI Solver ▲" if self.ai_dropdown_open else "AI Solver ▼")
        
        if len(self.playback_btns) > 0:
            for btn in self.playback_btns.values():
                btn.show() if self.ai_dropdown_open else btn.hide()
        else:
            for btn in self.algo_btns.values():
                btn.show() if self.ai_dropdown_open else btn.hide()
            self.run_solver_btn.show() if self.ai_dropdown_open else self.run_solver_btn.hide()

    def update_moves(self, count, level_num):
        self.move_label.set_text(f"Level {level_num} Moves: {count}")

    def reset_ai_menu(self):
        for btn in self.playback_btns.values():
            btn.kill()
        self.playback_btns.clear()
        
        if self.ai_dropdown_open:
            for btn in self.algo_btns.values(): btn.show()
            self.run_solver_btn.show()

    def show_results(self, results_dict):
        for btn in self.algo_btns.values(): btn.hide()
        self.run_solver_btn.hide()
        
        for btn in self.playback_btns.values(): btn.kill()
        self.playback_btns.clear()
        
        self.ai_dropdown_open = True
        self.ai_toggle_btn.set_text("AI Solver ▲")
        
        y_offset = 155
        for algo, path in results_dict.items():
            if path is not None:
                text = f"Watch {algo} ({len(path)} steps)"
            else:
                text = f"{algo} Deadlocked"
                
            btn = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(10, y_offset, 250, 75), 
                text=text, manager=self.manager, container=self.panel,
                object_id=pygame_gui.core.ObjectID(class_id='@main_btn')
            )
            self.playback_btns[algo] = btn
            y_offset += 85

    def process_events(self, event):
        self.manager.process_events(event)

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.toggle_btn:
                self.toggle_expansion()
            elif event.ui_element == self.ai_toggle_btn:
                if not self.expanded: self.toggle_expansion()
                self.toggle_ai_dropdown()
            elif event.ui_element == self.run_solver_btn:
                return "RUN_SOLVER"
            elif event.ui_element in self.playback_btns.values():
                for algo, btn in self.playback_btns.items():
                    if event.ui_element == btn:
                        return f"PLAYBACK_{algo}"
            else:
                for algo_name, btn_element in self.algo_btns.items():
                    if event.ui_element == btn_element:
                        if algo_name in self.selected_algos:
                            self.selected_algos.remove(algo_name)
                        else:
                            self.selected_algos.add(algo_name)
                        btn_element.set_text(f"[X] {algo_name}" if algo_name in self.selected_algos else f"[ ] {algo_name}")
        return None

    def update(self, time_delta):
        self.manager.update(time_delta)

    def draw(self, surface):
        if self.expanded:
            surface.blit(self.dim_surf, (0, 0))
        self.manager.draw_ui(surface)