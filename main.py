import importlib.util
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
ROOT_MAIN = ROOT_DIR / "main.py"

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

spec = importlib.util.spec_from_file_location("mani_root_main", ROOT_MAIN)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
app = module.app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
