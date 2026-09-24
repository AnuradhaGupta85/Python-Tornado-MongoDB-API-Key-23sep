# Transaction CRUD, filtering, sorting, and monthly summary handlers.
from datetime import datetime, timezone, date
from bson import ObjectId
from pydantic import ValidationError
import tornado.web
from base_handler import BaseHandler
from database import db
from schemas import TransactionCreateSchema, TransactionUpdateSchema

class TransactionCollectionHandler(BaseHandler):
    auth_required = True
    async def get(self) -> None:
        user_id = self.current_api_key['user_id']
        query = {'user_id': user_id}
        tx_type = self.get_query_argument('type', None)
        if tx_type:
            if tx_type not in ('Income', 'Expense'):
                raise tornado.web.HTTPError(400, reason='type must be Income or Expense')
            query['type'] = tx_type
        category_id = self.get_query_argument('category_id', None)
        if category_id:
            if not ObjectId.is_valid(category_id):
                raise tornado.web.HTTPError(400, reason='Invalid category_id')
            query['category_id'] = category_id
        start_date, end_date = self.get_query_argument('start_date', None), self.get_query_argument('end_date', None)
        if start_date or end_date:
            query['date'] = {}
            if start_date:
                try: date.fromisoformat(start_date)
                except ValueError as exc: raise tornado.web.HTTPError(400, reason='start_date must be YYYY-MM-DD') from exc
                query['date']['$gte'] = start_date
            if end_date:
                try: date.fromisoformat(end_date)
                except ValueError as exc: raise tornado.web.HTTPError(400, reason='end_date must be YYYY-MM-DD') from exc
                query['date']['$lte'] = end_date
        search = self.get_query_argument('search', '').strip()
        if search:
            category_ids = [str(x['_id']) async for x in db.categories.find({'name': {'$regex': search, '$options': 'i'}})]
            query['$or'] = [{'description': {'$regex': search, '$options': 'i'}}, {'category_id': {'$in': category_ids}}]
        try:
            limit = max(1, min(int(self.get_query_argument('limit', '20')), 100))
            offset = max(0, int(self.get_query_argument('offset', '0')))
        except ValueError as exc:
            raise tornado.web.HTTPError(400, reason='limit and offset must be integers') from exc
        sort_by = self.get_query_argument('sort_by', 'date')
        if sort_by not in {'date', 'amount', 'category'}:
            raise tornado.web.HTTPError(400, reason='sort_by must be date, amount, or category')
        order = self.get_query_argument('order', 'desc')
        if order not in {'asc', 'desc'}:
            raise tornado.web.HTTPError(400, reason='order must be asc or desc')
        total = await db.transactions.count_documents(query)
        records = [x async for x in db.transactions.find(query)]
        categories = {str(x['_id']): x['name'] async for x in db.categories.find({'_id': {'$in': [ObjectId(x['category_id']) for x in records if ObjectId.is_valid(x['category_id'])]}})}
        reverse = order == 'desc'
        records.sort(key=lambda x: categories.get(x['category_id'], '') if sort_by == 'category' else x[sort_by], reverse=reverse)
        items = [self.serialize(record, categories.get(record['category_id'], 'Unknown')) for record in records[offset:offset + limit]]
        self.write_json({'items': items, 'total': total, 'limit': limit, 'offset': offset})

    async def post(self) -> None:
        try:
            payload = TransactionCreateSchema.model_validate(self.parse_json())
        except ValidationError as exc:
            raise tornado.web.HTTPError(422, reason=str(exc)) from exc
        category = await self.category_for_user(payload.category_id)
        now = datetime.now(timezone.utc)
        doc = {'user_id': self.current_api_key['user_id'], 'category_id': payload.category_id, 'amount': float(payload.amount), 'type': payload.type, 'date': payload.date.isoformat(), 'description': payload.description, 'created_at': now, 'updated_at': now}
        result = await db.transactions.insert_one(doc)
        doc['_id'] = result.inserted_id
        self.write_json(self.serialize(doc, category['name']), 201)

    async def category_for_user(self, category_id: str) -> dict:
        if not ObjectId.is_valid(category_id):
            raise tornado.web.HTTPError(422, reason='category_id is invalid')
        category = await db.categories.find_one({'_id': ObjectId(category_id)})
        if not category or (not category['is_predefined'] and category.get('user_id') != self.current_api_key['user_id']):
            raise tornado.web.HTTPError(422, reason='Category is unavailable')
        return category

    @staticmethod
    def serialize(doc: dict, category_name: str) -> dict:
        return {'id': str(doc['_id']), 'amount': doc['amount'], 'type': doc['type'], 'category_id': doc['category_id'], 'category_name': category_name, 'date': doc['date'], 'description': doc.get('description', '')}

