import sys
import os

# Add the worker directory to sys.path so tests can import 'worker'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
