# API key and password security helpers.
import hashlib
import os
import secrets
import tornado.web
from dotenv import load_dotenv

load_dotenv('.env_5ad06667-9bcd-48b5-bb6c-a469b3be3571', override=True)

def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()

def generate_api_key() -> tuple[str, str]:
    raw_key = secrets.token_urlsafe(32)
    return raw_key, hash_api_key(raw_key)

def get_admin_key(handler) -> None:
    expected = os.getenv('ADMIN_API_KEY', '')
    supplied = handler.request.headers.get('X-Admin-Key', '')
    if not expected or not supplied or not secrets.compare_digest(supplied, expected):
        raise tornado.web.HTTPError(401, reason='A valid X-Admin-Key is required')
