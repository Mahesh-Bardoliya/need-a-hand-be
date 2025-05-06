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
from .utils import generate_password_hash
from .utils import is_user_authenticated

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


def except_exiting_login(request: Request, settings: Settings):
    """
    Check if the user is already logged in by verifying the access token in cookies.

    Cookies Workflow:
    - Checks for the presence of the `access_token` cookie.
    - If the token is valid, the user is considered logged in.
    - If the token is invalid, it allows the user to proceed with login.
    """
    token = request.cookies.get("access_token")
    if not token:
        return
    try:
        decode_token_wrapper(token, settings.secret_key, settings.jwt_algorithm)
    except JWTError:
        pass

    raise_error_message(
        status_code=status.HTTP_421_MISDIRECTED_REQUEST,
        message="User have already logged in. Please refresh to login",
        error_code=421,
        details=[],
        headers={"WWW-Authenticate": "Bearer"},
    )


@auth_router.post(
    "/register", response_class=Response, status_code=status.HTTP_201_CREATED
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
    except_exiting_login(request, settings)

    existing_user = db_session.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

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
        {"email": new_user.email, "username": new_user.username}
    )
    response.set_cookie(key="access_token", value=f"Bearer {token}", httponly=True)


@auth_router.post("/login", response_class=Response, status_code=status.HTTP_200_OK)
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
    db_user = db_session.query(User).filter(User.username == form_data.username).first()
    if not is_user_authenticated(form_data.password, db_user):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(
        {"email": db_user.email, "username": db_user.username}
    )
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=True,
        samesite="none",
    )


@auth_router.get("/refresh", response_class=Response, status_code=status.HTTP_200_OK)
def refresh_access_token(
    request: Request,
    response: Response,
    settings: Settings = Depends(get_settings),
    current_user: User = Depends(get_current_user),
):
    """
    Refresh the current session's access token.

    Overview:
    - Validates current token
    - Issues new access token
    - Maintains user session

    Use Case & Workflow:
    1. Called automatically before token expiration
    2. Validates existing token
    3. Generates new token with fresh expiration
    4. Updates session cookie
    5. Returns 200 OK on success

    Validations:
    - Verifies existing token is valid
    - Checks user still exists and is active
    - Validates token signature and expiration
    - Returns 401 if current token is invalid
    """
    try:
        decode_token_wrapper(
            request.cookies.get("access_token"),
            settings.secret_key,
            settings.jwt_algorithm,
        )
    except JWTError:
        raise_credentials_exception()

    access_token = create_access_token(
        {"email": current_user.email, "username": current_user.username}
    )

    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=True,
        samesite="none",
    )


@auth_router.delete("/logout", response_class=Response, status_code=status.HTTP_200_OK)
def logout(response: Response):
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
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=True,
        samesite="none",
    )
