# Registration, login, profile, and administrative API key handlers.
from datetime import datetime, timezone
import bcrypt
from bson import ObjectId
from pydantic import ValidationError
import tornado.web
from base_handler import BaseHandler
from database import db
from schemas import RegisterSchema, LoginSchema, ApiKeyCreateSchema
from security import generate_api_key, get_admin_key

class RegisterHandler(BaseHandler):
    async def post(self) -> None:
        try:
            payload = RegisterSchema.model_validate(self.parse_json())
        except ValidationError as exc:
            raise self.validation_error(exc) from exc
        email = str(payload.email).lower()
        if await db.users.find_one({'email': email}):
            raise tornado.web.HTTPError(409, reason='Email is already registered')
        password_hash = bcrypt.hashpw(payload.password.encode(), bcrypt.gensalt()).decode()
        result = await db.users.insert_one({'email': email, 'password_hash': password_hash, 'created_at': datetime.now(timezone.utc)})
        self.write_json({'id': str(result.inserted_id), 'email': email}, 201)

class LoginHandler(BaseHandler):
    async def post(self) -> None:
        try:
            payload = LoginSchema.model_validate(self.parse_json())
        except ValidationError as exc:
            raise self.validation_error(exc) from exc
        user = await db.users.find_one({'email': str(payload.email).lower()})
        if not user or not bcrypt.checkpw(payload.password.encode(), user['password_hash'].encode()):
            raise tornado.web.HTTPError(401, reason='Invalid email or password')
        raw_key, key_hash = generate_api_key()
        await db.api_keys.insert_one({'key_hash': key_hash, 'name': 'login session', 'user_id': str(user['_id']), 'is_active': True, 'created_at': datetime.now(timezone.utc), 'last_used_at': None})
        self.write_json({'api_key': raw_key, 'user': {'id': str(user['_id']), 'email': user['email']}})

class MeHandler(BaseHandler):
    auth_required = True
    async def get(self) -> None:
        try:
            user_id = ObjectId(self.current_api_key['user_id'])
        except Exception as exc:
            raise tornado.web.HTTPError(401, reason='Invalid user key') from exc
        user = await db.users.find_one({'_id': user_id}, {'password_hash': 0})
        if not user:
            raise tornado.web.HTTPError(401, reason='User no longer exists')
        self.write_json({'id': str(user['_id']), 'email': user['email'], 'created_at': user['created_at']})

class ApiKeyHandler(BaseHandler):
    async def post(self) -> None:
        get_admin_key(self)
        try:
            payload = ApiKeyCreateSchema.model_validate(self.parse_json())
        except ValidationError as exc:
            raise self.validation_error(exc) from exc
        raw_key, key_hash = generate_api_key()
        result = await db.api_keys.insert_one({'key_hash': key_hash, 'name': payload.name, 'user_id': None, 'is_active': True, 'created_at': datetime.now(timezone.utc), 'last_used_at': None})
        self.write_json({'id': str(result.inserted_id), 'name': payload.name, 'api_key': raw_key}, 201)

    async def get(self) -> None:
        get_admin_key(self)
        keys = []
        async for key in db.api_keys.find({}, {'key_hash': 0}):
            keys.append({'id': str(key['_id']), 'name': key['name'], 'user_id': key.get('user_id'), 'is_active': key['is_active'], 'created_at': key['created_at'], 'last_used_at': key.get('last_used_at')})
        self.write_json({'items': keys, 'total': len(keys)})

class ApiKeyDetailHandler(BaseHandler):
    async def delete(self, key_id: str) -> None:
        get_admin_key(self)
        if not ObjectId.is_valid(key_id):
            raise tornado.web.HTTPError(404, reason='API key not found')
        result = await db.api_keys.update_one({'_id': ObjectId(key_id)}, {'$set': {'is_active': False}})
        if not result.matched_count:
            raise tornado.web.HTTPError(404, reason='API key not found')
        self.set_status(204)
        self.finish()
