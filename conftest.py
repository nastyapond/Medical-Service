"""Root conftest.py to ensure app module is in Python path"""
import sys
from pathlib import Path

# Add the workspace root to Python path so pytest can find the app module
workspace_root = Path(__file__).parent
if str(workspace_root) not in sys.path:
    sys.path.insert(0, str(workspace_root))
