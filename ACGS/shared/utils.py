# ACGS/shared/utils.py
import logging
import time
from functools import wraps
from typing import Optional, Any, Callable, Coroutine
from pydantic import ValidationError
import uuid
from datetime import datetime, timezone, timedelta
import jwt # PyJWT library
from passlib.context import CryptContext # For password hashing

# --- Configuration (should ideally be loaded from environment variables) ---
# These are placeholders; manage secrets and configurations properly in a real app.
JWT_SECRET_KEY = "your-super-secret-jwt-key" # CHANGE THIS!
JWT_REFRESH_SECRET_KEY = "your-super-secret-jwt-refresh-key" # CHANGE THIS!
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
ALGORITHM = "HS256"

# --- Password Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# --- JWT Token Generation and Decoding ---

def create_jwt_token(
    data: dict,
    secret_key: str,
    expires_delta: timedelta,
    jti: Optional[str] = None
) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    if jti:
        to_encode.update({"jti": jti}) # jti (JWT ID) claim, unique identifier for the token
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
    return encoded_jwt

def create_access_token(user_id: int, username: str, scopes: Optional[list[str]] = None, jti: Optional[str] = None) -> tuple[str, datetime, str]:
    """
    Generates an access token.
    Returns the token, its expiry time, and its JTI.
    """
    if jti is None:
        jti = str(uuid.uuid4())
    expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire_datetime = datetime.now(timezone.utc) + expires_delta
    token = create_jwt_token(
        data={"sub": username, "user_id": user_id, "scopes": scopes or [], "type": "access"},
        secret_key=JWT_SECRET_KEY,
        expires_delta=expires_delta,
        jti=jti
    )
    return token, expire_datetime, jti

def create_refresh_token(user_id: int, username: str, existing_jti: Optional[str] = None) -> tuple[str, datetime, str]:
    """
    Generates a refresh token.
    Returns the token, its expiry time, and its JTI.
    If existing_jti is provided, it uses that as the JTI. Otherwise, generates a new one.
    """
    jti = existing_jti or str(uuid.uuid4())
    expires_delta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    expire_datetime = datetime.now(timezone.utc) + expires_delta
    token = create_jwt_token(
        data={"sub": username, "user_id": user_id, "type": "refresh"}, # No scopes in refresh typically
        secret_key=JWT_REFRESH_SECRET_KEY,
        expires_delta=expires_delta,
        jti=jti
    )
    return token, expire_datetime, jti


def decode_jwt_token(token: str, secret_key: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logging.warning("Token expired.")
        return None
    except jwt.InvalidTokenError as e:
        logging.error(f"Invalid token: {e}")
        return None
    except Exception as e:
        logging.error(f"Error decoding token: {e}")
        return None

# --- Logging Configuration ---
# Basic logging setup. For production, consider structured logging (e.g., JSON).
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler() # Outputs to console
        # Add FileHandler here if you want to log to a file
        # logging.FileHandler("acgs_service.log")
    ]
)

def get_logger(name: str) -> logging.Logger:
    """Returns a logger instance."""
    return logging.getLogger(name)

# --- Decorators ---

def log_execution_time(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to log the execution time of a function (sync or async)."""
    @wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.perf_counter()
        result = await func(*args, **kwargs)
        end_time = time.perf_counter()
        logger = get_logger(func.__module__)
        logger.info(f"Function '{func.__name__}' executed in {end_time - start_time:.4f} seconds.")
        return result

    @wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        logger = get_logger(func.__module__)
        logger.info(f"Function '{func.__name__}' executed in {end_time - start_time:.4f} seconds.")
        return result

    if isinstance(func, Coroutine): # Check if it's an async function
         return async_wrapper
    else: # It's a sync function
        return sync_wrapper


def handle_validation_errors(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to catch Pydantic ValidationErrors and log them."""
    @wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)
        except ValidationError as e:
            logger = get_logger(func.__module__)
            logger.error(f"Validation error in '{func.__name__}': {e.errors()}")
            # Depending on the framework, you might re-raise a specific HTTP error here
            raise # Or return a specific error response
        except Exception as e:
            logger = get_logger(func.__module__)
            logger.error(f"Unexpected error in '{func.__name__}': {e}")
            raise

    @wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            logger = get_logger(func.__module__)
            logger.error(f"Validation error in '{func.__name__}': {e.errors()}")
            raise
        except Exception as e:
            logger = get_logger(func.__module__)
            logger.error(f"Unexpected error in '{func.__name__}': {e}")
            raise

    if isinstance(func, Coroutine):
        return async_wrapper
    else:
        return sync_wrapper

