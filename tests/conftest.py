import sys
import os

# Ensure the project root is on sys.path so `src` package can be imported during tests
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
