from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from ..dependencies import get_current_user
from ..dependencies import get_db_session
from ..helpers.errors_and_exceptions import raise_error_message
from ..models import User
from ..schemas.user import UserProfileResponseSchema
from ..schemas.user import UserResponseSchema

users_router = APIRouter(prefix="/users", tags=["Users"])


@users_router.get("/profile", response_model=UserProfileResponseSchema)
def current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get the authenticated user's profile details.

    Overview:
    - Retrieves the complete profile information of the currently logged-in user
    - Returns detailed user information including personal details and preferences

    Use Case & Workflow:
    - Used when displaying user's own profile information
    - Typically called after successful authentication
    - Frontend can use this to populate user profile pages or settings

    Validations:
    - Requires valid authentication token
    - Automatically validates user existence through the get_current_user dependency
    - Returns 401 if unauthorized or token is invalid
    """
    return current_user


@users_router.get("/{uuid}", response_model=UserResponseSchema)
def fetch_user(uuid: UUID, db_session: Session = Depends(get_db_session)):
    """
    Retrieve a specific user's public profile by UUID.

    Overview:
    - Fetches public profile information for any user in the system
    - Provides a way to view other users' profiles

    Use Case & Workflow:
    - Used when viewing other users' profiles
    - Common in social features or user directories
    - Can be accessed by both authenticated and unauthenticated users

    Validations:
    - Validates UUID format
    - Checks if user exists and is not deleted
    - Returns 404 if user not found
    - Only returns non-sensitive user information
    """
    user = (
        db_session.query(User)
        .filter(User.uuid == uuid, User.deleted_at == None)
        .one_or_none()
    )

    if not user:
        raise_error_message(
            status_code=404,
            message="User not found.",
            error_code=4004,
            details=[{"dev_error": ""}],
        )
    return user
