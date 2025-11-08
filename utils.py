# utils.py
from pathlib import Path
import json
from datetime import datetime

data_dir = Path("data")
uploads_dir = Path("uploads")

def ensure_dirs():
    data_dir.mkdir(exist_ok=True)
    uploads_dir.mkdir(exist_ok=True)

def now_iso():
    return datetime.utcnow().isoformat()

def atomic_save_csv(df, path):
    """
    Save dataframe to CSV atomically by writing to a temp file then replacing.
    """
    tmp = Path(str(path) + ".tmp")
    df.to_csv(tmp, index=False)
    tmp.replace(path)

def read_json_field(val):
    try:
        return json.loads(val)
    except Exception:
        return None
