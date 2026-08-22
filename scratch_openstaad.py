import os
from openstaad import ops

try:
    s = ops.connect()
    print("Connected")
    filename = s.GetSTAADFile()
    print(f"File: {filename}")
    # Try to check if results are available
    res = s.AreResultsAvailable() if hasattr(s, 'AreResultsAvailable') else None
    print(f"AreResultsAvailable: {res}")
except Exception as e:
    print(f"Error: {e}")
