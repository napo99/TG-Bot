"""
Pytest configuration for liquidation-aggregator tests
Configures Python path to allow imports from parent directories
"""

import sys
from pathlib import Path

# Add service root to Python path (for importing production modules)
service_root = Path(__file__).parent.parent
if str(service_root) not in sys.path:
    sys.path.insert(0, str(service_root))

# Add project root to Python path (for importing shared modules)
project_root = service_root.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Add tests directory to Python path (for importing test utilities)
tests_dir = Path(__file__).parent
if str(tests_dir) not in sys.path:
    sys.path.insert(0, str(tests_dir))
