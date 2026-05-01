import sys
import os

# Add project root to path so we can import 'backend'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.main import app
