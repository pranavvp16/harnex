from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass

# 200k iterations is the OWASP 2024 minimum for PBKDF2-HMAC-SHA256 with bare passwords;
# our keys are 32 bytes of entropy so this is conservative but cheap to verify.
PBKDF2_ITERATIONS = 200_000
KEY_BYTES = 32  # base64url -> 43 chars
PREFIX_BYTES = 6  # base64url -> 8 chars; indexed for fast lookup
TOKEN_PREFIX = "hnx"


@dataclass(frozen=True)
class IssuedKey:
    plaintext: str  # only returned once, on issue
    prefix: str
    hash_blob: str  # `<salt_hex>$<hash_hex>`


def _b64url(b: bytes) -> str:
    import base64

    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")


def _hash(plaintext: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac(
        "sha256", plaintext.encode("utf-8"), salt, PBKDF2_ITERATIONS, dklen=32
    )


def issue_key() -> IssuedKey:
    prefix = _b64url(secrets.token_bytes(PREFIX_BYTES))
    secret = _b64url(secrets.token_bytes(KEY_BYTES))
    # Separator is '.' (not '_') because base64url uses '_' inside both segments.
    plaintext = f"{TOKEN_PREFIX}.{prefix}.{secret}"
    salt = secrets.token_bytes(16)
    digest = _hash(plaintext, salt)
    return IssuedKey(plaintext=plaintext, prefix=prefix, hash_blob=f"{salt.hex()}${digest.hex()}")


def parse_prefix(plaintext: str) -> str | None:
    """Pull the lookup prefix out of a plaintext key, or None if malformed."""
    parts = plaintext.split(".")
    if len(parts) != 3 or parts[0] != TOKEN_PREFIX:
        return None
    return parts[1] or None


def verify_key(plaintext: str, hash_blob: str) -> bool:
    try:
        salt_hex, digest_hex = hash_blob.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
    except ValueError:
        return False
    actual = _hash(plaintext, salt)
    return hmac.compare_digest(actual, expected)


__all__ = [
    "KEY_BYTES",
    "PBKDF2_ITERATIONS",
    "PREFIX_BYTES",
    "TOKEN_PREFIX",
    "IssuedKey",
    "issue_key",
    "parse_prefix",
    "verify_key",
]
