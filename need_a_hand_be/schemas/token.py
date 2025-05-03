from typing import Optional

from pydantic import BaseModel
from pydantic import EmailStr


class TokenData(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
