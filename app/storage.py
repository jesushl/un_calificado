import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode

from .config import get_settings


def object_root() -> Path:
    root = Path(get_settings().object_store_path)
    if not root.is_absolute():
        root = Path(__file__).resolve().parent.parent / root
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()


def object_path(object_key: str) -> Path:
    safe = Path(object_key)
    if safe.is_absolute() or ".." in safe.parts:
        raise ValueError("object_key inválido")
    return object_root() / safe


def put_object(object_key: str, data: bytes) -> Path:
    path = object_path(object_key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def signed_download(object_key: str, file_id: str, ttl_seconds: int = 900) -> dict:
    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
    expires = int(expires_at.timestamp())
    secret = (settings.file_signing_secret or settings.jwt_secret).encode("utf-8")
    message = f"{file_id}:{object_key}:{expires}".encode("utf-8")
    signature = hmac.new(secret, message, hashlib.sha256).hexdigest()
    query = urlencode({"exp": expires, "sig": signature})
    return {
        "downloadUrl": f"/api/v1/files/{file_id}/content?{query}",
        "downloadUrlExpiresAt": expires_at.isoformat(),
    }


def verify_signed_download(file_id: str, object_key: str, expires: str, signature: str) -> bool:
    try:
        expires_ts = int(expires)
    except (TypeError, ValueError):
        return False
    if expires_ts < int(datetime.now(timezone.utc).timestamp()):
        return False
    settings = get_settings()
    secret = (settings.file_signing_secret or settings.jwt_secret).encode("utf-8")
    message = f"{file_id}:{object_key}:{expires_ts}".encode("utf-8")
    expected = hmac.new(secret, message, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature or "")
