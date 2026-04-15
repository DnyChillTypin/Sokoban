# Sokoban AI — Technical Architecture Document

> **A high-performance, JIT-compiled AI solver suite embedded inside a cooperative-multitasking Pygame engine.**

---

## 1. Executive Summary

This project is a ground-up implementation of the classic **Sokoban** puzzle game, purpose-built as an AI testbed for comparing search algorithm performance on an NP-hard state-space. The engine ships with **six distinct pathfinding algorithms** that run simultaneously without freezing the UI, a **Numba-compiled heuristic** operating at C-level speeds, and a real-time **Radar Chart** visualization that live-animates each solver's performance metrics as results arrive.

The system is designed around three core engineering principles:

1. **Non-blocking computation** — Solvers run cooperatively inside the game loop via Python generators, preserving 60 FPS rendering at all times.
2. **Machine-code heuristics** — The admissible heuristic is compiled to native LLVM instructions via Numba's `@njit`, eliminating Python interpreter overhead during the millions of node expansions required by A\*.
3. **State-synchronized UI** — A "Clear-on-Dirty" architecture ensures that stale solver results are instantly invalidated the moment the player mutates the board state.

### Core Technology Stack

| Layer            | Technology      | Role                                                    |
| ---------------- | --------------- | ------------------------------------------------------- |
| **Runtime**      | Python 3.14     | Application logic and orchestration                     |
| **Rendering**    | Pygame-CE 2.5   | Hardware-accelerated 2D rendering at 60 FPS             |
| **UI Framework** | Pygame_GUI      | Themed button panels, dropdowns, and overlays           |
| **JIT Compiler** | Numba (`@njit`) | Translates heuristic math to LLVM/C machine code        |
| **Numerics**     | NumPy           | Contiguous-memory 3D distance matrices for O(1) lookups |

---

## 2. The AI Engine & Cooperative Multitasking

### 2.1 Algorithm Suite

The solver engine implements six algorithms, spanning uninformed search, informed search, and a purpose-built real-time variant:

| Algorithm             | Type               | Optimality           | Data Structure      | Priority Function                            |
| --------------------- | ------------------ | -------------------- | ------------------- | -------------------------------------------- |
| **BFS**               | Uninformed         | Move-optimal         | `collections.deque` | FIFO order                                   |
| **DFS**               | Uninformed         | Non-optimal          | `list` (stack)      | LIFO order                                   |
| **Best-First Search** | Informed, Greedy   | Non-optimal          | `heapq` min-heap    | `f = h(n)`                                   |
| **Dijkstra**          | Informed, Weighted | Cost-optimal         | `heapq` min-heap    | `f = g(n)` with edge costs (move=1, push=10) |
| **A\***               | Informed           | Optimal + Admissible | `heapq` min-heap    | `f = g(n) + h(n)`                            |
| **Weighted A\***      | Informed, Bounded  | ε-suboptimal         | `heapq` min-heap    | `f = g(n) + 5.0 · h(n)`                      |

**Weighted A\*** is exclusively reserved for the real-time **Hint** system. By inflating the heuristic weight to `5.0`, it trades solution optimality for speed, returning a viable next-push suggestion within a strict **2-second timeout**. During execution it calls `pygame.event.pump()` every 5,000 iterations to keep the OS from marking the process as unresponsive.

### 2.2 Cooperative Multitasking via Python Generators

Sokoban search spaces are enormous. A 9×8 level with 4 boxes can exceed **7 million generated nodes** under DFS (see §5). Running any solver to completion in a single frame would freeze the Pygame rendering pipeline for seconds or minutes.

The engine avoids this entirely through **cooperative multitasking** using Python's native generator protocol (`yield`).

#### Architecture

Each solver method is implemented as a **generator function** that yields control back to the game loop after processing a fixed chunk of work:

