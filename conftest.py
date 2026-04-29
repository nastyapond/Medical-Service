
import sys
from pathlib import Path

workspace_root = Path(__file__).parent
if str(workspace_root) not in sys.path:
    sys.path.insert(0, str(workspace_root))
