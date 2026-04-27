#!/usr/bin/env python
import os
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent

data_path = Path(root / 'datasets' / 'dataset.csv')
data_path = Path(os.getenv('DATA_PATH', str(data_path)))
result = subprocess.run([sys.executable, str(root / 'ml_service' / 'train_rubert.py'), '--data-path', str(data_path)])
sys.exit(result.returncode)
