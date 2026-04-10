import pygame
import math
from settings import font_path, window_width, window_height

class RadarChart:
    def __init__(self, center, radius, font_size, color_map):
        self.center = center
        self.radius = radius
        self.color_map = color_map
        self.font = pygame.font.Font(font_path, font_size)
        self.metrics = ['Time', 'Nodes', 'Fringe', 'Pushes', 'Pruned']
        self.metric_keys = ['time', 'visited', 'max_fringe', 'pushes', 'pruned']
        self.num_metrics = len(self.metrics)
        self.angles = [-math.pi / 2 + (2 * math.pi * i) / self.num_metrics for i in range(self.num_metrics)]
        self.data_snapshots = {}
        self.max_bounds = {k: 0.1 for k in self.metric_keys}

        # Tooltip hover state
        self.hovered_algo = None
        self.hover_start_time = 0
        self.HOVER_DELAY_MS = 500
        self.legend_hitboxes = []

    def update_data(self, results_dict):
        self.data_snapshots = results_dict
        # Reset max bounds
        self.max_bounds = {k: 0.1 for k in self.metric_keys} # Use 0.1 to prevent zero div
        
        # Calculate maximum for each metric across algorithms for normalization
        for algo, metrics in self.data_snapshots.items():
            if metrics is None or not isinstance(metrics, dict):
                continue
            for k in self.metric_keys:
                val = metrics.get(k, 0)
                if val == "FAIL": val = 0
                self.max_bounds[k] = max(self.max_bounds[k], float(val))
                
        # Ensure no max_bound is 0
        for k in self.metric_keys:
            if self.max_bounds[k] <= 0:
                self.max_bounds[k] = 1.0

    def _draw_tooltip(self, surface, algo, mouse_pos):
        """Draw a detailed metrics tooltip near the mouse cursor."""
        metrics = self.data_snapshots.get(algo)
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
        if not self.data_snapshots:
            return

        cx, cy = self.center

        def draw_pixel_star(surf, cx, cy, color):
            """Draws a small 5x5 pixel-art style star"""
            offsets = [(0,0), (0,-1), (0,1), (-1,0), (1,0), (0,-2), (0,2), (-2,0), (2,0), (-1,-1), (1,-1), (-1,1), (1,1)]
            for dx, dy in offsets:
                surf.set_at((cx + dx, cy + dy), color)

        # 1. Draw web backgrounds (wireframes)
        num_rings = 4
        for r in range(1, num_rings + 1):
            ratio = r / num_rings
            points = []
            for angle in self.angles:
                px = cx + self.radius * ratio * math.cos(angle)
                py = cy + self.radius * ratio * math.sin(angle)
                points.append((px, py))
            pygame.draw.polygon(surface, (140, 140, 140), points, 2)

        # 2. Draw spokes and labels
        for i, angle in enumerate(self.angles):
            px = cx + self.radius * math.cos(angle)
            py = cy + self.radius * math.sin(angle)
            pygame.draw.line(surface, (140, 140, 140), (cx, cy), (px, py), 2)

            # Labels
            label_text = self.metrics[i]
            # Offset labels outwards depending on length
            lx = cx + (self.radius + 35) * math.cos(angle)
            ly = cy + (self.radius + 35) * math.sin(angle)
            
            txt_surf = self.font.render(label_text, True, (200, 200, 200))
            rect = txt_surf.get_rect(center=(lx, ly))
            surface.blit(txt_surf, rect)

        # 3. Draw algorithm polygons
        # Create a transparent surface for overlapping blending
        surf_w = int(self.radius * 3)
        surf_h = int(self.radius * 3)
        poly_surface = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)
        poly_center = (surf_w // 2, surf_h // 2)
        for algo, metrics in self.data_snapshots.items():
            if metrics is None or not isinstance(metrics, dict):
                continue
            if visible_algos is not None and algo not in visible_algos:
                continue

            color = self.color_map.get(algo, (255, 255, 255))
            poly_points = []
            
            for i, k in enumerate(self.metric_keys):
                val = metrics.get(k, 0)
                if val == "FAIL": val = 0
                val = float(val)

                normalized = val / self.max_bounds[k]
                dist = self.radius * normalized
                px = poly_center[0] + dist * math.cos(self.angles[i])
                py = poly_center[1] + dist * math.sin(self.angles[i])
                poly_points.append((px, py))
            
            if len(poly_points) >= 3:
                # To ensure proper alpha blending in Pygame, draw each poly to its own surf
                algo_surf = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)
                
                # Translucency setup (Wireframe focus)
                fill_color = (*color, 30) # Very faint fill for footprint
                edge_color = (*color, 255) # Fully vibrant edge
                
                pygame.draw.polygon(algo_surf, fill_color, poly_points)
                pygame.draw.polygon(algo_surf, edge_color, poly_points, 3) # Thicker 3px edge
                
                # Blit to the collective poly surface
                poly_surface.blit(algo_surf, (0, 0))

        # --- LEGEND REFACTOR: Multi-line Centered Layout ---
        row1_keys = ['BFS', 'DFS', 'BestFS']
        row2_keys = ['Dijkstra', 'A*']
        
        # Helper to get active algos for a row
        get_active = lambda keys: [(k, self.data_snapshots[k]) for k in keys if k in self.data_snapshots and isinstance(self.data_snapshots[k], dict) and (visible_algos is None or k in visible_algos)]
        
        row1_algos = get_active(row1_keys)
        row2_algos = get_active(row2_keys)
        
        spacing = 160
        legend_start_y = cy + self.radius + 60

        mouse_pos = pygame.mouse.get_pos()
        current_hover = None
        self.legend_hitboxes = []  # Collect hitboxes for hover detection
        
        def draw_row(algos, start_y):
            row_width = (len(algos) - 1) * spacing + 100 # Approx width
            row_start_x = cx - row_width // 2
            for i, (algo, _) in enumerate(algos):
                color = self.color_map.get(algo, (255, 255, 255))
                lx = row_start_x + (i * spacing)
                ly = start_y
                pygame.draw.rect(surface, color, (lx, ly, 20, 20))
                
                if algo.lower() == "a*":
                    display_name = "A"
                    txt_surf = self.font.render(display_name, True, (255, 255, 255))
                    surface.blit(txt_surf, (lx + 30, ly))
                    # Draw star next to A (superscript)
                    draw_pixel_star(surface, lx + 30 + txt_surf.get_width() + 6, ly + 6, (255, 255, 255))
                    text_w = txt_surf.get_width() + 16  # Account for star
                else:
                    display_name = algo.upper()
                    txt_surf = self.font.render(display_name, True, (255, 255, 255))
                    surface.blit(txt_surf, (lx + 30, ly))
                    text_w = txt_surf.get_width()

                # Build hitbox covering color square + text
                hitbox = pygame.Rect(lx, ly, 30 + text_w, max(20, txt_surf.get_height()))
                self.legend_hitboxes.append((algo, hitbox))

        if row1_algos:
            draw_row(row1_algos, legend_start_y)
        if row2_algos:
            draw_row(row2_algos, legend_start_y + 40)

        # Blit the accumulated alpha surface back to the main surface
        top_left_x = cx - poly_center[0]
        top_left_y = cy - poly_center[1]
        surface.blit(poly_surface, (top_left_x, top_left_y))

    def draw_tooltip(self, surface):
        """Logic to detect hover and render the top-layer tooltip."""
        if not self.data_snapshots:
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
        
        # If hovering on something and enough time has passed, draw tooltip
        if self.hovered_algo is not None and (now - self.hover_start_time) >= self.HOVER_DELAY_MS:
            self._draw_tooltip(surface, self.hovered_algo, mouse_pos)
