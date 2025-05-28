import logging
from passlib.context import CryptContext

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# Add other utility functions as needed
# For example, functions for date/time formatting, data cleaning, etc.

# Example utility for pagination (if you decide to implement it)
# def paginate(query, page: int = 1, page_size: int = 10):
#     return query.offset((page - 1) * page_size).limit(page_size).all()
