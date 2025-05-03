from passlib.context import CryptContext

from ..models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def is_user_authenticated(password: str, user: User = None):
    if (
        user
        and user.password_hash
        and len(user.password_hash.strip()) != 0
        and verify_password(password, user.password_hash)
    ):
        return True
    return False
