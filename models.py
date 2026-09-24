# Pydantic document models persisted in MongoDB collections.
from datetime import datetime, date
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class DocumentModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str | None = Field(default=None, alias='_id')

class User(DocumentModel):
    email: str
    password_hash: str
    created_at: datetime
    def __repr__(self) -> str:
        return f'User(email={self.email!r})'

class ApiKey(DocumentModel):
    key_hash: str
    name: str
    user_id: str | None = None
    is_active: bool = True
    created_at: datetime
    last_used_at: datetime | None = None
    def __repr__(self) -> str:
        return f'ApiKey(name={self.name!r})'

class Category(DocumentModel):
    name: str
    user_id: str | None = None
    is_predefined: bool = False
    created_at: datetime
    def __repr__(self) -> str:
        return f'Category(name={self.name!r})'

class Transaction(DocumentModel):
    user_id: str
    category_id: str
    amount: Decimal
    type: Literal['Income', 'Expense']
    date: date
    description: str = ''
    created_at: datetime
    updated_at: datetime
    def __repr__(self) -> str:
        return f'Transaction(id={self.id!r}, type={self.type!r})'
