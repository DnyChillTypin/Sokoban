echo "========================================"
echo "      Starting Sokoban AI Setup...      "
echo "========================================"

if ! command -v python3 &> /dev/null
then
    echo "Error: Python3 is not installed. Please install Python3 to run this game."
    exit 1
fi

if [ ! -d "venv" ]; then
    echo ">>> Creating a localized Python environment..."
    python3 -m venv venv
fi

echo ">>> Activating environment..."
source venv/bin/activate

echo ">>> Installing dependencies (pygame, pygame_gui)..."
pip install --quiet pygame pygame_gui

echo ">>> Launching Sokoban AI..."
python3 main.py

deactivate
echo ">>> Thanks for playing!"