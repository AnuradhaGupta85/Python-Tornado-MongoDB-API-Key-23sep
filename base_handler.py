# Shared Tornado handler behavior for JSON, CORS, and API key authentication.
import json
import tornado.web
from auth import get_current_api_key

class BaseHandler(tornado.web.RequestHandler):
    auth_required = False

    def set_default_headers(self) -> None:
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', 'Content-Type, X-API-Key, X-Admin-Key')
        self.set_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')

    async def prepare(self) -> None:
        self.current_api_key = None
        if self.auth_required:
            self.current_api_key = await get_current_api_key(self)
            if not self.current_api_key.get('user_id'):
                raise tornado.web.HTTPError(403, reason='This API key is not associated with a user')

    def options(self, *args, **kwargs) -> None:
        self.set_status(204)
        self.finish()

    def write_json(self, body: object, status: int = 200) -> None:
        self.set_status(status)
        self.set_header('Content-Type', 'application/json')
        self.write(json.dumps(body, default=str))

    def parse_json(self) -> dict:
        try:
            return json.loads(self.request.body or b'{}')
        except json.JSONDecodeError as exc:
            raise tornado.web.HTTPError(400, reason='Invalid JSON') from exc

    def write_error(self, status_code: int, **kwargs) -> None:
        detail = self._reason or 'Internal Server Error'
        self.set_header('Content-Type', 'application/json')
        self.finish(json.dumps({'detail': detail}))
