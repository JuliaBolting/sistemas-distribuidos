import hashlib
from pathlib import Path

def sha256_of_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def save_hash(hash_hex, outpath):
    out = Path(outpath)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf8") as f:
        f.write(hash_hex + "\n")