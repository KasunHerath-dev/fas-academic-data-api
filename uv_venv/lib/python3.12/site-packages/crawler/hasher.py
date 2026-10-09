import hashlib
import os

def calculate_sha256(file_path: str) -> str:
    """
    Calculates the SHA-256 hash of a file's contents.
    The file is read in chunks to handle potentially large PDFs without using too much memory.
    """
    sha256_hash = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        # Read in 4K chunks
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
            
    return sha256_hash.hexdigest()

def calculate_sha256_from_bytes(data: bytes) -> str:
    """
    Calculates the SHA-256 hash from in-memory bytes.
    """
    sha256_hash = hashlib.sha256()
    sha256_hash.update(data)
    return sha256_hash.hexdigest()