```python
def solve_bfs(self, initial_state, chunk_size=500, line_offset=0):
    # ...
    while queue:
        iterations += 1
        if iterations % chunk_size == 0:
            self._update_spinner(iterations, "BFS", line_offset)
            yield ("RUNNING", None)   # ← Cooperative yield point
        # ... expand one node ...
    yield ("DONE", result_dict)
```

**Key properties:**

- **Chunk Size**: Each solver processes exactly **500 node expansions per frame** before yielding. At 60 FPS, this translates to **30,000 expansions per second per algorithm**.
- **Simultaneous Execution**: Multiple generator instances are stored in `GameMenu.active_solvers: Dict[str, Generator]`. The `update()` method calls `next()` on each generator every frame, interleaving all five algorithms within a single thread.
- **Zero Thread Overhead**: No `threading`, `multiprocessing`, or GIL contention. Each solver is a simple state machine that suspends and resumes at well-defined yield points.

#### Data Flow

```
┌─────────────────────────────────────────────────────┐
│                    Game Loop (60 FPS)               │
│                                                     │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐         │
│  │  BFS     │   │  DFS     │   │  A*      │  ...    │
│  │ Generator│   │ Generator│   │ Generator│         │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘         │
│       │              │              │               │
│       ▼              ▼              ▼               │
│  next(gen) ──→  next(gen) ──→  next(gen)            │
│       │              │              │               │
│   "RUNNING"      "RUNNING"      "DONE" ──→ cache    │
│       │              │                              │
│       ▼              ▼                              │
│  ┌──────────────────────────────────────┐           │
│  │        Pygame Render Pipeline        │           │
│  │   draw() → display.update()          │           │
│  └──────────────────────────────────────┘           │
└─────────────────────────────────────────────────────┘
```

When a generator yields `("DONE", result_dict)`, the game loop caches the result in `execution_cache`, stops the spinner animation, re-enables the algorithm button, and queues the result for the Radar Chart's sequential animation pipeline.

---

## 3. Extreme Optimizations & Heuristics

### 3.1 Admissible Heuristic: Minimum Cost Perfect Matching

The heuristic function answers: _"What is the minimum total push-distance required to place every box on a unique target?"_ This is a combinatorial optimization problem — specifically, a **minimum-weight bipartite matching** — solved via **Bitmask Dynamic Programming**.

Given `n` boxes and `n` targets, the algorithm explores all `n!` permutations of box-to-target assignments, but collapses this exponential space into `O(n · 2^n)` unique subproblems using a bitmask to track which targets have been assigned.

#### State Representation

- `box_idx`: The current box being assigned (0 to n−1).
- `mask`: An integer bitmask where bit `j` is set if target `j` is already taken.
- `dp_cache[box_idx][mask]`: The minimum cost to optimally assign boxes `box_idx..n−1` given that the targets indicated by `mask` are unavailable.

#### Recurrence

```
dp[i][mask] = min over all free targets j of:
    cost_matrix[i][j] + dp[i+1][mask | (1 << j)]
```

#### Admissibility Proof

The heuristic is **admissible** (never overestimates) because:

1. Each distance `cost_matrix[i][j]` is the **true minimum push-distance** from box `i` to target `j`, computed via wall-aware reverse BFS.
2. The matching finds the **globally optimal** assignment across all boxes.
3. No real solution can achieve a lower total push-distance than this assignment.

### 3.2 Numba JIT Compilation

The matching algorithm is called once per **node expansion** in A\*. On a hard level, A\* may expand over 1,000,000 nodes, each requiring a full `O(n · 2^n)` DP traversal. In pure Python, this is catastrophically slow.

The solution: compile the entire heuristic pipeline to **LLVM IR → native x86 machine code** using Numba's `@njit` (no-Python-mode JIT):

