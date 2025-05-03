from fastapi import APIRouter
from fastapi import Depends

from ..dependencies import get_current_user
from ..models import User
from ..schemas.user import UserProfileSchema

users_router = APIRouter(prefix="/users", tags=["Users"])


@users_router.get("/profile", response_model=UserProfileSchema)
def register(current_user: User = Depends(get_current_user)):
    return current_user
