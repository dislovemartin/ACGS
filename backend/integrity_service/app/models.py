from sqlalchemy import Column, Integer, String, Text, DateTime, func, JSON, Index
from sqlalchemy.dialects.postgresql import ARRAY # For PostgreSQL specific ARRAY type
from shared.database import Base
from datetime import datetime

class PolicyRule(Base):
    __tablename__ = "policy_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_content = Column(Text, nullable=False) # Datalog rules
    version = Column(Integer, default=1, nullable=False)
    
    # Storing as JSON array; for PostgreSQL, ARRAY(Integer) could be an alternative
    # source_principle_ids = Column(ARRAY(Integer), nullable=True)
    source_principle_ids = Column(JSON, nullable=True) # e.g., [1, 2, 3]
    
    verification_status = Column(String, default="pending", nullable=False, index=True) # "pending", "verified", "failed"
    verified_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<PolicyRule(id={self.id}, version={self.version}, status='{self.verification_status}')>"

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    service_name = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=True, index=True) # Assuming user ID might be string (e.g., from JWT sub)
    action = Column(String, nullable=False, index=True)
    details = Column(JSON, nullable=True) # Flexible field for event-specific data

    def __repr__(self):
        return f"<AuditLog(id={self.id}, service='{self.service_name}', action='{self.action}', user='{self.user_id}')>"

# Example of a composite index if frequently querying by multiple fields
Index('ix_audit_log_service_action_ts', AuditLog.service_name, AuditLog.action, AuditLog.timestamp)
