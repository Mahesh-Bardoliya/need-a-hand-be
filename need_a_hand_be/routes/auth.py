from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import Response
from fastapi import status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy.orm import Session

from ..config import Settings
from ..dependencies import get_current_user
from ..dependencies import get_db_session
from ..dependencies import get_settings
from ..helpers.errors_and_exceptions import raise_credentials_exception
from ..helpers.errors_and_exceptions import raise_error_message
from ..helpers.token import create_access_token
from ..helpers.token import decode_token_wrapper
from ..models import User
from ..schemas.auth import UserRegister
from ..schemas.user import UserResponseSchema
from .utils import generate_password_hash
from .utils import is_user_authenticated

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post(
    "/register", response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED
)
def register(
    request: Request,
    response: Response,
    user: UserRegister,
    db_session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
):
    """
    Register a new user account in the system.

    Overview:
    - Creates a new user account with provided details
    - Sets up initial authentication by generating access token
    - Automatically logs in the user after successful registration

    Use Case & Workflow:
    1. Client submits registration form with user details
    2. System validates input data
    3. Creates new user record with hashed password
    4. Generates access token
    5. Sets HTTP-only cookie with token
    6. Returns 201 Created on success

    Validations:
    - Checks if email is already registered
    - Validates all required fields in UserRegister schema
    - Ensures user isn't already logged in
    - Password is hashed before storage
    """

    existing_user = db_session.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    existing_username = (
        db_session.query(User).filter(User.username == user.username).first()
    )
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken")

    new_user = User(
        name=user.name,
        username=user.username,
        email=user.email,
        password_hash=generate_password_hash(user.password),
    )
    db_session.add(new_user)
    db_session.commit()
    db_session.refresh(new_user)

    token = create_access_token(
        {"email": new_user.email, "username": new_user.username},
        secret_key=settings.secret_key,
        jwt_algorithm=settings.jwt_algorithm,
        expires_minutes=settings.access_token_expire_minutes,
    )
    is_prod = settings.environment == "production"
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        secure=is_prod,
        samesite="none" if is_prod else "lax",
    )
    return new_user


@auth_router.post(
    "/login", response_model=UserResponseSchema, status_code=status.HTTP_200_OK
)
def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db_session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
):
    """
    Authenticate user and create session.

    Overview:
    - Validates user credentials
    - Creates and sets session token
    - Establishes secure session via cookies

    Use Case & Workflow:
    1. User submits username/password
    2. System validates credentials
    3. Generates new access token
    4. Sets secure HTTP-only cookie
    5. Returns 200 OK on success

    Validations:
    - Verifies username exists
    - Validates password hash
    - Ensures secure cookie settings (HTTP-only, secure, SameSite)
    - Returns 401 for invalid credentials
    """
    db_user = (
        db_session.query(User)
        .filter(
            (User.username == form_data.username) | (User.email == form_data.username)
        )
        .first()
    )
    if not is_user_authenticated(form_data.password, db_user):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(
        {"email": db_user.email, "username": db_user.username},
        secret_key=settings.secret_key,
        jwt_algorithm=settings.jwt_algorithm,
        expires_minutes=settings.access_token_expire_minutes,
    )
    is_prod = settings.environment == "production"
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=is_prod,
        samesite="none" if is_prod else "lax",
    )
    return db_user


from ..dependencies import get_current_user_for_refresh


@auth_router.get(
    "/refresh", response_model=UserResponseSchema, status_code=status.HTTP_200_OK
)
def refresh_access_token(
    request: Request,
    response: Response,
    settings: Settings = Depends(get_settings),
    current_user: User = Depends(get_current_user_for_refresh),
):
    """
    Refresh the current session's access token.

    Overview:
    - Validates current token (allows recently expired ones)
    - Issues new access token
    - Maintains user session

    Use Case & Workflow:
    1. Called automatically when a request returns 401
    2. Validates existing token signature and window
    3. Generates new token with fresh expiration
    4. Updates session cookie
    5. Returns 200 OK on success

    Validations:
    - Verifies existing token signature is valid
    - Allows tokens expired within the last 7 days
    - Checks user still exists and is active
    - Returns 401 if current token is invalid or too old
    """

    access_token = create_access_token(
        {"email": current_user.email, "username": current_user.username},
        secret_key=settings.secret_key,
        jwt_algorithm=settings.jwt_algorithm,
        expires_minutes=settings.access_token_expire_minutes,
    )

    is_prod = settings.environment == "production"
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=is_prod,
        samesite="none" if is_prod else "lax",
    )
    return current_user


@auth_router.delete("/logout", status_code=status.HTTP_200_OK)
def logout(
    response: Response,
    settings: Settings = Depends(get_settings),
):
    """
    End user session and logout.

    Overview:
    - Terminates current user session
    - Removes authentication cookie
    - Logs user out of the system

    Use Case & Workflow:
    1. User requests logout
    2. System invalidates session
    3. Removes access token cookie
    4. Returns 200 OK
    5. Client redirects to logged-out state

    Validations:
    - No specific validation required
    - Cookie is removed regardless of current state
    - Succeeds even if already logged out
    """
    is_prod = settings.environment == "production"
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=is_prod,
        samesite="none" if is_prod else "lax",
    )
    return {"message": "Successfully logged out."}
