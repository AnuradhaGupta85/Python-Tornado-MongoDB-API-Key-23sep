# API key authentication backed by MongoDB.
from datetime import datetime, timezone
import tornado.web
from database import db
from security import hash_api_key

async def get_current_api_key(handler) -> dict:
    raw_key = handler.request.headers.get('X-API-Key', '')
    if not raw_key:
        raise tornado.web.HTTPError(401, reason='X-API-Key header is required')
    record = await db.api_keys.find_one({'key_hash': hash_api_key(raw_key), 'is_active': True})
    if not record:
        raise tornado.web.HTTPError(401, reason='Invalid or revoked API key')
    await db.api_keys.update_one({'_id': record['_id']}, {'$set': {'last_used_at': datetime.now(timezone.utc)}})
    return record
