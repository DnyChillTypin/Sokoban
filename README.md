# 📦 Sokoban AI Project

## 👥 Development Team

This project was delveloped by:

- **Nguyễn Thái Duy**
- **Đinh Quang Hưng**
- **Nguyễn Mạnh Tiến**

### Credits

- **Original Sokoban Game by:** Hiroyuki Imbayashi.
- **Art & Sprites:** [iClaimThisName](https://iclaimthisname.itch.io/pixel-art-puzzle-pack)

---

## Getting Started

### Prerequisites

Ensure you have Python installed on your system. We recommend using a virtual environment.

### Installation

Install the required dependencies using the requirement.txt file in the project:

```bash
    pip install -r requirements.txt
```

To run game Source code:

```bash
    py main.py
    python main.py
```

### GamePlay & Control

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

---

### 📸 Screenshots

---

### 🛠 To-Do List

- [ ] Implenment **IDA** search algorithm.
- [ ] Implenment **RBFS** (Recursive Best-First Search).
- [ ] Implenment **MCTS** (Monte Carlo Tree Search).
