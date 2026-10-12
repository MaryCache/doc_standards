import sys
from pathlib import Path

# scripts/ を import path に追加して check_* を直接 import できるようにする
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
