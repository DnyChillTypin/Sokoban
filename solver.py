import collections
import heapq
import time

class SokobanSolver:
    def __init__(self, level):
        self.walls = set()
        self.targets = set()
        self.deadlocks = set() 
        self.current_pruned = 0 # Tracks deadlocks avoided
        
        for row in range(level.rows):
            for col in range(level.columns):
                val = level.grid[row][col]
                if val == '1': 
                    self.walls.add((col, row))
                elif val in ['3', '4']: 
                    self.targets.add((col, row))

        for row in range(level.rows):
            for col in range(level.columns):
                if (col, row) in self.walls or (col, row) in self.targets:
                    continue
                
                up_wall = (col, row - 1) in self.walls
                down_wall = (col, row + 1) in self.walls
                left_wall = (col - 1, row) in self.walls
                right_wall = (col + 1, row) in self.walls
                
                if (up_wall or down_wall) and (left_wall or right_wall):
                    self.deadlocks.add((col, row))

    def get_initial_state(self, player, level):
        boxes = frozenset(tuple(box) for box in level.boxes)
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
                
            if (nx, ny) in boxes:
                bx, by = nx + dx, ny + dy
                
                # Normal rules (can't push into walls or boxes)
                if (bx, by) in self.walls or (bx, by) in boxes:
                    continue
                
                # Track when the Deadlock Scanner saves us! ---
                if (bx, by) in self.deadlocks:
                    self.current_pruned += 1
                    continue
                
                new_boxes = set(boxes)
                new_boxes.remove((nx, ny))
                new_boxes.add((bx, by))
                # Yields True for "is_push"
                yield move_dir, True, (nx, ny, frozenset(new_boxes))
            else:
                # Yields False for "is_push"
                yield move_dir, False, (nx, ny, boxes)

    def heuristic(self, state):
        _, _, boxes = state
        total = 0
        for bx, by in boxes:
            min_dist = min(abs(bx - tx) + abs(by - ty) for tx, ty in self.targets)
            total += min_dist
        return total

    def solve_bfs(self, initial_state):
        start_time = time.time()
        self.current_pruned = 0
        # Queue now holds: (state, path, pushes)
        queue = collections.deque([(initial_state, [], 0)])
        visited = set([initial_state])
        nodes_visited = 0
        nodes_generated = 1 
        max_fringe = 1
        
        while queue:
            max_fringe = max(max_fringe, len(queue))
            state, path, pushes = queue.popleft()
            nodes_visited += 1
            
            if self.is_goal_state(state): 
                return {'path': path, 'time': time.time() - start_time, 'visited': nodes_visited, 'generated': nodes_generated, 'max_fringe': max_fringe, 'pushes': pushes, 'pruned': self.current_pruned}
                
            for move, is_push, next_state in self.get_valid_moves(state):
                if next_state not in visited:
                    visited.add(next_state)
                    nodes_generated += 1
                    queue.append((next_state, path + [move], pushes + (1 if is_push else 0)))
                    
        return {'path': None, 'time': time.time() - start_time, 'visited': nodes_visited, 'generated': nodes_generated, 'max_fringe': max_fringe, 'pushes': 0, 'pruned': self.current_pruned}

    def solve_dfs(self, initial_state):
        start_time = time.time()
        self.current_pruned = 0
        stack = [(initial_state, [], 0)]
        visited = set([initial_state])
        nodes_visited = 0
        nodes_generated = 1
        max_fringe = 1
        
        while stack:
            max_fringe = max(max_fringe, len(stack))
            state, path, pushes = stack.pop()
            nodes_visited += 1
            
            if self.is_goal_state(state): 
                return {'path': path, 'time': time.time() - start_time, 'visited': nodes_visited, 'generated': nodes_generated, 'max_fringe': max_fringe, 'pushes': pushes, 'pruned': self.current_pruned}
                
            for move, is_push, next_state in self.get_valid_moves(state):
                if next_state not in visited:
                    visited.add(next_state)
                    nodes_generated += 1
                    stack.append((next_state, path + [move], pushes + (1 if is_push else 0)))
                    
        return {'path': None, 'time': time.time() - start_time, 'visited': nodes_visited, 'generated': nodes_generated, 'max_fringe': max_fringe, 'pushes': 0, 'pruned': self.current_pruned}

    def solve_astar(self, initial_state):
        start_time = time.time()
        count = 0 
        self.current_pruned = 0
        priority_queue = [(0, count, initial_state, [], 0)]
        visited = set([initial_state])
        nodes_visited = 0
        nodes_generated = 1
        max_fringe = 1
        
        while priority_queue:
            max_fringe = max(max_fringe, len(priority_queue))
            cost, _, state, path, pushes = heapq.heappop(priority_queue)
            nodes_visited += 1
            
            if self.is_goal_state(state): 
                return {'path': path, 'time': time.time() - start_time, 'visited': nodes_visited, 'generated': nodes_generated, 'max_fringe': max_fringe, 'pushes': pushes, 'pruned': self.current_pruned}
                
            for move, is_push, next_state in self.get_valid_moves(state):
                if next_state not in visited:
                    visited.add(next_state)
                    count += 1
                    nodes_generated += 1
                    priority = len(path) + 1 + self.heuristic(next_state)
                    heapq.heappush(priority_queue, (priority, count, next_state, path + [move], pushes + (1 if is_push else 0)))
                    
        return {'path': None, 'time': time.time() - start_time, 'visited': nodes_visited, 'generated': nodes_generated, 'max_fringe': max_fringe, 'pushes': 0, 'pruned': self.current_pruned}

    def solve_best_first(self, initial_state):
        start_time = time.time()
        count = 0 
        self.current_pruned = 0
        priority_queue = [(0, count, initial_state, [], 0)]
        visited = set([initial_state])
        nodes_visited = 0
        nodes_generated = 1
        max_fringe = 1
        
        while priority_queue:
            max_fringe = max(max_fringe, len(priority_queue))
            _, _, state, path, pushes = heapq.heappop(priority_queue)
            nodes_visited += 1
            
            if self.is_goal_state(state): 
                return {'path': path, 'time': time.time() - start_time, 'visited': nodes_visited, 'generated': nodes_generated, 'max_fringe': max_fringe, 'pushes': pushes, 'pruned': self.current_pruned}
                
            for move, is_push, next_state in self.get_valid_moves(state):
                if next_state not in visited:
                    visited.add(next_state)
                    count += 1
                    nodes_generated += 1
                    priority = self.heuristic(next_state) 
                    heapq.heappush(priority_queue, (priority, count, next_state, path + [move], pushes + (1 if is_push else 0)))
                    
        return {'path': None, 'time': time.time() - start_time, 'visited': nodes_visited, 'generated': nodes_generated, 'max_fringe': max_fringe, 'pushes': 0, 'pruned': self.current_pruned}