import collections
import heapq
import time
import pygame
import sys
import bisect
import numpy as np
from numba import njit

# ==========================================
# NUMBA JIT COMPILED HEURISTIC FUNCTIONS
# ==========================================
# We define these OUTSIDE the SokobanSolver class because Numba's @njit decorator 
# translates Python directly to LLVM/C machine code. It cannot understand Python 
# class instances (self) or dynamic memory structures like standard dictionaries.

@njit
def _solve_matching_rec(costs_matrix, box_idx, mask, dp_cache, target_count):
    """
    Recursive core of the Minimum Cost Perfect Matching algorithm.
    Compiled to raw C for maximum execution speed during node expansion.
    """
    # BASE CASE: All boxes have been successfully paired with a target.
    # The computational cost to match 0 remaining boxes is 0.
    if box_idx == len(costs_matrix):
        return 0
        
    # MEMOIZATION CHECK: O(1) cache lookup.
    # Numba arrays are C-contiguous in memory, making this 2D array lookup 
    # practically instantaneous compared to a Python dict hash collision.
    if dp_cache[box_idx, mask] != -1:
        return dp_cache[box_idx, mask]
        
    res = 999999  # Initialize with an arbitrarily high cost (infinity simulation)
    
    # Iterate through all available targets to find the optimal assignment
    for t_idx in range(target_count):
        # BITMASK CHECK: (1 << t_idx) creates a binary number with a 1 at the t_idx position.
        # The bitwise AND (&) checks if that specific target is already taken in our 'mask'.
        # If it equals 0, the target is free to be assigned.
        if not (mask & (1 << t_idx)):
            
            # Retrieve the precomputed true-distance from this box to this target
            cost = costs_matrix[box_idx, t_idx]
            
            # RECURSIVE STEP: 
            # 1. Move to the next box (box_idx + 1)
            # 2. Mark this target as 'taken' for the next branch using bitwise OR (|)
            m = cost + _solve_matching_rec(costs_matrix, box_idx + 1, mask | (1 << t_idx), dp_cache, target_count)
            
            # If this combination permutation yields a lower total cost, retain it
            if m < res: 
                res = m
                
    # Store the absolute optimal path cost for this specific bitmask configuration
    dp_cache[box_idx, mask] = res
    return res

