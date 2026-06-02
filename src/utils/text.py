import re
import hashlib

def normalize(s):
    return re.sub(r"\s+", " ", (s or "")).strip().lower()

def text_hash(s):
    return hashlib.sha256(normalize(s).encode("utf-8")).hexdigest()
