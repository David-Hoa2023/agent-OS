"""Example CLI runner."""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from codex_prime.cli import main

if __name__ == "__main__":
    sys.exit(main())
