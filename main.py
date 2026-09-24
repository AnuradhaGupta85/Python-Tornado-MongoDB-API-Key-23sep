# Tornado application entry point and routing.
import os
from dotenv import load_dotenv
import tornado.ioloop
import tornado.web
from base_handler import BaseHandler
from database import ensure_indexes
from handlers.auth_handlers import RegisterHandler, LoginHandler, MeHandler, ApiKeyHandler, ApiKeyDetailHandler
from handlers.category_handlers import CategoryCollectionHandler, CategoryDetailHandler
from handlers.transaction_handlers import TransactionCollectionHandler, TransactionDetailHandler, MonthlySummaryHandler

load_dotenv('.env_5ad06667-9bcd-48b5-bb6c-a469b3be3571', override=True)

class HealthHandler(BaseHandler):
    async def get(self) -> None:
        self.write_json({'status': 'ok'})

def make_app() -> tornado.web.Application:
    return tornado.web.Application([
        (r'/health', HealthHandler),
        (r'/api/v1/auth/register', RegisterHandler),
        (r'/api/v1/auth/login', LoginHandler),
        (r'/api/v1/auth/me', MeHandler),
        (r'/api/v1/admin/api-keys', ApiKeyHandler),
        (r'/api/v1/admin/api-keys/([^/]+)', ApiKeyDetailHandler),
        (r'/api/v1/categories', CategoryCollectionHandler),
        (r'/api/v1/categories/([^/]+)', CategoryDetailHandler),
        (r'/api/v1/transactions', TransactionCollectionHandler),
        (r'/api/v1/transactions/summary/monthly', MonthlySummaryHandler),
        (r'/api/v1/transactions/([^/]+)', TransactionDetailHandler),
    ], debug=False)

async def bootstrap() -> None:
    await ensure_indexes()

if __name__ == '__main__':
    port = int(os.getenv('PORT', '25350'))
    app = make_app()
    app.listen(port)
    tornado.ioloop.IOLoop.current().add_callback(bootstrap)
    tornado.ioloop.IOLoop.current().start()
