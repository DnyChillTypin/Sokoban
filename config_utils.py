import json
import os

import sys

def get_exe_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(get_exe_dir(), 'env.json')

def load_settings():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {CONFIG_FILE}: {e}")
    return {"music": "Off", "sound": "On", "resolution": "1600x900", "mode": "Windowed", "language": "en"}

def save_settings(settings):
    try:
        # Load existing first to merge, or just overwrite since we track everything
        with open(CONFIG_FILE, 'w') as f:
            json.dump(settings, f)
    except Exception as e:
        print(f"Error saving {CONFIG_FILE}: {e}")