```python
@njit
def _solve_matching_rec(costs_matrix, box_idx, mask, dp_cache, target_count):
    if box_idx == len(costs_matrix):
        return 0
    if dp_cache[box_idx, mask] != -1:
        return dp_cache[box_idx, mask]
    res = 999999
    for t_idx in range(target_count):
        if not (mask & (1 << t_idx)):           # Bitmask: is target free?
            cost = costs_matrix[box_idx, t_idx]
            m = cost + _solve_matching_rec(costs_matrix, box_idx + 1,
                                           mask | (1 << t_idx), dp_cache, target_count)
            if m < res:
                res = m
    dp_cache[box_idx, mask] = res
    return res
```

**Why `@njit` is necessary:**

| Concern       | Python Interpreter                    | Numba `@njit`                   |
| ------------- | ------------------------------------- | ------------------------------- |
| Loop dispatch | Bytecode interpretation per iteration | Native branch instructions      |
| Array access  | Object protocol + bounds checking     | Raw pointer arithmetic          |
| Recursion     | Frame allocation + reference counting | C-stack frames                  |
| Bitmask ops   | Integer object boxing/unboxing        | Register-level bit manipulation |

**Critical constraint:** `@njit` functions cannot access Python objects (`self`, `dict`, `list`). All data must be passed as **NumPy arrays with explicit dtypes**. This is why the distance data lives in a 3D `np.int32` array rather than a dictionary.

### 3.3 O(1) Distance Matrix via Reverse BFS

At level initialization, the solver precomputes a **3D NumPy distance matrix**:

```
dist_matrix: np.ndarray, shape=(num_targets, rows, columns), dtype=np.int32
```

For each target `t`, a **reverse BFS** (pull-search) floods outward from `t`, recording the minimum number of pushes required to move a box from any floor tile `(x, y)` to `t`. The BFS accounts for walls — a box can only be pushed from `(x, y)` to `(x+dx, y+dy)` if both the destination tile and the "puller" tile `(x+2·dx, y+2·dy)` are wall-free.

**Result**: During A\* execution, computing `cost_matrix[i][j]` for the matching heuristic is a single array index operation — `dist_matrix[j, by, bx]` — with **O(1) time complexity** and zero Python overhead when accessed inside `@njit` code.

A secondary 2D array `nearest_distances = np.min(dist_matrix, axis=0)` provides O(1) access to the shortest distance from any tile to its closest target, used by greedy heuristics.

### 3.4 Two-Tier Deadlock Detection

Deadlock detection is one of the most impactful pruning strategies in Sokoban solving. A deadlock is a board configuration from which no solution is reachable. Detecting and pruning these states early prevents the solver from exploring entire dead subtrees.

#### Tier 1: Static Detection (Preprocessing)

Computed once at level initialization and stored in `self.deadlocks: set`.

**Dead Corners**: A floor tile adjacent to two **perpendicular walls** (e.g., walls above and to the left) where no target exists. Any box pushed into such a corner is permanently trapped — it cannot be pushed in either axis.

```python
u = (c, r - 1) in self.walls    # Wall above
d = (c, r + 1) in self.walls    # Wall below
l = (c - 1, r) in self.walls    # Wall left
r_w = (c + 1, r) in self.walls  # Wall right
if (u or d) and (l or r_w):
    self.deadlocks.add((c, r))   # ← Dead corner
```

**Dead Edges**: A continuous wall-run between two dead corners with no target along the edge. If a box is pushed anywhere onto this edge, it will slide into a corner and become trapped. Detection scans horizontally and vertically, verifying that every tile along the run is backed by a continuous wall on one side.

#### Tier 2: Dynamic Detection (Runtime)

Evaluated **on every box push** during node expansion:

**Freeze Deadlocks**: A box is "frozen" if it cannot move in **either axis** — both directions along each axis are blocked by either a wall or another box. If a frozen box is not on a target, the state is irrecoverable.

```python
h_blocked = (left is wall/box) and (right is wall/box)
v_blocked = (up is wall/box)   and (down is wall/box)
if h_blocked and v_blocked and box not on target:
    return True  # ← Prune this state
```

