<div align="center">

# Sokoban AI Engine

**A high-performance, JIT-compiled AI solver suite embedded inside a cooperative-multitasking Pygame engine.**

![Python Builder](https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Pygame CE](https://img.shields.io/badge/Pygame--CE-60_FPS-5C3EE8?style=for-the-badge&logo=python&logoColor=white)
![Numba JIT](https://img.shields.io/badge/Numba-LLVM_JIT-00A3E0?style=for-the-badge&logo=llvm&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-O(1)_Matrix-013243?style=for-the-badge&logo=numpy&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-success?style=for-the-badge)

<!-- PLACEHOLDER FOR GAMEPLAY GIF -->
<!-- ![Sokoban AI Gameplay](assets/graphics/gameplay_demo.gif) -->

</div>

---

## Table of Contents
1. [Key Features](#-key-features)
2. [Technical Architecture](#-technical-architecture)
3. [Installation & Setup](#-installation--setup)
4. [Controls & Gameplay](#-controls--gameplay)
5. [Credits & Acknowledgements](#-credits--acknowledgements)

---

## Key Features

This project reconstructs the classic Sokoban puzzle game from the ground up to serve as a high-fidelity AI testbed.

- **6-Algorithm Solver Suite**: Run A*, Breadth-First Search (BFS), Depth-First Search (DFS), Dijkstra, Best-First Search, and Weighted A* simultaneously.
- **Live Radar Chart Analytics**: A dynamically animating polar coordinate chart compares solver performance metrics (Time, Nodes Visited, Pushes, Max Memory, etc.) in real-time as results arrive.
- **Morden "Cyber-Glass" UI**: Built with Pygame_GUI, featuring glassmorphism elements, dynamic UI scaling, and responsive pixel-art layouts.
- **Dual-Language Localization**: Full English and Vietnamese support that hot-swaps interfaces dynamically at render-time.
- **Native Standalone Packaging**: Fully bundled via PyInstaller utilizing `sys._MEIPASS` and Git LFS for out-of-the-box Windows execution.

---

## Technical Architecture

The engine is engineered around three core principles to conquer the NP-hard Sokoban state-space without dropping a single frame:

### 1. Cooperative Multitasking (Python Generators)
Running heavy graph searches normally freezes UI threads. This engine solves that by wrapping solvers in Python's native `yield` generator protocol. Each algorithm acts as an independent state machine, processing precisely 500 node expansions per frame before yielding control back to the 60 FPS Pygame render loop. Multiple solvers can race cooperatively in a single thread without GIL contention.

### 2. JIT-Compiled Heuristics (Numba @njit)
At the heart of the informed searches (A*) is an Admissible Minimum Cost Perfect Matching heuristic. Because evaluating this `O(n · 2^n)` dynamic programming matrix is computationally brutal in pure Python, the math is compiled natively to LLVM/C machine code using Numba.

### 3. O(1) Matrix & Pruning System
Before searching begins, a wall-aware reverse BFS floods the grid, generating a 3D NumPy distance matrix. The Numba-compiled heuristics index this matrix in `O(1)` time. Furthermore, a two-tier deadlock detection system identifies dead corners statically and "frozen" boxes dynamically, aggressively pruning unreachable branches.

---

## Installation & Setup

Want to run the solvers yourself? We provide compiled binaries for immediate play, or you can build it directly from the Python source.

### Quick Start (Windows)
The easiest way to play the game without installing Python or dependencies.

1. Navigate to the **`dist/`** folder in this repository.
2. Download **`SokobanAI.exe`** (Note: Due to file sizes, this is hosted via Git LFS).
3. Run the executable. No installation required!

### Source Build Instructions
For developers who want to inspect the source code or run it on macOS/Linux.

**Prerequisites:**
- Python 3.10+ (Tested on 3.14)
- Git LFS (Required to pull the large asset files)

**1. Clone the repository**
```bash
git clone https://github.com/DnyChillTypin/Sokoban.git
cd Sokoban
```

**2. Create and activate a Virtual Environment**
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

**3. Install Dependencies**
```bash
pip install -r requirements.txt
```

**4. Run the Engine**
```bash
python main.py
```

---

## Controls & Gameplay

The game features dynamic input tracking and quality-of-life puzzle shortcuts.

| Action | Key / Input |
| :--- | :--- |
| **Movement** | `W`, `A`, `S`, `D` or `Arrow Keys` |
| **Restart Level** | `R` |
| **Undo Move** | `Z` |
| **Level Navigation** | `N` (Next) / `P` (Previous) *or* UI Arrows |
| **Quick Quit** | `Shift` + `Q` |
| **Menu / Back** | `ESC` |
| **Toggle AI Panel** | `TAB` |

*Note: All manual movement controls are automatically suppressed while asynchronous solvers compute to prevent state-space corruption.*

---

## 🤝 Credits & Acknowledgements

Created as an advanced data structures and AI testbed.

**Development Team:**
- [Nguyễn Thái Duy](https://github.com/DnyChillTypin)
- [Đinh Quang Hưng](https://github.com/hwngdominate05)
- [Nguyễn Mạnh Tiến](https://github.com/NguyenManhTien1505)

**Original Concept:**
- Sokoban was originally created by Hiroyuki Imabayashi in 1981.
