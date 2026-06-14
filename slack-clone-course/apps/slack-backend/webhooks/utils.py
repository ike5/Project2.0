"""HMAC signing/verification for webhook payloads."""
import hashlib
import hmac

SIGNATURE_HEADER = "X-Slackclone-Signature"


def sign(secret: str, body: bytes) -> str:
    """Return 'sha256=<hex>' for a raw request body and a shared secret."""
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def verify(secret: str, body: bytes, signature: str) -> bool:
    """Constant-time check that `signature` matches `body` signed with `secret`."""
    expected = sign(secret, body)
    # compare_digest avoids timing attacks that leak how much of the sig matched.
    return hmac.compare_digest(expected, signature or "")
