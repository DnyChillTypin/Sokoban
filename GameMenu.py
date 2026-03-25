import pygame
import pygame_gui
from settings import *

class GameMenu:
    def __init__(self):
        self.manager = pygame_gui.UIManager((window_width, window_height))
        
        # Menu State
        self.expanded = False
        self.ai_dropdown_open = False
        self.selected_algos = {'A*'}
        
        # Pre-calculate the dimming surface for optimization
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
            relative_rect=pygame.Rect(10, 20, 250, 30),
            text="Level 0 Moves: 0",
            manager=self.manager,
            container=self.panel
        )

        self.ai_toggle_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(10, 70, 200, 40),
            text="AI Solver ▼",
            manager=self.manager,
            container=self.panel
        )

        self.algo_btns = {}
        y_offset = 110
        for algo in ['A*', 'BFS', 'DFS']:
            box_text = f"[X] {algo}" if algo in self.selected_algos else f"[ ] {algo}"
            btn = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(10, y_offset, 200, 30),
                text=box_text,
                manager=self.manager,
                container=self.panel,
                visible=False
            )
            self.algo_btns[algo] = btn
            y_offset += 30

        self.run_solver_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(10, y_offset + 5, 200, 40),
            text="Run Solver",
            manager=self.manager,
            container=self.panel,
            visible=False
        )

        self.toggle_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(menu_width - 30, (window_height // 2) - 40, 30, 80),
            text=">",
            manager=self.manager,
            container=self.panel
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
        
        for btn in self.algo_btns.values():
            btn.show() if self.ai_dropdown_open else btn.hide()
            
        self.run_solver_btn.show() if self.ai_dropdown_open else self.run_solver_btn.hide()

    def update_moves(self, count, level_num):
        self.move_label.set_text(f"Level {level_num} Moves: {count}")

    def process_events(self, event):
        """Processes UI events and returns a command string if the main game needs to do something."""
        self.manager.process_events(event)

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.toggle_btn:
                self.toggle_expansion()
            
            elif event.ui_element == self.ai_toggle_btn:
                if not self.expanded:
                    self.toggle_expansion()
                self.toggle_ai_dropdown()
            
            elif event.ui_element == self.run_solver_btn:
                # Tell main.py that the run button was clicked!
                return "RUN_SOLVER"
            
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