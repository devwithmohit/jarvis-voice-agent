import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.grpc_server import serve

if __name__ == "__main__":
    serve()