@njit
def fast_solve_matching_wrapper(dist_matrix, boxes_array, target_count):
    """
    EXTREME PERFORMANCE WRAPPER:
    This function handles the heavy lifting of node expansion in machine code.
    
    Data Architecture:
    1. dist_matrix: A 3D NumPy array (num_targets, rows, cols) containing 
       precomputed BFS distances. Accessed via contiguous indexing.
    2. boxes_array: A 2D array (num_boxes, 2) containing integers of box locations.
    """
    num_boxes = len(boxes_array)
    
    # 1. DYNAMIC ALLOCATION: Allocate the cost-matrix directly in Numba/LLVM space.
    # Using np.zeros with int32 ensures we have a flat, contiguous memory block 
    # that matches the C-level performance requirements of the recursive matcher.
    costs = np.zeros((num_boxes, target_count), dtype=np.int32)
    
    # 2. VECTORIZED COST GENERATION: Build the box-to-target mapping.
    # We iterate over every box i and every target j.
    # By fetching directly from the 3D dist_matrix, we overhead of Python dictionary 
    # lookups and tuple object creation is completely eliminated.
    for i in range(num_boxes):
        bx, by = boxes_array[i, 0], boxes_array[i, 1]
        for j in range(target_count):
            # Fetch cost: dist_matrix[target_index, y_coord, x_coord]
            costs[i, j] = dist_matrix[j, by, bx]
            
    # 3. ALLOCATE DP CACHE: Creates a 2D array of dimensions [num_boxes] x [2^target_count].
    # Using a Power-of-2 bitmask (1 << target_count) allows for O(1) state lookup 
    # via bit-shifting, which is the most efficient way to track combinatorial subsets.
    dp_cache = np.full((num_boxes, 1 << target_count), -1, dtype=np.int32)
    
    # Start recursion at box 0 with an empty mask (0 means no targets taken)
    return _solve_matching_rec(costs, 0, 0, dp_cache, target_count)

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
        
        # 4. Initialize Heuristic Cache
        self.heuristic_cache = {}

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
        EXTREME PERFORMANCE PRECOMPUTATION:
        Builds a 3D NumPy array of 'True Distances' from every floor tile 
        to every target, using BFS Pull logic.
        
        Memory Layout:
        - Shape: (num_targets, rows, columns)
        - DType: np.int32 (Standard 4-byte integer for LLVM compatibility)
        - Default Value: 999999 (High value to prevent DP wrap-around while maintaining 
          valid comparison operations).
        """
        self.targets_list = list(self.targets)
        self.pullable_tiles = set()
        
        # Initialize 3D Distance Matrix in contiguous memory
        # Dimensions: [Target Index][Y Coordinate][X Coordinate]
        self.dist_matrix = np.full(
            (self.num_targets, self.level.rows, self.level.columns), 
            999999, 
            dtype=np.int32
        )
        
        for t_idx, target in enumerate(self.targets_list):
            queue = collections.deque([(target[0], target[1], 0)])
            # Seed the distance matrix at the target source
            self.dist_matrix[t_idx, target[1], target[0]] = 0
            
            while queue:
                x, y, dist = queue.popleft()
                self.pullable_tiles.add((x, y))
                
                for dx, dy in ((0,1), (1,0), (0,-1), (-1,0)):
                    nx, ny = x + dx, y + dy
                    px, py = x + 2*dx, y + 2*dy
                    
                    if (nx, ny) not in self.walls and (px, py) not in self.walls:
                        # Direct NumPy access instead of dict .get() / .set()
                        if self.dist_matrix[t_idx, ny, nx] == 999999:
                            self.dist_matrix[t_idx, ny, nx] = dist + 1
                            queue.append((nx, ny, dist + 1))
            
        # Optional: Build a 2D 'min-distance-to-any-target' map for simple heuristics
        self.nearest_distances = np.min(self.dist_matrix, axis=0)
            
    def _update_spinner(self, iterations, algo_name, line_offset=0):
        if iterations % 1000 == 0:
            chars = ['|', '/', '-', '\\']
            char = chars[(iterations // 1000) % 4]
            # ANSI escape codes: \033[A moves cursor UP, \033[B moves cursor DOWN
            # We move up by line_offset + 1 (to account for the current line we are on), 
            # then \r to start of line, update, then move back down.
            sys.stdout.write(f"\033[{line_offset + 1}A\r  Crunching {algo_name}... [{char}]\033[{line_offset + 1}B")
            sys.stdout.flush()
        return None

    def _clear_spinner(self):
        sys.stdout.write("\r" + " " * 50 + "\r")
        sys.stdout.flush()

    def heuristic(self, state):
        """
        Admissible heuristic: Minimum Cost Perfect Matching using bitmask DP.
        Delegates the heavy combinatorial math to the Numba-compiled C function.
        """
        _, _, boxes = state
        
        # 1. Convert boxes tuple to a typed NumPy array.
        # This conversion happens once per heuristic call, allowing the 
        # rest of the matching logic to execute at raw machine speeds.
        boxes_array = np.array(boxes, dtype=np.int32)
        
        # 2. Execute JIT-Compiled Math
        # We pass the precomputed 3D distance grid and the current box locations.
        # Numba handles the LLVM-translated execution of the matching recursion.
        total = fast_solve_matching_wrapper(self.dist_matrix, boxes_array, self.num_targets)
        
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
                
                if (bx, by) in deadlocks or (bx, by) not in self.pullable_tiles:
                    self.current_pruned += 1
                    continue
                
                # OPTIMIZATION: Maintain sorted tuple using bisect
                new_boxes_list = list(boxes)
                new_boxes_list.remove((nx, ny))
                bisect.insort(new_boxes_list, (bx, by))
                new_boxes = tuple(new_boxes_list)
                
                # Freeze deadlock check on the pushed box
                new_boxes_set = set(new_boxes)
                if self._is_freeze_deadlock((bx, by), new_boxes_set):
                    self.current_pruned += 1
                    continue
                
                yield move_dir, True, (nx, ny, new_boxes)
            else:
                yield move_dir, False, (nx, ny, boxes)

    def _reconstruct_path(self, state, came_from):
        path = []
        pushes = 0
        while state in came_from and came_from[state] is not None:
            state, move, is_push = came_from[state]
            path.append(move)
            if is_push:
                pushes += 1
        return path[::-1], pushes

    def solve_bfs(self, initial_state, chunk_size=500, line_offset=0):
        start_time = time.time()
        self.current_pruned = 0
        queue = collections.deque([initial_state])
        came_from = {initial_state: None}
        nodes_visited = 0; nodes_generated = 1; max_fringe = 1; iterations = 0
        
        while queue:
            iterations += 1
            if iterations % chunk_size == 0:
                self._update_spinner(iterations, "BFS", line_offset)
                yield ("RUNNING", None)

            if time.time() - start_time > 120.0: 
                self._clear_spinner()
                yield ("DONE", self._fail_dict(start_time, nodes_visited, nodes_generated, max_fringe))
                return

            max_fringe = max(max_fringe, len(queue))
            state = queue.popleft()
            nodes_visited += 1
            
            if self.is_goal_state(state): 
                self._clear_spinner()
                path, pushes = self._reconstruct_path(state, came_from)
                yield ("DONE", self._success_dict(path, start_time, nodes_visited, nodes_generated, max_fringe, pushes))
                return
                
            for move, is_push, next_state in self.get_valid_moves(state):
                if next_state not in came_from:
                    came_from[next_state] = (state, move, is_push)
                    nodes_generated += 1
                    queue.append(next_state)
        
        yield ("DONE", self._fail_dict(start_time, nodes_visited, nodes_generated, max_fringe))

    def solve_dfs(self, initial_state, chunk_size=500, line_offset=0):
        start_time = time.time()
        self.current_pruned = 0
        stack = [initial_state]
        came_from = {initial_state: None}
        nodes_visited = 0; nodes_generated = 1; max_fringe = 1; iterations = 0
        
        while stack:
            iterations += 1
            if iterations % chunk_size == 0:
                self._update_spinner(iterations, "DFS", line_offset)
                yield ("RUNNING", None)

            if time.time() - start_time > 120.0:
                self._clear_spinner()
                yield ("DONE", self._fail_dict(start_time, nodes_visited, nodes_generated, max_fringe))
                return

            max_fringe = max(max_fringe, len(stack))
            state = stack.pop()
            nodes_visited += 1
            
            if self.is_goal_state(state):
                self._clear_spinner()
                path, pushes = self._reconstruct_path(state, came_from)
                yield ("DONE", self._success_dict(path, start_time, nodes_visited, nodes_generated, max_fringe, pushes))
                return
                
            for move, is_push, next_state in self.get_valid_moves(state):
                if next_state not in came_from:
                    came_from[next_state] = (state, move, is_push)
                    nodes_generated += 1
                    stack.append(next_state)
        
        yield ("DONE", self._fail_dict(start_time, nodes_visited, nodes_generated, max_fringe))

    def solve_astar(self, initial_state, chunk_size=500, line_offset=0):
        start_time = time.time()
        count = 0; self.current_pruned = 0
        # PQ entry: (f_score, tiebreaker, state, g_score)
        priority_queue = [(self.heuristic(initial_state), count, initial_state, 0)]
        came_from = {initial_state: None}
        cost_so_far = {initial_state: 0}
        nodes_visited = 0; nodes_generated = 1; max_fringe = 1; iterations = 0
        
        while priority_queue:
            iterations += 1
            if iterations % chunk_size == 0:
                self._update_spinner(iterations, "A*", line_offset)
                yield ("RUNNING", None)

            if time.time() - start_time > 120.0:
                self._clear_spinner()
                yield ("DONE", self._fail_dict(start_time, nodes_visited, nodes_generated, max_fringe))
                return

            max_fringe = max(max_fringe, len(priority_queue))
            _, _, state, g = heapq.heappop(priority_queue)
            nodes_visited += 1
            
            if self.is_goal_state(state):
                self._clear_spinner()
                path, pushes = self._reconstruct_path(state, came_from)
                yield ("DONE", self._success_dict(path, start_time, nodes_visited, nodes_generated, max_fringe, pushes))
                return
                
            for move, is_push, next_state in self.get_valid_moves(state):
                new_cost = g + 1
                if next_state not in cost_so_far or new_cost < cost_so_far[next_state]:
                    cost_so_far[next_state] = new_cost
                    came_from[next_state] = (state, move, is_push)
                    count += 1
                    nodes_generated += 1
                    priority = new_cost + self.heuristic(next_state)
                    heapq.heappush(priority_queue, (priority, count, next_state, new_cost))
        
        yield ("DONE", self._fail_dict(start_time, nodes_visited, nodes_generated, max_fringe))

    def solve_fast_hint(self, initial_state, weight=5.0, timeout=2.0):
        """
        Hyper-fast Weighted A* exclusively for the hint system.
        Designed to return a result almost instantaneously by being greedy.
        """
        start_time = time.time()
        count = 0; self.current_pruned = 0
        
        # PQ entry: (f_score, tiebreaker, state, g_score)
        priority_queue = [(weight * self.heuristic(initial_state), count, initial_state, 0)]
        came_from = {initial_state: None}
        cost_so_far = {initial_state: 0}
        nodes_visited = 0; nodes_generated = 1; max_fringe = 1; iterations = 0
        
        while priority_queue:
            iterations += 1
            # Keep OS happy every 5000 iterations and check timeout
            if iterations % 5000 == 0:
                pygame.event.pump()
                if time.time() - start_time > timeout:
                    return self._fail_dict(start_time, nodes_visited, nodes_generated, max_fringe)

            max_fringe = max(max_fringe, len(priority_queue))
            _, _, state, g = heapq.heappop(priority_queue)
            nodes_visited += 1
            
            if self.is_goal_state(state):
                path, pushes = self._reconstruct_path(state, came_from)
                return self._success_dict(path, start_time, nodes_visited, nodes_generated, max_fringe, pushes)
                
            for move, is_push, next_state in self.get_valid_moves(state):
                new_cost = g + 1
                if next_state not in cost_so_far or new_cost < cost_so_far[next_state]:
                    cost_so_far[next_state] = new_cost
                    came_from[next_state] = (state, move, is_push)
                    count += 1
                    nodes_generated += 1
                    # Weighted A* priority: f = g + weight * h
                    priority = new_cost + (weight * self.heuristic(next_state))
                    heapq.heappush(priority_queue, (priority, count, next_state, new_cost))
                    
        return self._fail_dict(start_time, nodes_visited, nodes_generated, max_fringe)

    def solve_best_first(self, initial_state, chunk_size=500, line_offset=0):
        start_time = time.time()
        count = 0; self.current_pruned = 0
        priority_queue = [(self.heuristic(initial_state), count, initial_state)]
        came_from = {initial_state: None}
        nodes_visited = 0; nodes_generated = 1; max_fringe = 1; iterations = 0
        
        while priority_queue:
            iterations += 1
            if iterations % chunk_size == 0:
                self._update_spinner(iterations, "BestFS", line_offset)
                yield ("RUNNING", None)

            if time.time() - start_time > 120.0:
                self._clear_spinner()
                yield ("DONE", self._fail_dict(start_time, nodes_visited, nodes_generated, max_fringe))
                return

            max_fringe = max(max_fringe, len(priority_queue))
            _, _, state = heapq.heappop(priority_queue)
            nodes_visited += 1
            
            if self.is_goal_state(state):
                self._clear_spinner()
                path, pushes = self._reconstruct_path(state, came_from)
                yield ("DONE", self._success_dict(path, start_time, nodes_visited, nodes_generated, max_fringe, pushes))
                return
                
            for move, is_push, next_state in self.get_valid_moves(state):
                if next_state not in came_from:
                    came_from[next_state] = (state, move, is_push)
                    count += 1
                    nodes_generated += 1
                    priority = self.heuristic(next_state) 
                    heapq.heappush(priority_queue, (priority, count, next_state))
        
        yield ("DONE", self._fail_dict(start_time, nodes_visited, nodes_generated, max_fringe))

    def solve_dijkstra(self, initial_state, move_cost=1, push_cost=10, chunk_size=500, line_offset=0):
        start_time = time.time()
        count = 0; self.current_pruned = 0
        # PQ entry: (g_score, tiebreaker, state)
        priority_queue = [(0, count, initial_state)]
        came_from = {initial_state: None}
        cost_so_far = {initial_state: 0}
        nodes_visited = 0; nodes_generated = 1; max_fringe = 1; iterations = 0
        
        while priority_queue:
            iterations += 1
            if iterations % chunk_size == 0:
                self._update_spinner(iterations, "Dijkstra", line_offset)
                yield ("RUNNING", None)

            if time.time() - start_time > 120.0:
                self._clear_spinner()
                yield ("DONE", self._fail_dict(start_time, nodes_visited, nodes_generated, max_fringe))
                return

            max_fringe = max(max_fringe, len(priority_queue))
            g, _, state = heapq.heappop(priority_queue)
            nodes_visited += 1
            
            if g > cost_so_far.get(state, float('inf')):
                continue
            
            if self.is_goal_state(state):
                self._clear_spinner()
                path, pushes = self._reconstruct_path(state, came_from)
                yield ("DONE", self._success_dict(path, start_time, nodes_visited, nodes_generated, max_fringe, pushes))
                return
                
            for move, is_push, next_state in self.get_valid_moves(state):
                edge_cost = push_cost if is_push else move_cost
                new_g = g + edge_cost
                
                if next_state not in cost_so_far or new_g < cost_so_far[next_state]:
                    cost_so_far[next_state] = new_g
                    came_from[next_state] = (state, move, is_push)
                    count += 1
                    nodes_generated += 1
                    heapq.heappush(priority_queue, (new_g, count, next_state))
        
        yield ("DONE", self._fail_dict(start_time, nodes_visited, nodes_generated, max_fringe))

    def _fail_dict(self, start_time, visited, generated, fringe, aborted=False):
        return {'path': None, 'time': time.time() - start_time, 'visited': visited, 'generated': generated, 'max_fringe': fringe, 'pushes': 0, 'moves': 0, 'pruned': self.current_pruned, 'aborted': aborted}
        
    def _success_dict(self, path, start_time, visited, generated, fringe, pushes):
        return {'path': path, 'time': time.time() - start_time, 'visited': visited, 'generated': generated, 'max_fringe': fringe, 'pushes': pushes, 'moves': len(path), 'pruned': self.current_pruned}