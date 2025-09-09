import base64
import hashlib
import hmac
import os

# Stored password format:
# pbkdf2_sha256$<iterations>$<salt_b64>$<hash_b64>
ALGO = "pbkdf2_sha256"
DEFAULT_ITERATIONS = 100_000
HASH_LEN = 32  # 256-bit
SALT_LEN = 16

#salt = os.urandom(SALT_LEN)


def hash_password(plain: str, *, iterations: int = DEFAULT_ITERATIONS) -> str:
    #
    salt = os.urandom(SALT_LEN)
    dk = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt, iterations, dklen=HASH_LEN)
    return f"{ALGO}${iterations}${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(dk).decode()}"


def verify_password(plain: str, stored: str) -> bool:
    try:
        algo, iters_str, salt_b64, hash_b64 = stored.split("$", 3)
        if algo != ALGO:
            return False
        iterations = int(iters_str)
        salt = base64.urlsafe_b64decode(salt_b64.encode())
        expected = base64.urlsafe_b64decode(hash_b64.encode())
        dk = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt, iterations, dklen=len(expected))
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False
