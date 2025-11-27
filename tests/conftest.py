"""Pytest configuration and fixtures."""

import sys
from pathlib import Path

# Add src directory to Python path so 'app' module can be imported
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))
