import pygame
import math
from settings import font_path, window_width, window_height

class RadarChart:
    def __init__(self, center, radius, font_size, color_map):
        self.center = center
        self.radius = radius
        self.color_map = color_map
        self.font = pygame.font.Font(font_path, font_size)
        self.metrics = ['Time', 'Nodes', 'Moves', 'Pushes', 'Fringe', 'Pruned']
        self.metric_keys = ['time', 'visited', 'moves', 'pushes', 'max_fringe', 'pruned']
        self.num_metrics = len(self.metrics)
        self.angles = [-math.pi / 2 + (2 * math.pi * i) / self.num_metrics for i in range(self.num_metrics)]
        self.data_snapshots = {}
        self.max_bounds = {k: 0.1 for k in self.metric_keys}

        self.hovered_algo = None
        self.hover_start_time = 0
        self.HOVER_DELAY_MS = 500
        self.legend_hitboxes = []
        
        # Animation Queue System
        self.anim_queue = [] # List of (algo_name, metrics_dict)
        self.active_algo = None
        self.active_metrics = None
        self.finished_algos = {} # algo_name -> metrics_dict
        
        self.progress = 0.0
        self.ANIMATION_SPEED = 2.0 # Progress per second (0.5s duration)
        
        # Normalization Bounds
        self.old_max_bounds = {k: 0.1 for k in self.metric_keys}
        self.new_max_bounds = {k: 0.1 for k in self.metric_keys}

    def _get_max_bounds(self, algorithms_dict):
        bounds = {k: 0.1 for k in self.metric_keys}
        for metrics in algorithms_dict.values():
            if metrics is None or not isinstance(metrics, dict): continue
            for k in self.metric_keys:
                val = metrics.get(k, 0)
                if val == "FAIL": val = 0
                bounds[k] = max(bounds[k], float(val))
        for k in bounds:
            if bounds[k] <= 0: bounds[k] = 1.0
        return bounds

    def add_to_queue(self, algo_name, metrics):
        """Add a new algorithm result to the sequential animation queue."""
        # Check if already finished, currently active, or already in the queue
        if algo_name in self.finished_algos or (self.active_algo == algo_name):
            return
            
        if any(name == algo_name for name, _ in self.anim_queue):
            return
            
        self.anim_queue.append((algo_name, metrics))
        if self.active_algo is None:
            self._start_next_animation()

    def _start_next_animation(self):
        if not self.anim_queue:
            self.active_algo = None
            self.active_metrics = None
            return

        self.active_algo, self.active_metrics = self.anim_queue.pop(0)
        self.progress = 0.0
        self.old_max_bounds = self._get_max_bounds(self.finished_algos)
        
        temp_finished = self.finished_algos.copy()
        temp_finished[self.active_algo] = self.active_metrics
        self.new_max_bounds = self._get_max_bounds(temp_finished)

    def update(self, dt):
        """Tick the animation state machine driven by delta time."""
        if self.active_algo is None:
            if self.anim_queue:
                self._start_next_animation()
            return

        # Safety: Cap dt to 100ms to prevent animation skipping after long solver freezes
        capped_dt = min(dt, 0.1)
        self.progress += capped_dt * self.ANIMATION_SPEED
        if self.progress >= 1.0:
            self.progress = 1.0
            self.finished_algos[self.active_algo] = self.active_metrics
            self._start_next_animation()

    def reset(self):
        """Clear all snapshots and queues."""
        self.anim_queue.clear()
        self.active_algo = None
        self.active_metrics = None
        self.finished_algos.clear()
        self.progress = 0.0
        self.old_max_bounds = {k: 0.1 for k in self.metric_keys}
        self.new_max_bounds = {k: 0.1 for k in self.metric_keys}

    def trigger_replay(self, metrics_map):
        """Re-queue all provided results for a fresh animation cycle."""
        self.reset()
        for name, metrics in metrics_map.items():
            self.add_to_queue(name, metrics)

    def _draw_tooltip(self, surface, algo, mouse_pos):
        """Draw a detailed metrics tooltip near the mouse cursor."""
        metrics = self.finished_algos.get(algo)
        if not metrics or not isinstance(metrics, dict):
            return

        # Build tooltip lines
        path = metrics.get('path')
        moves_val = "FAIL" if not path else str(len(path))
        pushes_val = metrics.get('pushes', 'N/A')
        if pushes_val == "FAIL" or not path:
            pushes_val = "FAIL"

        tooltip_lines = [
            f"Time (s): {metrics.get('time', 0):.4f}",
            f"Visited: {metrics.get('visited', 0)}",
            f"Generated: {metrics.get('generated', 0)}",
            f"Max Mem: {metrics.get('max_fringe', 0)}",
            f"Pruned: {metrics.get('pruned', 0)}",
            f"Pushes: {pushes_val}",
            f"Moves: {moves_val}",
        ]

        # Render text surfaces
        padding_x, padding_y = 14, 10
        line_spacing = 6
        text_surfs = [self.font.render(line, True, (220, 220, 220)) for line in tooltip_lines]

        max_text_w = max(s.get_width() for s in text_surfs)
        total_text_h = sum(s.get_height() for s in text_surfs) + line_spacing * (len(text_surfs) - 1)

        box_w = max_text_w + padding_x * 2
        box_h = total_text_h + padding_y * 2

        # Position near cursor with screen clamping
        tx = mouse_pos[0] + 16
        ty = mouse_pos[1] + 16

        if tx + box_w > window_width:
            tx = mouse_pos[0] - box_w - 8
        if ty + box_h > window_height:
            ty = mouse_pos[1] - box_h - 8
        if tx < 0:
            tx = 4
        if ty < 0:
            ty = 4

        # Draw background
        tooltip_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        tooltip_surf.fill((20, 20, 25, 230))
        surface.blit(tooltip_surf, (tx, ty))

        # Draw border
        border_color = self.color_map.get(algo, (180, 180, 180))
        pygame.draw.rect(surface, border_color, (tx, ty, box_w, box_h), 2)

        # Draw text lines
        cur_y = ty + padding_y
        for ts in text_surfs:
            surface.blit(ts, (tx + padding_x, cur_y))
            cur_y += ts.get_height() + line_spacing

    def draw(self, surface, visible_algos=None):
        if not self.finished_algos and not self.active_algo:
            return

        cx, cy = self.center

        def draw_pixel_star(surf, cx, cy, color):
            """Draws a small 5x5 pixel-art style star"""
            offsets = [(0,0), (0,-1), (0,1), (-1,0), (1,0), (0,-2), (0,2), (-2,0), (2,0), (-1,-1), (1,-1), (-1,1), (1,1)]
            for dx, dy in offsets:
                surf.set_at((cx + dx, cy + dy), color)

        # 1. Calculate Current Max Bounds (LERP between old and new)
        current_max_bounds = {}
        for k in self.metric_keys:
            old = self.old_max_bounds[k]
            new = self.new_max_bounds[k]
            current_max_bounds[k] = old + (new - old) * self.progress

        # 2. Draw web backgrounds (wireframes)
        num_rings = 4
        for r in range(1, num_rings + 1):
            ratio = r / num_rings
            points = []
            for angle in self.angles:
                px = cx + self.radius * ratio * math.cos(angle)
                py = cy + self.radius * ratio * math.sin(angle)
                points.append((px, py))
            pygame.draw.polygon(surface, (140, 140, 140), points, 2)

        # 3. Draw spokes and labels
        for i, angle in enumerate(self.angles):
            px = cx + self.radius * math.cos(angle)
            py = cy + self.radius * math.sin(angle)
            pygame.draw.line(surface, (140, 140, 140), (cx, cy), (px, py), 2)
            label_text = self.metrics[i]
            lx = cx + (self.radius + 35) * math.cos(angle)
            ly = cy + (self.radius + 35) * math.sin(angle)
            txt_surf = self.font.render(label_text, True, (248, 244, 239)) # Cream color
            rect = txt_surf.get_rect(center=(lx, ly))
            surface.blit(txt_surf, rect)

        # 4. Collection for rendering
        surf_w = int(self.radius * 3)
        surf_h = int(self.radius * 3)
        poly_surface = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)
        poly_center = (surf_w // 2, surf_h // 2)

        def get_poly_points(center, metrics, bounds, scale=1.0):
            pts = []
            for i, k in enumerate(self.metric_keys):
                val = metrics.get(k, 0)
                if val == "FAIL": val = 0
                normalized = float(val) / bounds[k]
                
                # AXIS_BUFFER: prevent vertices from touching the physical edge (makes differences more visible)
                AXIS_BUFFER = 0.88 
                dist = self.radius * (AXIS_BUFFER * min(normalized, scale))
                
                px = center[0] + dist * math.cos(self.angles[i])
                py = center[1] + dist * math.sin(self.angles[i])
                pts.append((px, py))
            return pts

        # Combine finished and active for drawing
        all_to_draw = list(self.finished_algos.items())
        if self.active_algo:
            all_to_draw.append((self.active_algo, self.active_metrics))

        for algo, metrics in all_to_draw:
            if not metrics or not isinstance(metrics, dict):
                continue
            if visible_algos is not None and algo not in visible_algos:
                continue

            # Vertex Split: expanding algo starts at scale 0.0, others stay at 1.0 (relative to lerped bounds)
            scale = self.progress if algo == self.active_algo else 1.0
            color = self.color_map.get(algo, (255, 255, 255))
            poly_points = get_poly_points(poly_center, metrics, current_max_bounds, scale)
            
            if len(poly_points) >= 3:
                algo_surf = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)
                pygame.draw.polygon(algo_surf, (*color, 30), poly_points)
                pygame.draw.polygon(algo_surf, (*color, 255), poly_points, 3)
                poly_surface.blit(algo_surf, (0, 0))

        # Legend Logic
        row1_keys = ['BFS', 'DFS', 'BestFS']
        row2_keys = ['Dijkstra', 'A*']
        get_active = lambda keys: [(k, self.finished_algos.get(k) or (self.active_metrics if k == self.active_algo else None)) 
                                   for k in keys if (k in self.finished_algos or k == self.active_algo) 
                                   and (visible_algos is None or k in visible_algos)]
        
        row1_algos = get_active(row1_keys)
        row2_algos = get_active(row2_keys)
        spacing = 160
        legend_start_y = cy + self.radius + 60
        self.legend_hitboxes = []

        def draw_row(algos, start_y):
            row_width = (len(algos) - 1) * spacing + 100
            row_start_x = cx - row_width // 2
            for i, (algo, _) in enumerate(algos):
                color = self.color_map.get(algo, (255, 255, 255))
                lx, ly = row_start_x + (i * spacing), start_y
                pygame.draw.rect(surface, color, (lx, ly, 20, 20))
                display_name = "A" if algo.lower() == "a*" else algo.upper()
                txt_surf = self.font.render(display_name, True, (255, 255, 255))
                surface.blit(txt_surf, (lx + 30, ly))
                if algo.lower() == "a*": draw_pixel_star(surface, lx + 30 + txt_surf.get_width() + 6, ly + 6, (255, 255, 255))
                text_w = txt_surf.get_width() + (16 if algo.lower() == "a*" else 0)
                self.legend_hitboxes.append((algo, pygame.Rect(lx, ly, 30 + text_w, max(20, txt_surf.get_height()))))

        if row1_algos: draw_row(row1_algos, legend_start_y)
        if row2_algos: draw_row(row2_algos, legend_start_y + 40)

        surface.blit(poly_surface, (cx - poly_center[0], cy - poly_center[1]))

    def draw_tooltip(self, surface):
        """Logic to detect hover and render the top-layer tooltip."""
        if not self.finished_algos and not self.active_algo:
            return

        mouse_pos = pygame.mouse.get_pos()
        current_hover = None
        
        for algo, hitbox in self.legend_hitboxes:
            if hitbox.collidepoint(mouse_pos):
                current_hover = algo
                break

        now = pygame.time.get_ticks()

        if current_hover != self.hovered_algo:
            # Mouse moved to a different item (or left all items)
            self.hovered_algo = current_hover
            self.hover_start_time = now
            
        if self.hovered_algo and (now - self.hover_start_time > self.HOVER_DELAY_MS):
            self._draw_tooltip(surface, self.hovered_algo, mouse_pos)
