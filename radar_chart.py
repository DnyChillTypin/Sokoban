import pygame
import math
from settings import font_path

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

    def draw(self, surface):
        if not self.data_snapshots:
            return

        cx, cy = self.center

        # 1. Draw web backgrounds (wireframes)
        num_rings = 4
        for r in range(1, num_rings + 1):
            ratio = r / num_rings
            points = []
            for angle in self.angles:
                px = cx + self.radius * ratio * math.cos(angle)
                py = cy + self.radius * ratio * math.sin(angle)
                points.append((px, py))
            pygame.draw.polygon(surface, (100, 100, 100), points, 2)

        # 2. Draw spokes and labels
        for i, angle in enumerate(self.angles):
            px = cx + self.radius * math.cos(angle)
            py = cy + self.radius * math.sin(angle)
            pygame.draw.line(surface, (100, 100, 100), (cx, cy), (px, py), 2)

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

        legend_start_y = cy + self.radius + 60
        # Count valid algos for centering legend
        valid_algos = [a for a, m in self.data_snapshots.items() if m is not None and isinstance(m, dict)]
        legend_start_x = cx - (len(valid_algos) * 100) // 2
        legend_idx = 0

        for algo, metrics in self.data_snapshots.items():
            if metrics is None or not isinstance(metrics, dict):
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
                
                # Translucency setup
                fill_color = (*color, 120) # (R, G, B, A) - increased opacity
                edge_color = (*color, 255)
                
                pygame.draw.polygon(algo_surf, fill_color, poly_points)
                pygame.draw.polygon(algo_surf, edge_color, poly_points, 2)
                
                # Blit to the collective poly surface
                poly_surface.blit(algo_surf, (0, 0))

            # Draw legend entry directly on main surface
            lx = legend_start_x + (legend_idx * 100)
            ly = legend_start_y
            pygame.draw.rect(surface, color, (lx, ly, 20, 20))
            
            txt_surf = self.font.render(algo, True, (255, 255, 255))
            surface.blit(txt_surf, (lx + 30, ly))
            
            legend_idx += 1

        # Blit the accumulated alpha surface back to the main surface
        top_left_x = cx - poly_center[0]
        top_left_y = cy - poly_center[1]
        surface.blit(poly_surface, (top_left_x, top_left_y))
