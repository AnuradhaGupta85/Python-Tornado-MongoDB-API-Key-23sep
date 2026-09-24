# Pydantic request and response validation schemas.
from datetime import date as Date, datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

class RegisterSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class LoginSchema(RegisterSchema):
    pass

class ApiKeyCreateSchema(BaseModel):
    name: str = Field(min_length=1, max_length=100)

class ChangePasswordSchema(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

class CategoryCreateSchema(BaseModel):
    name: str = Field(min_length=1, max_length=100)

class CategoryUpdateSchema(CategoryCreateSchema):
    pass

class TransactionCreateSchema(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    type: Literal['Income', 'Expense']
    category_id: str = Field(min_length=1)
    date: Date
    description: str = Field(default='', max_length=1000)

class TransactionUpdateSchema(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    type: Literal['Income', 'Expense'] | None = None
    category_id: str | None = Field(default=None, min_length=1)
    date: Date | None = None
    description: str | None = Field(default=None, max_length=1000)

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    created_at: datetime

class CategoryResponse(BaseModel):
    id: str
    name: str
    is_predefined: bool
    user_id: str | None

class TransactionResponse(BaseModel):
    id: str
    amount: Decimal
    type: str
    category_id: str
    category_name: str
    date: Date
    description: str
