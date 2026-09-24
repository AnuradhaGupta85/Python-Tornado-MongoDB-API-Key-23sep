# Category collection and detail handlers.
from datetime import datetime, timezone
from bson import ObjectId
from pydantic import ValidationError
import tornado.web
from base_handler import BaseHandler
from database import db
from schemas import CategoryCreateSchema, CategoryUpdateSchema

class CategoryCollectionHandler(BaseHandler):
    auth_required = True
    async def get(self) -> None:
        user_id = self.current_api_key['user_id']
        query = {'$or': [{'is_predefined': True}, {'user_id': user_id}]}
        limit, offset = self.pagination()
        total = await db.categories.count_documents(query)
        items = []
        async for item in db.categories.find(query).sort('name', 1).skip(offset).limit(limit):
            items.append({'id': str(item['_id']), 'name': item['name'], 'is_predefined': item['is_predefined'], 'user_id': item.get('user_id')})
        self.write_json({'items': items, 'total': total, 'limit': limit, 'offset': offset})

    async def post(self) -> None:
        try:
            payload = CategoryCreateSchema.model_validate(self.parse_json())
        except ValidationError as exc:
            raise self.validation_error(exc) from exc
        name = payload.name.strip()
        if not name:
            raise tornado.web.HTTPError(422, reason='Category name cannot be blank')
        doc = {'name': name, 'user_id': self.current_api_key['user_id'], 'is_predefined': False, 'created_at': datetime.now(timezone.utc)}
        try:
            result = await db.categories.insert_one(doc)
        except Exception as exc:
            if 'duplicate key' in str(exc).lower():
                raise tornado.web.HTTPError(409, reason='You already have a category with this name') from exc
            raise
        self.write_json({'id': str(result.inserted_id), 'name': name, 'is_predefined': False, 'user_id': doc['user_id']}, 201)

    def pagination(self) -> tuple[int, int]:
        try:
            limit, offset = int(self.get_query_argument('limit', '20')), int(self.get_query_argument('offset', '0'))
        except ValueError as exc:
            raise tornado.web.HTTPError(400, reason='limit and offset must be integers') from exc
        return max(1, min(limit, 100)), max(0, offset)

class CategoryDetailHandler(BaseHandler):
    auth_required = True
    async def get(self, category_id: str) -> None:
        category = await self._available(category_id)
        self.write_json({'id': str(category['_id']), 'name': category['name'], 'is_predefined': category['is_predefined'], 'user_id': category.get('user_id')})

    async def put(self, category_id: str) -> None:
        category = await self._available(category_id)
        if category['is_predefined'] or category.get('user_id') != self.current_api_key['user_id']:
            raise tornado.web.HTTPError(403, reason='Only your custom categories can be renamed')
        try:
            payload = CategoryUpdateSchema.model_validate(self.parse_json())
        except ValidationError as exc:
            raise self.validation_error(exc) from exc
        name = payload.name.strip()
        if not name:
            raise tornado.web.HTTPError(422, reason='Category name cannot be blank')
        existing = await db.categories.find_one({
            'user_id': self.current_api_key['user_id'], 'name': name, '_id': {'$ne': category['_id']}
        })
        if existing:
            raise tornado.web.HTTPError(409, reason='You already have a category with this name')
        try:
            await db.categories.update_one({'_id': category['_id']}, {'$set': {'name': name}})
        except Exception as exc:
            if 'duplicate key' in str(exc).lower():
                raise tornado.web.HTTPError(409, reason='You already have a category with this name') from exc
            raise
        self.write_json({'id': str(category['_id']), 'name': name, 'is_predefined': False, 'user_id': category['user_id']})

    async def delete(self, category_id: str) -> None:
        category = await self._available(category_id)
        if category['is_predefined'] or category.get('user_id') != self.current_api_key['user_id']:
            raise tornado.web.HTTPError(403, reason='Only your unused custom categories can be deleted')
        if await db.transactions.find_one({'category_id': category_id}):
            raise tornado.web.HTTPError(409, reason='Category is in use by a transaction')
        await db.categories.delete_one({'_id': category['_id']})
        self.set_status(204)
        self.finish()

    async def _available(self, category_id: str) -> dict:
        if not ObjectId.is_valid(category_id):
            raise tornado.web.HTTPError(404, reason='Category not found')
        category = await db.categories.find_one({'_id': ObjectId(category_id)})
        if not category or (not category['is_predefined'] and category.get('user_id') != self.current_api_key['user_id']):
            raise tornado.web.HTTPError(404, reason='Category not found')
        return category
