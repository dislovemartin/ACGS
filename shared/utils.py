# ACGS/shared/utils.py

import logging
from datetime import datetime, timezone, timedelta
import re
from typing import Optional # Added import

# Setup basic logger
# In a real application, you'd likely use a more sophisticated logging setup,
# possibly configured in each service's main.py or from a central config.
logging.basicConfig(level=logging.INFO) # Consider making level configurable
logger = logging.getLogger("acgs_shared_utils")

def get_utc_now() -> datetime:
    """Returns the current datetime in UTC."""
    return datetime.now(timezone.utc)

def create_timestamp_str(dt_object: Optional[datetime] = None) -> str:
    """Creates a standardized ISO 8601 timestamp string from a datetime object."""
    if dt_object is None:
        dt_object = get_utc_now()
    return dt_object.isoformat()

def parse_timestamp_str(timestamp_str: str) -> Optional[datetime]:
    """Parses an ISO 8601 timestamp string into a datetime object."""
    if not timestamp_str: # Handle empty string case
        return None
    try:
        # More robust parsing for various ISO 8601 formats
        if timestamp_str.endswith("Z"):
            timestamp_str = timestamp_str[:-1] + "+00:00"
        return datetime.fromisoformat(timestamp_str)
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid timestamp format: {timestamp_str}. Error: {e}")
        return None

def calculate_expiration_time(minutes: int) -> datetime:
    """Calculates an expiration datetime from now + minutes in UTC."""
    return get_utc_now() + timedelta(minutes=minutes)

def sanitize_input(text: Optional[str]) -> str: # text can be Optional[str]
    """
    Basic input sanitization.
    Removes potentially harmful characters or sequences.
    This is a very basic example and should be expanded based on specific needs
    and supplemented by context-aware escaping (e.g., HTML escaping, SQL parameterization).
    """
    if not isinstance(text, str): # If text is None or not a string, return empty string
        return ""
    # Remove control characters except for common whitespace like newline, tab, carriage return
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)
    # Add other sanitization rules as needed, e.g., for SQL injection, XSS.
    # However, for SQL, always prefer parameterized queries. For XSS, use templating engines' auto-escaping.
    return text.strip()

def generate_short_id(length: int = 8) -> str:
    """Generates a short, somewhat unique ID. Not cryptographically secure."""
    import random
    import string
    if length <= 0:
        raise ValueError("Length must be a positive integer.")
    characters = string.ascii_lowercase + string.digits
    return "".join(random.choice(characters) for _ in range(length))

class CommonHTTPErrorMessages:
    """Common error messages for HTTP exceptions."""
    NOT_FOUND = "Resource not found."
    UNAUTHORIZED = "Not authorized to access this resource."
    FORBIDDEN = "Access forbidden."
    BAD_REQUEST = "Bad request."
    INTERNAL_SERVER_ERROR = "Internal server error."
    INVALID_CREDENTIALS = "Invalid credentials."
    VALIDATION_ERROR = "Validation error."

# Example utility for pagination (can be expanded)
class Paginator:
    def __init__(self, items: list, page: int = 1, per_page: int = 10):
        if not isinstance(page, int) or page < 1:
            page = 1
        if not isinstance(per_page, int) or per_page < 1:
            per_page = 10
            
        self.items = items
        self.page = page
        self.per_page = per_page
        self.total_items = len(items)
        # Ensure total_pages is at least 1 if there are items, 0 otherwise
        if self.total_items == 0:
            self.total_pages = 0
        else:
            self.total_pages = (self.total_items + self.per_page - 1) // self.per_page
        
        # Adjust page if it's out of bounds after total_pages calculation
        if self.total_items > 0 and self.page > self.total_pages :
            self.page = self.total_pages
        elif self.total_items == 0: # if no items, page should be 1 or 0 depending on convention
            self.page = 1


    def get_page_items(self) -> list:
        if self.total_items == 0:
            return []
        start_index = (self.page - 1) * self.per_page
        end_index = start_index + self.per_page
        return self.items[start_index:end_index]

    def has_next(self) -> bool:
        return self.page < self.total_pages

    def has_prev(self) -> bool:
        return self.page > 1 and self.total_pages > 0 # No prev if on page 1 or no pages

    def get_pagination_details(self) -> dict:
        return {
            "page": self.page,
            "per_page": self.per_page,
            "total_items": self.total_items,
            "total_pages": self.total_pages,
            "has_next": self.has_next(),
            "has_prev": self.has_prev(),
            "items_on_page": len(self.get_page_items())
        }

# You might add more project-specific utilities here.
