echo "========================================"
echo "      Starting Sokoban AI Setup...      "
echo "========================================"

# Check if Python3 is installed
if ! command -v python3 &> /dev/null
then
    echo "Error: Python3 is not installed. Please install Python3 to run this game."
    exit 1
fi

# Create virtual environment if it doesn't already exist
if [ ! -d "venv" ]; then
    echo ">>> Creating a localized Python environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo ">>> Activating environment..."
source venv/bin/activate

# Install required libraries
echo ">>> Installing dependencies (pygame, pygame_gui)..."
pip install --quiet pygame pygame_gui

# Launch game
echo ">>> Launching Sokoban AI..."
python3 main.py

# Deactivating environment when the game window is closed
deactivate
echo ">>> Thanks for playing!"