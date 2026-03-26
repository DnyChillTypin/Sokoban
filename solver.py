import collections
import heapq

class SokobanSolver:
    def __init__(self, level):
        self.walls = set()
        self.targets = set()
        self.deadlocks = set() # --- NEW: Memory for deadly corners ---
        
        for row in range(level.rows):
            for col in range(level.columns):
                val = level.grid[row][col]
                if val == '1': 
                    self.walls.add((col, row))
                elif val in ['3', '4']: 
                    self.targets.add((col, row))

        # --- OPTIMIZATION: Identify all non-target corners! ---
        for row in range(level.rows):
            for col in range(level.columns):
                # We don't care about walls or targets
                if (col, row) in self.walls or (col, row) in self.targets:
                    continue
                
                # Check for walls blocking the horizontal and vertical axes
                up_wall = (col, row - 1) in self.walls
                down_wall = (col, row + 1) in self.walls
                left_wall = (col - 1, row) in self.walls
                right_wall = (col + 1, row) in self.walls
                
                # If it is blocked vertically AND horizontally, it's a corner deadlock.
                if (up_wall or down_wall) and (left_wall or right_wall):
                    self.deadlocks.add((col, row))

    def get_initial_state(self, player, level):
        boxes = tuple(sorted([tuple(box) for box in level.boxes]))
        return (player.x, player.y, boxes)

    def is_goal_state(self, state):
        _, _, boxes = state
        return all(box in self.targets for box in boxes)

    def get_valid_moves(self, state):
        px, py, boxes = state
        directions = {'U': (0, -1), 'D': (0, 1), 'L': (-1, 0), 'R': (1, 0)}
        
        for move_dir, (dx, dy) in directions.items():
            nx, ny = px + dx, py + dy
            
            if (nx, ny) in self.walls: 
                continue
                
            new_boxes = list(boxes)
            if (nx, ny) in boxes:
                bx, by = nx + dx, ny + dy
                
                # --- OPTIMIZATION: Skip this move entirely if it pushes a box into a deadlock! ---
                if (bx, by) in self.walls or (bx, by) in boxes or (bx, by) in self.deadlocks:
                    continue
                    
                new_boxes.remove((nx, ny))
                new_boxes.append((bx, by))
                
            yield move_dir, (nx, ny, tuple(sorted(new_boxes)))

    def solve_bfs(self, initial_state):
        queue = collections.deque([(initial_state, [])])
        visited = set([initial_state])
        
        while queue:
            state, path = queue.popleft()
            if self.is_goal_state(state): return path
                
            for move, next_state in self.get_valid_moves(state):
                if next_state not in visited:
                    visited.add(next_state)
                    queue.append((next_state, path + [move]))
        return None

    def solve_dfs(self, initial_state):
        stack = [(initial_state, [])]
        visited = set([initial_state])
        
        while stack:
            state, path = stack.pop()
            if self.is_goal_state(state): return path
                
            for move, next_state in self.get_valid_moves(state):
                if next_state not in visited:
                    visited.add(next_state)
                    stack.append((next_state, path + [move]))
        return None

    def heuristic(self, state):
        _, _, boxes = state
        total = 0
        for bx, by in boxes:
            min_dist = min(abs(bx - tx) + abs(by - ty) for tx, ty in self.targets)
            total += min_dist
        return total

    def solve_astar(self, initial_state):
        count = 0 
        priority_queue = [(0, count, initial_state, [])]
        visited = set([initial_state])
        
        while priority_queue:
            cost, _, state, path = heapq.heappop(priority_queue)
            
            if self.is_goal_state(state): return path
                
            for move, next_state in self.get_valid_moves(state):
                if next_state not in visited:
                    visited.add(next_state)
                    count += 1
                    priority = len(path) + 1 + self.heuristic(next_state)
                    heapq.heappush(priority_queue, (priority, count, next_state, path + [move]))
        return None