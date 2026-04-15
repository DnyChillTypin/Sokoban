# 📦 Sokoban AI Project

---

Sokoban AI Solver is a project that explores the efficiency of classic search algorithms in a constrained puzzle environment. The game is modeled as a state-space search problem, allowing algorithms like A\*, BFS, and DFS to solve levels automatically.

## 👥 Development Team

---

This project was developed by:

- **Nguyễn Thái Duy**
- **Đinh Quang Hưng**
- **Nguyễn Mạnh Tiến**

## 🎓 Supervision

---

- **Supervised by:** **TS.Nguyễn Quốc Tuấn**

### 📌 Credits

---

- **Original Sokoban Game by:** Hiroyuki Imbayashi.
- **Art & Sprites:** [iClaimThisName](https://iclaimthisname.itch.io/pixel-art-puzzle-pack)

## 🏗 Project Structure

---

```bash
SOKOBAN/
├─ assets/
├─ levels/
├─ menu.py
├─ main.py
├─ GameMenu.py
├─ selectLevels.py
├─ level.py
├─ player.py
├─ solver.py
├─ button.py
├─ particles.py
├─ settings.py
├─ theme.json
├─ env.json
├─ requirements.txt
├─ radar_chart.py
├─ README.md
├─ assests_list.txt
├─ run_game.sh
├─ ARCHITECTURE.md
```

## 🚀 Getting Started

---

### Prerequisites

---

Ensure you have Python installed on your system. We recommend using a virtual environment.

### Installation

---

Install the required dependencies using the **requirements.txt** file in the project:

```bash
    pip install -r requirements.txt
```

To run game Source code:

```bash
    py main.py
    python main.py
```

### 🎮 GamePlay & Control

---

**Control:**

- **Movement:** Use 'Arrow Keys' or 'WASD'.
- **Undo:** Use 'Ctrl + Z' to get back one step.
- **Restart:** Press 'R' to reset current level.
- **Navigation:** 'N' for Next Level, 'P' for Previous Level.
- **Menu:** Use 'Mouse Click' for UI interaction.
- **Exit:** Press 'ESC' to quit game.

**Rules:**

- The goal for Sokoban is to push all of the boxes onto the goals:
- Player cannot move through walls or boxes
- Only 1 box can be pushed at a time
- Puzzle is solved once every boxes are on the goals

### 🤖 AI Solver Features

---

The AI solver is implemented in **solver.py** and supports:

- **BFS (Breadth-First Search)** - guarantees a solution.
- **DFS (Depth-First Search)** - faster but not optimal.
- **A\*** - efficient with heuristic guidance.

- **Dijkstra** - ensures shortest path without heuristic.
- **Best-First Search** - fast heuristic-based exploration.

### 📸 Screenshots

---

### 🛠 To-Do List

---

- [ ] Implement **IDA** search algorithm.
- [ ] Implement **RBFS** (Recursive Best-First Search).
- [ ] Implement **MCTS** (Monte Carlo Tree Search).
