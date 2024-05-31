from starlette.config import Config
from starlette.datastructures import Secret

try:
    config = Config(".env")
except FileNotFoundError:
    config = Config()

DATABASE_URL = config("DATABASE_URL", cast=Secret)
TEST_DATABASE_URL = config("TEST_DATABASE_URL", cast=Secret)
JWT_SECRET_KEY = config("JWT_SECRET_KEY", cast=Secret)
JWT_ALGORITHM = config("JWT_ALGORITHM", cast=Secret)
