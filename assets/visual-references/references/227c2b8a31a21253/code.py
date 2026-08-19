from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from scripts.reference_reconstruction import render_reference

if __name__ == "__main__":
    render_reference("227c2b8a31a21253", Path(__file__).with_name("reconstruction.png"))