# --- Unique ID Generation ---

def generate_unique_id(prefix: Optional[str] = None) -> str:
    """Generates a UUID v4 string, optionally prefixed."""
    uid = str(uuid.uuid4())
    if prefix:
        return f"{prefix}_{uid}"
    return uid

# --- Date/Time Utilities ---

def get_current_utc_timestamp() -> datetime:
    """Returns the current UTC timestamp."""
    return datetime.now(timezone.utc)

def format_datetime_iso(dt: datetime) -> str:
    """Formats a datetime object to ISO 8601 string."""
    return dt.isoformat()

def parse_iso_datetime(dt_str: str) -> Optional[datetime]:
    """Parses an ISO 8601 string to a datetime object."""
    try:
        return datetime.fromisoformat(dt_str)
    except (ValueError, TypeError):
        return None

# Example of a more complex utility, e.g., for pagination or query building
# This is a placeholder, actual implementation would depend on DB and ORM
def build_query_filters(params: dict, allowed_filters: list[str]) -> dict:
    """
    Constructs a dictionary of filters based on allowed parameters.
    (Very basic example)
    """
    filters = {}
    for key, value in params.items():
        if key in allowed_filters and value is not None:
            filters[key] = value
    return filters

if __name__ == "__main__":
    # Example usage of some utilities
    logger = get_logger(__name__)
    logger.info("Testing shared utilities...")

    # Password Hashing
    password = "securepassword123"
    hashed_password = get_password_hash(password)
    logger.info(f"Original password: {password}")
    logger.info(f"Hashed password: {hashed_password}")
    logger.info(f"Password verification: {verify_password(password, hashed_password)}")

    # JWT Tokens
    user_data = {"user_id": 123, "username": "testuser", "scopes": ["read", "write"]}
    
    access_token, access_exp, access_jti = create_access_token(user_id=user_data["user_id"], username=user_data["username"], scopes=user_data["scopes"])
    logger.info(f"Access Token (JTI: {access_jti}): {access_token}, Expires: {access_exp.isoformat()}")
    
    refresh_token, refresh_exp, refresh_jti = create_refresh_token(user_id=user_data["user_id"], username=user_data["username"])
    logger.info(f"Refresh Token (JTI: {refresh_jti}): {refresh_token}, Expires: {refresh_exp.isoformat()}")

    decoded_access = decode_jwt_token(access_token, JWT_SECRET_KEY)
    logger.info(f"Decoded Access Token: {decoded_access}")

    decoded_refresh = decode_jwt_token(refresh_token, JWT_REFRESH_SECRET_KEY)
    logger.info(f"Decoded Refresh Token: {decoded_refresh}")

    # Unique ID
    logger.info(f"Generated Unique ID: {generate_unique_id()}")
    logger.info(f"Generated Prefixed Unique ID: {generate_unique_id(prefix='user')}")

    # Datetime
    now_utc = get_current_utc_timestamp()
    logger.info(f"Current UTC Timestamp: {format_datetime_iso(now_utc)}")

    # Example of logging decorator
    @log_execution_time
    def example_sync_function(delay: float):
        time.sleep(delay)
        return f"Sync function completed after {delay}s"

    @log_execution_time
    async def example_async_function(delay: float):
        import asyncio
        await asyncio.sleep(delay)
        return f"Async function completed after {delay}s"

    logger.info(example_sync_function(0.1))
    # For async, you'd typically run it within an event loop
    # import asyncio
    # asyncio.run(example_async_function(0.1))

    logger.info("Utility tests finished.")
