from fastapi import HTTPException
from fastapi import status


def raise_credentials_exception():
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    raise credentials_exception


def raise_error_message(
    status_code: int, message: str, error_code: int, details: list, headers: dict = None
):
    details = {"details": details, "error_code": error_code, "error_message": message}
    if headers:
        raise HTTPException(status_code=status_code, detail=details, headers=headers)
    raise HTTPException(status_code=status_code, detail=details)