Additionally, before any push, the engine checks whether the destination tile is in the **pullable tiles set** — tiles reachable by the reverse BFS. If a box would land on a tile from which no target is reachable by any sequence of pushes, the move is pruned immediately.

### 3.5 State Hashing with Sorted Tuples

Search algorithms require a `visited` set (or `came_from` dictionary) for duplicate detection. The key is the full game state: `(player_x, player_y, box_positions)`.

Box positions are canonicalized as **sorted tuples**:

```python
boxes = tuple(sorted(tuple(box) for box in level.boxes))
state = (player.x, player.y, boxes)
```

**Why sorted tuples?**

| Alternative    | Hash Time               | Memory                           | Equality Check          |
| -------------- | ----------------------- | -------------------------------- | ----------------------- |
| `frozenset`    | O(n)                    | High (set overhead + hash table) | O(n) worst case         |
| `sorted tuple` | O(1) amortized          | Minimal (flat C array)           | O(n) but cache-friendly |
| Unsorted tuple | Fails — `(A,B) ≠ (B,A)` | —                                | Invalid                 |

Sorted tuples guarantee **canonical ordering**, so two states with the same box positions always produce identical hash keys regardless of discovery order. When a box is pushed, the new sorted tuple is maintained efficiently using `bisect.insort()` — a O(n) insertion into an already-sorted list — rather than re-sorting from scratch.

---

## 4. UI/UX Architecture & State Synchronization

### 4.1 Radar Chart Visualization

The `RadarChart` class renders a live-animated **polar coordinate chart** comparing all solver metrics on six axes: Time, Nodes Visited, Moves, Pushes, Max Fringe (peak memory), and Pruned States.

#### Polar-to-Cartesian Mapping

Each metric `k` for algorithm `a` is normalized against a dynamic upper bound and projected onto a hexagonal web:

```python
angle_i = -π/2 + (2π · i) / 6       # Evenly spaced angles starting from 12 o'clock
normalized = value[a][k] / max_bound[k]
x = cx + radius · normalized · cos(angle_i)
y = cy + radius · normalized · sin(angle_i)
```

The resulting 6 vertices form a polygon drawn with per-algorithm neon coloring (30 alpha fill, 255 alpha outline).

#### Sequential LERP Animation

Results do not appear all at once. Each solver's polygon **expands from the center** over 500ms using **Linear Interpolation**:

```python
# In update(dt):
self.progress += dt * ANIMATION_SPEED   # ANIMATION_SPEED = 2.0 → 0.5s duration

# In draw():
scale = self.progress if algo == self.active_algo else 1.0
dist = radius * AXIS_BUFFER * min(normalized, scale)
```

The animation queue processes one algorithm at a time. As each solver finishes, its result is enqueued. When the active animation completes (`progress ≥ 1.0`), the next queued result begins animating. This creates a visually dramatic "reveal" sequence where each polygon layers onto the chart one at a time.

**Dynamic Normalization**: As new results arrive, the axis scales may change. The chart smoothly interpolates between old and new bounds:

```python
current_max[k] = old_max[k] + (new_max[k] - old_max[k]) * progress
```

This prevents sudden rescaling jumps and ensures that previously drawn polygons gracefully shrink or expand to accommodate the new data.

#### Interactive Tooltips

Hovering over a legend entry triggers a detailed metrics tooltip (with a 500ms delay to prevent flicker). Hovering over an axis label shows a short description of the metric. Both use screen-edge clamping to prevent overflow.

### 4.2 State-Aware Invalidation ("Clear-on-Dirty")

A critical data integrity problem arises when solver results are cached: if the player moves a box after solving, the cached paths and metrics become **stale** — they describe solutions to a board state that no longer exists.

The engine implements a **"Clear-on-Dirty"** pattern: three mutation points in `main.py` each call `self.menu.reset_ai_menu()` immediately after changing the board state:

