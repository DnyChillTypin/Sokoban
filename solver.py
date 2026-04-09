import collections
import heapq
import time
import pygame

class SokobanSolver:
    def __init__(self, level):
        self.level = level
        self.walls = set()
        self.targets = set()
        self.deadlocks = set() 
        self.dead_edges = set()
        self.exact_distances = {} # O(1) Precomputed heuristic map (per-target)
        self.nearest_distances = {} # O(1) min-distance to any target
        self.current_pruned = 0 
        self.floor_tiles = set()
        
        # 1. Parse the map
        for row in range(level.rows):
            for col in range(level.columns):
                val = level.grid[row][col]
                if val == '1': 
                    self.walls.add((col, row))
                elif val in ['3', '4']: 
                    self.targets.add((col, row))
                    self.floor_tiles.add((col, row))
                elif val == '0':
                    self.floor_tiles.add((col, row))

        # Freeze the wall set for faster lookup
        self.walls_frozen = frozenset(self.walls)
        self.targets_tuple = tuple(sorted(self.targets))
        self.num_targets = len(self.targets)

        # 2. Build the Advanced Deadlock Matrix (corners + dead edges)
        self._build_deadlock_matrix()
        
        # 3. Precompute Exact Wall-Aware Distances for perfect, pure A*
        self._precompute_exact_distances()

    def _build_deadlock_matrix(self):
        """
        Two-stage deadlock detection:
          Stage A: Dead Corners — a floor tile adjacent to two perpendicular walls
                   where no target exists.
          Stage B: Dead Edges  — a wall-run between two dead corners with no target
                   along the edge. Any box pushed onto this edge is permanently trapped.
        """
        corners = set()
        
        # Stage A: Basic Corners
        for r in range(self.level.rows):
            for c in range(self.level.columns):
                if (c, r) in self.walls or (c, r) in self.targets: continue
                if (c, r) not in self.floor_tiles: continue
                u = (c, r - 1) in self.walls
                d = (c, r + 1) in self.walls
                l = (c - 1, r) in self.walls
                r_w = (c + 1, r) in self.walls
                if (u or d) and (l or r_w):
                    self.deadlocks.add((c, r))
                    corners.add((c, r))

        # Stage B: Dead Edges — wall-runs between two dead corners
        # Scan horizontal edges
        for r in range(self.level.rows):
            for c in range(self.level.columns):
                if (c, r) not in corners:
                    continue
                # Scan rightward from this corner
                nc = c + 1
                edge_tiles = []
                has_target = False
                # Walk along until we hit a wall, go out of bounds, or find another corner
                while nc < self.level.columns and (nc, r) not in self.walls:
                    if (nc, r) in self.targets:
                        has_target = True
                        break
                    edge_tiles.append((nc, r))
                    if (nc, r) in corners:
                        break  # reached end corner
                    nc += 1
                
                # Valid dead edge: ends at another corner, no targets, and the entire
                # edge is backed by a continuous wall on one side (up or down)
                if edge_tiles and (nc, r) in corners and not has_target:
                    # Check wall backing: all tiles along this edge must have a wall
                    # on the same side (above or below)
                    wall_above = all((t[0], t[1] - 1) in self.walls for t in edge_tiles)
                    wall_below = all((t[0], t[1] + 1) in self.walls for t in edge_tiles)
                    if wall_above or wall_below:
                        for t in edge_tiles:
                            self.dead_edges.add(t)
                            self.deadlocks.add(t)
        
        # Scan vertical edges
        for c in range(self.level.columns):
            for r in range(self.level.rows):
                if (c, r) not in corners:
                    continue
                # Scan downward from this corner
                nr = r + 1
                edge_tiles = []
                has_target = False
                while nr < self.level.rows and (c, nr) not in self.walls:
                    if (c, nr) in self.targets:
                        has_target = True
                        break
                    edge_tiles.append((c, nr))
                    if (c, nr) in corners:
                        break
                    nr += 1
                
                if edge_tiles and (c, nr) in corners and not has_target:
                    wall_left = all((t[0] - 1, t[1]) in self.walls for t in edge_tiles)
                    wall_right = all((t[0] + 1, t[1]) in self.walls for t in edge_tiles)
                    if wall_left or wall_right:
                        for t in edge_tiles:
                            self.dead_edges.add(t)
                            self.deadlocks.add(t)

    def _precompute_exact_distances(self):
        """
        Per-target BFS: For each target, BFS outward to compute the true
        wall-aware walking distance from every reachable floor tile.
        Also builds the 'nearest_distances' map (min over all targets)
        used by the greedy/nearest heuristic.
        """
        self._per_target_dist = {}  # (target) -> {(x,y): dist}
        
        for target in self.targets:
            dist_map = {}
            queue = collections.deque()
            queue.append((target[0], target[1], 0))
            dist_map[target] = 0
            
            while queue:
                x, y, dist = queue.popleft()
                for dx, dy in ((0,1), (1,0), (0,-1), (-1,0)):
                    nx, ny = x + dx, y + dy
                    if (nx, ny) not in self.walls and (nx, ny) not in dist_map:
                        dist_map[(nx, ny)] = dist + 1
                        queue.append((nx, ny, dist + 1))
            
            self._per_target_dist[target] = dist_map
        
        # Build nearest-distance map (used by simple heuristic)
        all_positions = set()
        for dm in self._per_target_dist.values():
            all_positions.update(dm.keys())
        
        for pos in all_positions:
            min_dist = 999
            for target, dm in self._per_target_dist.items():
                d = dm.get(pos, 999)
                if d < min_dist:
                    min_dist = d
            self.nearest_distances[pos] = min_dist
            self.exact_distances[pos] = min_dist  # backward compat

    def heuristic(self, state):
        """
        Admissible heuristic: greedy assignment of boxes to targets using the
        minimum wall-aware distance. This is a simple sum-of-minimums which is
        admissible (never overestimates) and uses O(1) precomputed lookups.
        """
        _, _, boxes = state
        total = 0
        for bx, by in boxes:
            # O(1) Lookup: Perfectly accurate, pure, and incredibly fast
            total += self.nearest_distances.get((bx, by), 999) 
        return total

    def get_initial_state(self, player, level):
        # OPTIMIZATION: Sorted Tuples instead of frozensets
        boxes = tuple(sorted(tuple(box) for box in level.boxes))
        return (player.x, player.y, boxes)

    def is_goal_state(self, state):
        _, _, boxes = state
        return all(box in self.targets for box in boxes)

    def _is_freeze_deadlock(self, box_pos, boxes_set):
        """
        Detect simple freeze deadlocks: a box is frozen if it cannot move
        in either axis (both directions blocked by wall or another frozen box).
        This is checked iteratively for newly pushed boxes only.
        """
        bx, by = box_pos
        
        # Check horizontal freedom
        h_blocked = ((bx - 1, by) in self.walls or (bx - 1, by) in boxes_set) and \
                    ((bx + 1, by) in self.walls or (bx + 1, by) in boxes_set)
        
        # Check vertical freedom 
        v_blocked = ((bx, by - 1) in self.walls or (bx, by - 1) in boxes_set) and \
                    ((bx, by + 1) in self.walls or (bx, by + 1) in boxes_set)
        
        if h_blocked and v_blocked and box_pos not in self.targets:
            return True
        return False

    def get_valid_moves(self, state):
        px, py, boxes = state
        walls = self.walls
        deadlocks = self.deadlocks
        directions = (('U', 0, -1), ('D', 0, 1), ('L', -1, 0), ('R', 1, 0))
        
        for move_dir, dx, dy in directions:
            nx, ny = px + dx, py + dy
            
            if (nx, ny) in walls: 
                continue
                
            if (nx, ny) in boxes:
                bx, by = nx + dx, ny + dy
                
                if (bx, by) in walls or (bx, by) in boxes:
                    continue
                
                if (bx, by) in deadlocks:
                    self.current_pruned += 1
                    continue
                
                # OPTIMIZATION: Maintain sorted tuple
                new_boxes_list = []
                for b in boxes:
                    if b != (nx, ny):
                        new_boxes_list.append(b)
                new_boxes_list.append((bx, by))
                new_boxes = tuple(sorted(new_boxes_list))
                
                # Freeze deadlock check on the pushed box
                new_boxes_set = set(new_boxes)
                if self._is_freeze_deadlock((bx, by), new_boxes_set):
                    self.current_pruned += 1
                    continue
                
                yield move_dir, True, (nx, ny, new_boxes)
            else:
                yield move_dir, False, (nx, ny, boxes)

    def solve_bfs(self, initial_state):
        start_time = time.time()
        self.current_pruned = 0
        queue = collections.deque([(initial_state, [], 0)])
        visited = {initial_state}
        nodes_visited = 0; nodes_generated = 1; max_fringe = 1; iterations = 0
        
        while queue:
            iterations += 1
            if iterations % 5000 == 0: pygame.event.pump()
            if time.time() - start_time > 120.0: return self._fail_dict(start_time, nodes_visited, nodes_generated, max_fringe)

            max_fringe = max(max_fringe, len(queue))
            state, path, pushes = queue.popleft()
            nodes_visited += 1
            
            if self.is_goal_state(state): return self._success_dict(path, start_time, nodes_visited, nodes_generated, max_fringe, pushes)
                
            for move, is_push, next_state in self.get_valid_moves(state):
                if next_state not in visited:
                    visited.add(next_state)
                    nodes_generated += 1
                    queue.append((next_state, path + [move], pushes + (1 if is_push else 0)))
        return self._fail_dict(start_time, nodes_visited, nodes_generated, max_fringe)

    def solve_dfs(self, initial_state):
        start_time = time.time()
        self.current_pruned = 0
        stack = [(initial_state, [], 0)]
        visited = {initial_state}
        nodes_visited = 0; nodes_generated = 1; max_fringe = 1; iterations = 0
        
        while stack:
            iterations += 1
            if iterations % 5000 == 0: pygame.event.pump()
            if time.time() - start_time > 120.0: return self._fail_dict(start_time, nodes_visited, nodes_generated, max_fringe)

            max_fringe = max(max_fringe, len(stack))
            state, path, pushes = stack.pop()
            nodes_visited += 1
            
            if self.is_goal_state(state): return self._success_dict(path, start_time, nodes_visited, nodes_generated, max_fringe, pushes)
                
            for move, is_push, next_state in self.get_valid_moves(state):
                if next_state not in visited:
                    visited.add(next_state)
                    nodes_generated += 1
                    stack.append((next_state, path + [move], pushes + (1 if is_push else 0)))
        return self._fail_dict(start_time, nodes_visited, nodes_generated, max_fringe)

    def solve_astar(self, initial_state):
        start_time = time.time()
        count = 0; self.current_pruned = 0
        priority_queue = [(0, count, initial_state, [], 0)]
        visited = {initial_state}
        nodes_visited = 0; nodes_generated = 1; max_fringe = 1; iterations = 0
        
        while priority_queue:
            iterations += 1
            if iterations % 5000 == 0: pygame.event.pump()
            if time.time() - start_time > 120.0: return self._fail_dict(start_time, nodes_visited, nodes_generated, max_fringe)

            max_fringe = max(max_fringe, len(priority_queue))
            _, _, state, path, pushes = heapq.heappop(priority_queue)
            nodes_visited += 1
            
            if self.is_goal_state(state): return self._success_dict(path, start_time, nodes_visited, nodes_generated, max_fringe, pushes)
                
            for move, is_push, next_state in self.get_valid_moves(state):
                if next_state not in visited:
                    visited.add(next_state)
                    count += 1
                    nodes_generated += 1
                    # PURE A*: len(path) + perfect heuristic. No multipliers.
                    priority = len(path) + self.heuristic(next_state)
                    heapq.heappush(priority_queue, (priority, count, next_state, path + [move], pushes + (1 if is_push else 0)))
        return self._fail_dict(start_time, nodes_visited, nodes_generated, max_fringe)

    def solve_best_first(self, initial_state):
        start_time = time.time()
        count = 0; self.current_pruned = 0
        priority_queue = [(0, count, initial_state, [], 0)]
        visited = {initial_state}
        nodes_visited = 0; nodes_generated = 1; max_fringe = 1; iterations = 0
        
        while priority_queue:
            iterations += 1
            if iterations % 5000 == 0: pygame.event.pump()
            if time.time() - start_time > 120.0: return self._fail_dict(start_time, nodes_visited, nodes_generated, max_fringe)

            max_fringe = max(max_fringe, len(priority_queue))
            _, _, state, path, pushes = heapq.heappop(priority_queue)
            nodes_visited += 1
            
            if self.is_goal_state(state): return self._success_dict(path, start_time, nodes_visited, nodes_generated, max_fringe, pushes)
                
            for move, is_push, next_state in self.get_valid_moves(state):
                if next_state not in visited:
                    visited.add(next_state)
                    count += 1
                    nodes_generated += 1
                    priority = self.heuristic(next_state) 
                    heapq.heappush(priority_queue, (priority, count, next_state, path + [move], pushes + (1 if is_push else 0)))
        return self._fail_dict(start_time, nodes_visited, nodes_generated, max_fringe)

    def _fail_dict(self, start_time, visited, generated, fringe):
        return {'path': None, 'time': time.time() - start_time, 'visited': visited, 'generated': generated, 'max_fringe': fringe, 'pushes': 0, 'pruned': self.current_pruned}
        
    def _success_dict(self, path, start_time, visited, generated, fringe, pushes):
        return {'path': path, 'time': time.time() - start_time, 'visited': visited, 'generated': generated, 'max_fringe': fringe, 'pushes': pushes, 'pruned': self.current_pruned}