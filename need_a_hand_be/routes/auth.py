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
from ..dependencies import get_db
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


@auth_router.post("/register", response_class=Response)
def register(
    request: Request,
    response: Response,
    user: UserRegister,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    except_exiting_login(request, settings)

    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        name=user.name,
        username=user.username,
        email=user.email,
        password_hash=generate_password_hash(user.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token(
        {"email": new_user.email, "username": new_user.username}
    )
    response.set_cookie(key="access_token", value=f"Bearer {token}", httponly=True)


@auth_router.post("/login", response_class=Response)
def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    except_exiting_login(request, settings)
    db_user = db.query(User).filter(User.username == form_data.username).first()
    if not is_user_authenticated(form_data.password, db_user):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(
        {"email": db_user.email, "username": db_user.username}
    )
    response.set_cookie(
        key="access_token", value=f"Bearer {access_token}", httponly=True
    )


@auth_router.get("/refresh", response_class=Response)
def refresh(
    request: Request,
    response: Response,
    settings: Settings = Depends(get_settings),
    current_user: User = Depends(get_current_user),
):
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
        key="access_token", value=f"Bearer {access_token}", httponly=True
    )


@auth_router.delete("/logout", response_class=Response)
def login(response: Response):
    response.delete_cookie(key="access_token", httponly=True)
