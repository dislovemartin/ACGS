# ACGS/shared/security_middleware.py
from fastapi import Request, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from typing import Optional, List, Dict, Any
from jose import JWTError, jwt # Using python-jose for JWT processing
from pydantic import ValidationError

from .schemas import TokenData, User # Assuming User schema for current user
from .utils import JWT_SECRET_KEY, ALGORITHM, decode_jwt_token, get_logger
# This dependency might be circular if User model also imports something from here.
# For current_user, it's more about the data structure (TokenData) than the full User model initially.

logger = get_logger(__name__)

# OAuth2PasswordBearer is a class that you can use to get a token from the request.
# tokenUrl is the URL that the client will use to get the token.
# This URL should correspond to an endpoint in your Authentication service.
# For inter-service communication, this might be less relevant if services use trusted headers
# or a different auth mechanism. However, for user-facing services, it's standard.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False) # auto_error=False to handle missing token manually

class AuthContext:
    """Holds authentication context for the current request."""
    def __init__(
        self,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        is_authenticated: bool = False,
        token: Optional[str] = None,
        token_data: Optional[TokenData] = None,
        error: Optional[str] = None,
    ):
        self.user_id = user_id
        self.username = username
        self.scopes = scopes or []
        self.is_authenticated = is_authenticated
self.token = token
        self.token_data = token_data
        self.error = error

async def get_auth_context(request: Request) -> AuthContext:
    """
    Dependency to extract and validate token, then provide authentication context.
    This can be used by endpoints that require authentication but can also function
    without it (e.g., public data with enhanced features for logged-in users).
    """
    token = request.headers.get("Authorization")
    auth_error: Optional[str] = None
    token_data_obj: Optional[TokenData] = None
    user_id_val: Optional[int] = None
    username_val: Optional[str] = None
    scopes_val: List[str] = []
    is_auth_val: bool = False

    if token:
        if token.startswith("Bearer "):
            token = token.split("Bearer ")[1]
        try:
            payload = decode_jwt_token(token, JWT_SECRET_KEY)
            if payload:
                # Ensure 'sub' (username) and 'user_id' are in the payload
                username_val = payload.get("sub")
                user_id_val = payload.get("user_id")
                scopes_val = payload.get("scopes", [])

                if username_val is None or user_id_val is None:
                    auth_error = "Invalid token: missing username or user_id"
                    logger.warning(f"Auth: {auth_error} in token from {request.client.host}")
                else:
                    try:
                        token_data_obj = TokenData(username=username_val, user_id=user_id_val, scopes=scopes_val, jti=payload.get("jti"))
                        is_auth_val = True
                        logger.info(f"Auth: User {username_val} (ID: {user_id_val}) authenticated with scopes: {scopes_val}")
                    except ValidationError as e:
                        auth_error = f"Invalid token data structure: {e.errors()}"
                        logger.warning(f"Auth: {auth_error} for token from {request.client.host}")
            else:
                # decode_jwt_token already logs expiration or invalidity.
                # auth_error could be "Token expired" or "Invalid token" based on decode_jwt_token's behavior.
                auth_error = "Token is invalid or expired" # Generic message
                logger.warning(f"Auth: {auth_error} for token from {request.client.host}")

        except JWTError as e: # Should be caught by decode_jwt_token, but as a fallback
            auth_error = f"JWT processing error: {str(e)}"
            logger.error(f"Auth: {auth_error} for token from {request.client.host}")
        except Exception as e: # Catch unexpected errors
            auth_error = f"Unexpected authentication error: {str(e)}"
            logger.exception(f"Auth: {auth_error} for token from {request.client.host}")
    else:
        auth_error = "Authorization header missing or token not provided"
        # This is not necessarily an error for optional authentication, so log level might be INFO or DEBUG
        # logger.debug(f"Auth: No token provided from {request.client.host}")

    return AuthContext(
        user_id=user_id_val,
        username=username_val,
        scopes=scopes_val,
        is_authenticated=is_auth_val,
        token=token,
        token_data=token_data_obj,
        error=auth_error if not is_auth_val else None
    )


