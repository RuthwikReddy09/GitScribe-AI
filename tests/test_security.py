import hashlib
import hmac

from app.core.security import verify_github_signature


def test_verify_github_signature_valid():
    body = b'{"hello":"world"}'
    secret = 'secret'
    sig = 'sha256=' + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_github_signature(body, sig, secret)


def test_verify_github_signature_invalid():
    assert not verify_github_signature(b'{}', 'sha256=bad', 'secret')