| Mutation Event             | Location                  | Trigger                                               |
| -------------------------- | ------------------------- | ----------------------------------------------------- |
| Player movement / box push | `handle_movement_input()` | `if self.player.x != old_x or self.player.y != old_y` |
| Keyboard undo (`Z`)        | `event()`                 | `elif event.key == pygame.K_z`                        |
| UI undo button             | `event()`                 | `elif action == "UNDO_CLICKED"`                       |

`reset_ai_menu()` performs a complete cache wipe:

```python
def reset_ai_menu(self):
    self.execution_cache.clear()      # Purge all solver results
    self.active_solvers.clear()       # Kill running generators
    self.radar_chart.reset()          # Clear animation queue
    self.algo_results = {algo: None for algo in ALGORITHMS}
    # ... re-enable buttons, hide result labels ...
```

**Behavioral consequence**: Pressing "Solve" after the cache is cleared triggers a fresh solver run. Pressing "Solve" again _without_ moving triggers a **Radar Chart replay** — the cached results are re-queued into the animation pipeline without any computation:

```python
# In execute_solvers():
if all selected algos are in execution_cache:
    self.menu.radar_chart.trigger_replay(cached_algos)
    return   # ← No solvers launched
```

This creates the correct UX loop: **Solve → View Results → Move → Results Disappear → Solve Again**.

### 4.3 Movement Suppression During Computation

While solvers are active, manual movement is **suppressed** to prevent the player from mutating the board state mid-computation:

```python
def handle_movement_input(self, key):
    if self.menu.active_solvers:
        return False    # ← Guard clause
```

Without this guard, a player could push a box while A\* is mid-expansion, causing the solver to compute a path against a state that no longer matches the board — a subtle but critical data corruption bug.

### 4.4 Visual Feedback: Pixel-Art Loading Spinners

Each algorithm button features a custom **pixel-art rotating cross** spinner that activates during computation. The spinner uses a 4-frame rotation cycle rendered at 5x scale to match the game's pixel aesthetic:

```python
frame = (pygame.time.get_ticks() // 150) % 4   # 150ms per frame
# Renders a cross with one arm highlighted per frame
```

This provides immediate visual confirmation that computation is in progress, distinct from the algorithm being idle or selected.

---

## 5. Performance & Benchmarking

### 5.1 Terminal Execution Summary

Upon batch completion, the engine prints a formatted performance table to the terminal:

```
Algorithm    | Time (s)   | Visited    | Generated  | Max Mem    | Pruned   | Pushes   | Moves
-----------------------------------------------------------------------------------------------
BFS          | 28.9491    | 743031     | 785891     | 48565      | 134581   | 19       | 43
DFS          | 20.9425    | 539731     | 547302     | 7574       | 109315   | 1765     | 12903
BestFS       | 0.9242     | 135        | 208        | 74         | 15       | 19       | 47
Dijkstra     | 38.9681    | 1027040    | 1038429    | 22787      | 150555   | 19       | 43
A*           | 5.6440     | 151021     | 178913     | 28068      | 39933    | 19       | 43
-----------------------------------------------------------------------------------------------
```

**Column definitions:**

| Metric        | Description                                                                              |
| ------------- | ---------------------------------------------------------------------------------------- |
| **Time**      | Wall-clock solve time in seconds                                                         |
| **Visited**   | Nodes popped from the frontier and expanded                                              |
| **Generated** | Total successor states enqueued (including duplicates rejected later)                    |
| **Max Mem**   | Peak frontier size — the maximum number of states simultaneously held in the queue/stack |
| **Pruned**    | States rejected by deadlock detection before enqueuing                                   |
| **Pushes**    | Number of box-push moves in the solution path                                            |
| **Moves**     | Total moves (walks + pushes) in the solution path                                        |

Solvers that exceed the **120-second timeout** report `FAIL`. Manually aborted solvers (via `ESC`) report `ABORT`.

### 5.2 Comparative Analysis

The benchmarking data reveals the dramatic impact of informed search and heuristic quality:

