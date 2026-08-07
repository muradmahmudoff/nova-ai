"""Nova AI backend server-ini işə salır. İstifadə: python scripts/run_server.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import uvicorn
from config.settings import settings

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.server_host, port=settings.server_port, reload=False)