async def get_current_user(
    security_scopes: SecurityScopes, # FastAPI's way to handle required scopes
    auth_context: AuthContext = Depends(get_auth_context),
) -> TokenData:
    """
    FastAPI dependency to get the current authenticated user's token data.
    Raises HTTPException if authentication fails or scopes are not met.
    This is for endpoints that STRICTLY require authentication.
    """
    if not auth_context.is_authenticated or not auth_context.token_data:
        credential_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=auth_context.error or "Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
        logger.warning(f"GetCurrentUser: Authentication failed. Detail: {credential_exception.detail}")
        raise credential_exception

    # Check scopes
    if security_scopes.scopes: # If specific scopes are required for the endpoint
        authenticated_scopes = set(auth_context.scopes)
        required_scopes = set(security_scopes.scopes)
        if not required_scopes.issubset(authenticated_scopes):
            scope_exception = HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Required scopes: {', '.join(required_scopes)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
            logger.warning(f"GetCurrentUser: User {auth_context.username} missing scopes. Required: {required_scopes}, Has: {authenticated_scopes}")
            raise scope_exception

    logger.info(f"GetCurrentUser: User {auth_context.username} (ID: {auth_context.user_id}) authorized for scopes: {security_scopes.scopes or 'any'}")
    return auth_context.token_data


async def get_optional_current_user(
    auth_context: AuthContext = Depends(get_auth_context),
) -> Optional[TokenData]:
    """
    FastAPI dependency to get the current user's token data if authenticated,
    but does not raise an error if not. Allows for optional authentication.
    """
    if auth_context.is_authenticated and auth_context.token_data:
        logger.info(f"GetOptionalCurrentUser: User {auth_context.username} (ID: {auth_context.user_id}) is authenticated.")
        return auth_context.token_data
    logger.info("GetOptionalCurrentUser: No authenticated user or invalid token.")
    return None


# Example of a more specific permission dependency
async def require_admin_user(current_user: TokenData = Depends(get_current_user)):
    """
    Dependency to ensure the current user has an 'admin' scope.
    Relies on get_current_user to handle authentication first.
    """
    # Note: 'get_current_user' already checks for general authentication.
    # This adds a specific scope check on top.
    # To make 'admin' a required scope for get_current_user directly, you would do:
    # Depends(get_current_user_with_scopes(["admin"])) where get_current_user_with_scopes is
    # a factory or SecurityScopes is used directly in the endpoint.
    # For simplicity here, we check the scope after `get_current_user`.

    # This check is somewhat redundant if `SecurityScopes(["admin"])` is used with `get_current_user`.
    # However, it demonstrates how custom permission checks can be built.
    if "admin" not in current_user.scopes:
        logger.warning(f"RequireAdminUser: User {current_user.username} attempted admin action without 'admin' scope.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have admin privileges.",
        )
    logger.info(f"RequireAdminUser: User {current_user.username} authorized as admin.")
    return current_user


# This is a simplified way to use SecurityScopes directly in endpoint.
# from fastapi import Security
# @app.get("/users/me", response_model=UserSchema)
# async def read_users_me(current_user: UserSchema = Security(get_current_user, scopes=["users:me"])):
#     return current_user

# A more robust way to handle user loading from DB if full user object is needed:
# async def get_current_active_user(current_user_token: TokenData = Depends(get_current_user),
#                                   db: AsyncSession = Depends(get_async_db)) -> User: # Assuming User is your SQLAlchemy model
#     # Here you would query your database using current_user_token.user_id or username
#     # user = await db.get(User, current_user_token.user_id)
#     # if not user or not user.is_active:
#     #     raise HTTPException(status_code=400, detail="Inactive user or user not found")
#     # return user
#     # This requires User model and get_async_db to be defined and accessible.
#     # For shared middleware, it's often better to return TokenData and let services fetch user details if needed.
    pass

# Note: The actual User model/schema might come from the Authentication service's client library
# or a shared schema definition if services are tightly coupled.
# For now, TokenData is the primary output of authentication.
