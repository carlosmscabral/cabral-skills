"""Pytest configuration for the preso engine test suite.

Pytest loads this file before it imports `preso` or a test module.
The file stops bytecode writes, because `scripts/validate_repo.py` rejects
`__pycache__` in the repository tree.
"""

import shutil
import sys
from pathlib import Path

sys.dont_write_bytecode = True

# Pytest writes the bytecode of this file before Python executes the file.
# The flag above cannot stop that one write, so this file removes its own cache.
shutil.rmtree(Path(__file__).parent / "__pycache__", ignore_errors=True)
