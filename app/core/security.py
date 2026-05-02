import hashlib
import hmac


def verify_github_signature(body: bytes, signature_header: str | None, secret: str) -> bool:
    if not signature_header or not signature_header.startswith('sha256='):
        return False
    expected = 'sha256=' + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)
