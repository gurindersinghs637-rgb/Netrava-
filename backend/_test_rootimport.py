import sys, os
# When launched as "uvicorn backend.app.main:app" from project root,
# Python imports "backend.app.main" but inside main.py uses "from backend.app.xxx"
# This test verifies the root-level import fails without sys.path fix
try:
    import importlib
    spec = importlib.util.find_spec('backend.app.main')
    print(f"backend.app.main spec: {spec}")
except Exception as e:
    print(f"Error: {e}")

print("sys.path:", sys.path[:5])

