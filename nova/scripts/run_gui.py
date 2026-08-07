"""Nova AI GUI tətbiqini işə salır. İstifadə: python scripts/run_gui.py
Qeyd: Backend server ayrıca işə salınmalıdır (scripts/run_server.py).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.gui.main_window import main

if __name__ == "__main__":
    main()
