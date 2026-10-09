from pydantic import BaseModel
from typing import List, TypeVar, Generic, Optional

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T]
    count: int

class ErrorResponse(BaseModel):
    detail: str