**Search Tree Pruning**: On a representative 9×11 level, Best-First Search visits only **135 nodes** to find a 19-push solution, while BFS exhaustively expands **743,031** — a **5,504× reduction**. This demonstrates the power of the Minimum Cost Perfect Matching heuristic in guiding the search toward the goal.

**Optimality vs. Speed Trade-off**:

- **BFS** and **A\*** both find the optimal 19-push solution, but A\* does so after visiting only **151,021 nodes** compared to BFS's **743,031** — a 4.9× improvement from heuristic guidance.
- **Best-First Search** finds a slightly suboptimal solution (19 pushes, 47 moves vs. 43 moves for A\*) but does so **6× faster** than even A\*.
- **DFS** finds _a_ solution quickly but at **1,765 pushes** and **12,903 moves** — an extraordinarily suboptimal path, illustrating why depth-first search is unsuitable for optimization problems.

**Memory Characteristics**: BFS maintains a peak frontier of **48,565 states** (breadth-first expansion requires storing the entire wavefront), while DFS peaks at only **7,574** (depth-first naturally limits active branch width). A\* sits between them at **28,068**, trading memory for informed exploration.

---

## 6. Application Deployment & Localization

### 6.1 PyInstaller Standalone Packaging
To support distribution without requiring a local Python environment, the application is packaged into a native executable using PyInstaller.
- **Dependency Handling**: The `build.spec` is customized to correctly package `numba`, `llvmlite`, `numpy`, and `pygame_gui`.
- **Resource Pathing**: The application natively handles `sys._MEIPASS` directory shifting during the boot sequence. When the executable extracts itself to a temporary directory, `main.py` redirects its CWD, allowing Pygame to cleanly load assets without hardcoded paths.
- **Save Persistence**: The `env.json` configuration config uses `sys.executable` logic to persist alongside the `.exe` file itself, preventing data loss when the temporary PyInstaller `_MEIPASS` folder is destroyed.
- **Binary Distribution**: To circumvent GitHub's 100MB commit limit for the 130MB standalone distributions, the project utilizes **Git LFS** (Large File Storage).

### 6.2 Dual-Language Localization
Sokoban AI natively supports English and Vietnamese text parsing.
- **Dynamic Text Resolution**: UI bindings, settings toggles (e.g., Music, SFX), main menu navigation, and Radar Chart tooltips fetch localized strings dynamically at render-time using `translations.py`.
- **Instant Synchronization**: Modifying the language setting triggers an immediate UI rebuild without requiring a reboot. The selection persists across sessions.

---

## 7. Module Reference

| Module            | Lines | Responsibility                                                                   |
| ----------------- | ----- | -------------------------------------------------------------------------------- |
| `solver.py`       | 615   | Search algorithms, heuristic engine, deadlock detection, distance precomputation |
| `main.py`         | ~720  | Game loop, state management, cooperative scheduling, tutorial animations         |
| `GameMenu.py`     | ~450  | UI panel, button management, execution cache, terminal reporting                 |
| `radar_chart.py`  | ~360  | Polar chart rendering, LERP animation queue, translated tooltip system           |
| `menu.py`         | ~330  | Multi-column main menu, resolution settings UI, state machine management         |
| `selectLevels.py` | ~215  | Level browser with dynamic preview rendering, pagination, and navigation         |
| `level.py`        | ~185  | Level file parser, tile grid, environmental generation (flora), collision data   |
| `translations.py` | ~80   | Key-value dictionary registry for language string substitution                   |
| `config_utils.py` | ~22   | Persistent variables saving/loading, executable directory tracking               |
| `particles.py`    | 80    | Physics-based confetti burst system with gravity and air friction                |
| `button.py`       | 48    | Custom pixel-art spinner widget for loading states                               |
| `settings.py`     | ~65   | Global constants, UI asset textures mapping, core algorithm registry             |

---

_Architecture Document — Sokoban AI Engine_
_Authored for portfolio review by senior engineers and technical recruiters._
