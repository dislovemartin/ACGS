import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from shared.database import Base # Import the shared Base from top-level shared

# Association table for User and Role many-to-many relationship
user_roles_table = Table('auth_user_roles', Base.metadata,
    Column('user_id', Integer, ForeignKey('auth_users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('auth_roles.id'), primary_key=True)
)

# Association table for Role and Permission many-to-many relationship
role_permissions_table = Table('auth_role_permissions', Base.metadata,
    Column('role_id', Integer, ForeignKey('auth_roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('auth_permissions.id'), primary_key=True)
)

class Permission(Base):
    __tablename__ = "auth_permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)  # e.g., "articles:create", "users:read_all"
    description = Column(String(255))
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    roles = relationship("Role", secondary=role_permissions_table, back_populates="permissions")

    def __repr__(self):
        return f"<Permission(id={self.id}, name='{self.name}')>"

class User(Base):
    __tablename__ = "auth_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    # Constitutional Council membership
    is_constitutional_council_member = Column(Boolean, default=False, nullable=False)
    constitutional_council_appointed_at = Column(DateTime, nullable=True)
    constitutional_council_term_expires = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime)

    roles = relationship("Role", secondary=user_roles_table, back_populates="users")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role"""
        return any(role.name == role_name for role in self.roles)

    def has_permission(self, permission_name: str) -> bool:
        """Check if user has a specific permission through their roles"""
        for role in self.roles:
            if any(perm.name == permission_name for perm in role.permissions):
                return True
        return False

    def is_constitutional_council_active(self) -> bool:
        """Check if user is an active Constitutional Council member"""
        if not self.is_constitutional_council_member:
            return False
        if self.constitutional_council_term_expires:
            return datetime.datetime.utcnow() < self.constitutional_council_term_expires
        return True

class Role(Base):
    __tablename__ = "auth_roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(80), unique=True, nullable=False, index=True)
    description = Column(String(255))
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    users = relationship("User", secondary=user_roles_table, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions_table, back_populates="roles")

    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}')>"

# Token Blacklist for JWT revocation
class TokenBlacklist(Base):
    __tablename__ = "auth_token_blacklist"

    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String(36), unique=True, nullable=False, index=True)  # JWT ID (unique identifier for the token)
    token_type = Column(String(50), nullable=False) # e.g., 'access_token', 'refresh_token'
    user_id = Column(Integer, ForeignKey('auth_users.id'), nullable=False)
    expires_at = Column(DateTime, nullable=False) # The original expiry time of the token
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    user = relationship("User")

    def __repr__(self):
        return f"<TokenBlacklist(jti='{self.jti}', user_id={self.user_id})>"
