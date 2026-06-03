from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT / "basededatos" / "bolsa_data.db"

DB_PATH = Path(os.environ.get("AXON_DB_PATH", str(DEFAULT_DB_PATH))).resolve()
CORS_ORIGINS = [
    o.strip()
    for o in os.environ.get(
        "AXON_CORS_ORIGINS",
        "http://localhost:8501,http://127.0.0.1:8501",
    ).split(",")
    if o.strip()
]
