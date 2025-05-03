import uvicorn

from .dependencies import get_settings
from .factory import create_fastapi, setup_engine

settings = get_settings()

app = create_fastapi(settings)
engine = setup_engine(settings)


if __name__ == "__main__":
    # Used for debugging.
    uvicorn.run(app)