class TransactionDetailHandler(TransactionCollectionHandler):
    async def get(self, transaction_id: str) -> None:
        doc = await self.owned(transaction_id)
        category = await self.category_for_user(doc['category_id'])
        self.write_json(self.serialize(doc, category['name']))

    async def put(self, transaction_id: str) -> None:
        doc = await self.owned(transaction_id)
        try:
            payload = TransactionUpdateSchema.model_validate(self.parse_json())
        except ValidationError as exc:
            raise tornado.web.HTTPError(422, reason=str(exc)) from exc
        changes = payload.model_dump(exclude_none=True)
        if 'category_id' in changes:
            category = await self.category_for_user(changes['category_id'])
        else:
            category = await self.category_for_user(doc['category_id'])
        if 'amount' in changes: changes['amount'] = float(changes['amount'])
        if 'date' in changes: changes['date'] = changes['date'].isoformat()
        changes['updated_at'] = datetime.now(timezone.utc)
        await db.transactions.update_one({'_id': doc['_id']}, {'$set': changes})
        doc.update(changes)
        self.write_json(self.serialize(doc, category['name']))

    async def delete(self, transaction_id: str) -> None:
        doc = await self.owned(transaction_id)
        await db.transactions.delete_one({'_id': doc['_id']})
        self.set_status(204)
        self.finish()

    async def owned(self, transaction_id: str) -> dict:
        if not ObjectId.is_valid(transaction_id):
            raise tornado.web.HTTPError(404, reason='Transaction not found')
        doc = await db.transactions.find_one({'_id': ObjectId(transaction_id), 'user_id': self.current_api_key['user_id']})
        if not doc:
            raise tornado.web.HTTPError(404, reason='Transaction not found')
        return doc

class MonthlySummaryHandler(BaseHandler):
    auth_required = True
    async def get(self) -> None:
        month = self.get_query_argument('month', '')
        try:
            datetime.strptime(month, '%Y-%m')
        except ValueError as exc:
            raise tornado.web.HTTPError(400, reason='month must be YYYY-MM') from exc
        rows = [x async for x in db.transactions.find({'user_id': self.current_api_key['user_id'], 'date': {'$gte': f'{month}-01', '$lte': f'{month}-31'}})]
        income = sum(x['amount'] for x in rows if x['type'] == 'Income')
        expenses = sum(x['amount'] for x in rows if x['type'] == 'Expense')
        cat_ids = [ObjectId(x['category_id']) for x in rows if x['type'] == 'Expense' and ObjectId.is_valid(x['category_id'])]
        names = {str(x['_id']): x['name'] async for x in db.categories.find({'_id': {'$in': cat_ids}})}
        breakdown = {}
        for row in rows:
            if row['type'] == 'Expense':
                name = names.get(row['category_id'], 'Unknown')
                breakdown[name] = breakdown.get(name, 0) + row['amount']
        self.write_json({'month': month, 'total_income': income, 'total_expenses': expenses, 'balance': income - expenses, 'expense_by_category': breakdown})
