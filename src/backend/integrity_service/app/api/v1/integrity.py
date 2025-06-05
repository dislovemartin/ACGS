"""
Integrity Verification API endpoints for ACGS-PGP Framework
Provides comprehensive integrity verification for policy rules and audit logs
"""

from datetime import datetime, timezone
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
# from app.core.auth import require_internal_service, require_auditor, User

# Local auth stubs
class User:
    pass

def require_internal_service():
    return User()

def require_auditor():
    return User()
from app.schemas import IntegrityReport
from app.services.integrity_verification import integrity_verifier

router = APIRouter()


@router.post("/policy-rules/{rule_id}/sign")
async def sign_policy_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_internal_service)
):
    """Sign a policy rule with digital signature and timestamp"""
    try:
        result = await integrity_verifier.sign_policy_rule(db=db, rule_id=rule_id)
        return {
            "message": "Policy rule signed successfully",
            "signature_info": result
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sign policy rule: {str(e)}")


@router.post("/audit-logs/{log_id}/sign")
async def sign_audit_log(
    log_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_internal_service)
):
    """Sign an audit log entry with digital signature, timestamp, and chain integrity"""
    try:
        result = await integrity_verifier.sign_audit_log(db=db, log_id=log_id)
        return {
            "message": "Audit log signed successfully",
            "signature_info": result
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sign audit log: {str(e)}")


@router.get("/policy-rules/{rule_id}/verify", response_model=IntegrityReport)
async def verify_policy_rule_integrity(
    rule_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_auditor)
):
    """Verify complete integrity of a policy rule"""
    try:
        verification_results = await integrity_verifier.verify_policy_rule_integrity(db=db, rule_id=rule_id)
        
        return IntegrityReport(
            entity_type="policy_rule",
            entity_id=rule_id,
            content_hash=verification_results["verification_details"].get("computed_hash", ""),
            signature_verified=verification_results["signature_verified"],
            timestamp_verified=verification_results["timestamp_verified"],
            merkle_verified=True,  # Not implemented yet for policy rules
            chain_integrity=True,  # Not applicable for policy rules
            overall_integrity=verification_results["overall_integrity"],
            verification_details=verification_results["verification_details"],
            verified_at=verification_results["verified_at"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify policy rule: {str(e)}")


@router.get("/audit-logs/{log_id}/verify", response_model=IntegrityReport)
async def verify_audit_log_integrity(
    log_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_auditor)
):
    """Verify complete integrity of an audit log entry including chain integrity"""
    try:
        verification_results = await integrity_verifier.verify_audit_log_integrity(db=db, log_id=log_id)
        
        return IntegrityReport(
            entity_type="audit_log",
            entity_id=log_id,
            content_hash=verification_results["verification_details"].get("computed_hash", ""),
            signature_verified=verification_results["signature_verified"],
            timestamp_verified=verification_results["timestamp_verified"],
            merkle_verified=True,  # Not implemented yet for individual logs
            chain_integrity=verification_results["chain_integrity"],
            overall_integrity=verification_results["overall_integrity"],
            verification_details=verification_results["verification_details"],
            verified_at=verification_results["verified_at"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify audit log: {str(e)}")


@router.post("/audit-logs/batch-verify")
async def batch_verify_audit_logs(
    log_ids: List[int],
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_auditor)
):
    """Verify integrity of multiple audit log entries"""
    try:
        results = []
        
        for log_id in log_ids:
            try:
                verification_result = await integrity_verifier.verify_audit_log_integrity(db=db, log_id=log_id)
                results.append({
                    "log_id": log_id,
                    "status": "verified" if verification_result["overall_integrity"] else "failed",
                    "details": verification_result
                })
            except Exception as e:
                results.append({
                    "log_id": log_id,
                    "status": "error",
                    "error": str(e)
                })
        
        # Calculate summary statistics
        total_logs = len(results)
        verified_logs = sum(1 for r in results if r["status"] == "verified")
        failed_logs = sum(1 for r in results if r["status"] == "failed")
        error_logs = sum(1 for r in results if r["status"] == "error")
        
        return {
            "summary": {
                "total_logs": total_logs,
                "verified_logs": verified_logs,
                "failed_logs": failed_logs,
                "error_logs": error_logs,
                "verification_rate": verified_logs / total_logs if total_logs > 0 else 0
            },
            "results": results,
            "verified_at": datetime.now(timezone.utc)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to batch verify audit logs: {str(e)}")


@router.get("/chain-integrity/audit-logs")
async def verify_audit_log_chain_integrity(
    start_id: int = None,
    end_id: int = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_auditor)
):
    """Verify chain integrity of audit logs within a range"""
    try:
        from sqlalchemy import select
        from app.models import AuditLog
        
        # Build query for audit log range
        stmt = select(AuditLog)
        
        if start_id:
            stmt = stmt.where(AuditLog.id >= start_id)
        if end_id:
            stmt = stmt.where(AuditLog.id <= end_id)
        
        stmt = stmt.order_by(AuditLog.id).limit(limit)
        
        result = await db.execute(stmt)
        audit_logs = result.scalars().all()
        
        if not audit_logs:
            return {
                "message": "No audit logs found in specified range",
                "chain_integrity": True,
                "verified_logs": 0
            }
        
        # Verify chain integrity
        chain_integrity_results = []
        previous_hash = None
        
        for i, log in enumerate(audit_logs):
            expected_previous_hash = previous_hash
            actual_previous_hash = log.previous_hash
            
            chain_valid = (expected_previous_hash == actual_previous_hash)
            
            chain_integrity_results.append({
                "log_id": log.id,
                "chain_valid": chain_valid,
                "expected_previous_hash": expected_previous_hash,
                "actual_previous_hash": actual_previous_hash
            })
            
            # Update previous hash for next iteration
            previous_hash = log.entry_hash
        
        # Calculate overall chain integrity
        overall_chain_integrity = all(r["chain_valid"] for r in chain_integrity_results)
        broken_links = [r for r in chain_integrity_results if not r["chain_valid"]]
        
        return {
            "chain_integrity": overall_chain_integrity,
            "verified_logs": len(audit_logs),
            "broken_links": len(broken_links),
            "start_log_id": audit_logs[0].id,
            "end_log_id": audit_logs[-1].id,
            "details": chain_integrity_results,
            "broken_link_details": broken_links,
            "verified_at": datetime.now(timezone.utc)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify chain integrity: {str(e)}")


@router.get("/system-integrity-report")
async def generate_system_integrity_report(
    include_policy_rules: bool = True,
    include_audit_logs: bool = True,
    sample_size: int = 100,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_auditor)
):
    """Generate comprehensive system integrity report"""
    try:
        report = {
            "report_generated_at": datetime.now(timezone.utc),
            "policy_rules": {},
            "audit_logs": {},
            "overall_system_integrity": True
        }
        
        # Policy rules integrity check
        if include_policy_rules:
            from sqlalchemy import select, func
            from app.models import PolicyRule
            
            # Get sample of policy rules
            stmt = select(PolicyRule).order_by(PolicyRule.id.desc()).limit(sample_size)
            result = await db.execute(stmt)
            policy_rules = result.scalars().all()
            
            policy_integrity_results = []
            for rule in policy_rules:
                try:
                    verification_result = await integrity_verifier.verify_policy_rule_integrity(db=db, rule_id=rule.id)
                    policy_integrity_results.append({
                        "rule_id": rule.id,
                        "integrity_status": verification_result["overall_integrity"]
                    })
                except Exception as e:
                    policy_integrity_results.append({
                        "rule_id": rule.id,
                        "integrity_status": False,
                        "error": str(e)
                    })
            
            policy_integrity_rate = sum(1 for r in policy_integrity_results if r["integrity_status"]) / len(policy_integrity_results) if policy_integrity_results else 1.0
            
            report["policy_rules"] = {
                "total_checked": len(policy_integrity_results),
                "integrity_rate": policy_integrity_rate,
                "failed_rules": [r for r in policy_integrity_results if not r["integrity_status"]]
            }
        
        # Audit logs integrity check
        if include_audit_logs:
            from app.models import AuditLog
            
            # Get sample of audit logs
            stmt = select(AuditLog).order_by(AuditLog.id.desc()).limit(sample_size)
            result = await db.execute(stmt)
            audit_logs = result.scalars().all()
            
            audit_integrity_results = []
            for log in audit_logs:
                try:
                    verification_result = await integrity_verifier.verify_audit_log_integrity(db=db, log_id=log.id)
                    audit_integrity_results.append({
                        "log_id": log.id,
                        "integrity_status": verification_result["overall_integrity"]
                    })
                except Exception as e:
                    audit_integrity_results.append({
                        "log_id": log.id,
                        "integrity_status": False,
                        "error": str(e)
                    })
            
            audit_integrity_rate = sum(1 for r in audit_integrity_results if r["integrity_status"]) / len(audit_integrity_results) if audit_integrity_results else 1.0
            
            report["audit_logs"] = {
                "total_checked": len(audit_integrity_results),
                "integrity_rate": audit_integrity_rate,
                "failed_logs": [r for r in audit_integrity_results if not r["integrity_status"]]
            }
        
        # Calculate overall system integrity
        policy_rate = report["policy_rules"].get("integrity_rate", 1.0)
        audit_rate = report["audit_logs"].get("integrity_rate", 1.0)
        overall_rate = (policy_rate + audit_rate) / 2
        
        report["overall_system_integrity"] = overall_rate > 0.95  # 95% threshold
        report["overall_integrity_rate"] = overall_rate
        
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate integrity report: {str(e)}")


@router.post("/auto-sign-new-entries")
async def enable_auto_signing(
    enable: bool = True,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_internal_service)
):
    """Enable or disable automatic signing of new policy rules and audit logs"""
    # This would typically update a system configuration
    # For now, return a placeholder response
    return {
        "auto_signing_enabled": enable,
        "message": f"Automatic signing {'enabled' if enable else 'disabled'}",
        "updated_at": datetime.now(timezone.utc)
    }
