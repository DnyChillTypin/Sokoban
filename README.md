# 📦 Sokoban AI Project

## 👥 Development Team

---

This project was delveloped by:

- **Nguyễn Thái Duy**
- **Đinh Quang Hưng**
- **Nguyễn Mạnh Tiến**

### Credits

---

- **Original Sokoban Game by:** Hiroyuki Imbayashi.
- **Art & Sprites:** [iClaimThisName](https://iclaimthisname.itch.io/pixel-art-puzzle-pack)

## 🏗 Project Structure

---

```bash
SOKOBAN/
├─ assets/               # Chứa hình ảnh, âm thanh, font chữ
├─ levels/               # Các file cấu hình màn chơi (.txt/.json)
├─ models/               # (Nếu có) Các logic xử lý dữ liệu
├─ main.py               # Điểm khởi chạy chính của trò chơi
├─ GameMenu.py           # Quản lý giao diện menu chính
├─ level.py              # Xử lý logic tải và hiển thị màn chơi
├─ player.py             # Điều khiển và hành động của nhân vật
├─ solver.py             # Chứa các thuật toán AI (BFS, DFS, A*,...)
├─ button.py             # Thành phần giao diện (UI Components)
├─ particles.py          # Hiệu ứng hình ảnh trong game
├─ settings.py           # Các hằng số và cấu hình hệ thống
├─ theme.json            # Cấu hình màu sắc/giao diện
├─ requirements.txt      # Danh sách thư viện cần thiết
```

## 🚀 Getting Started

---

### Prerequisites

---

Ensure you have Python installed on your system. We recommend using a virtual environment.

### Installation

---

Install the required dependencies using the requirement.txt file in the project:

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

- **Movement:** Use 'Arrow Keys' or 'WASD'.
- **Restart:** Press 'R' to reset current level.
- **Navigation:** 'N' for Next Level, 'P' for Previous Level.
- **Menu:** Use 'Mouse Click' for UI interaction.
- **Exit:** Press 'ESC' to quit game.

**Rules:**

- The goal for Sokoban is to push all of the boxes onto the goals:
- Player cannot move through walls or boxes
- Only 1 box can be push at a time
- Puzzle is solved once every boxes are on the goals

### 🤖 AI Solver Features

---

The project includes a dedicated autonomous solving engine located in solver.py, designed to compute the most efficient paths for complex puzzles.
**Implemented Algorithms:**

- [x] A Search:Utilizes optimized heuristics to find the shortest path.

* **[x] BFS (Breadth-First Search)**: Guarantees the optimal solution for moves.
* [x] DPS

### 📸 Screenshots

---

### 🛠 To-Do List

---

- [ ] Implenment **IDA** search algorithm.
- [ ] Implenment **RBFS** (Recursive Best-First Search).
- [ ] Implenment **MCTS** (Monte Carlo Tree Search).
