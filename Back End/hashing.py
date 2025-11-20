import json
import hashlib

def canonical_json(obj):
    """
    Produce canonical JSON for consistent hashing.
    """
    return json.dumps(obj, separators=(",", ":"), sort_keys=True)

def sha256_bytes32_hex(obj):
    canonical = canonical_json(obj)
    h = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return "0x" + h
