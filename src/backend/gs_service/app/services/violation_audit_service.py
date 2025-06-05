"""
violation_audit_service.py

Constitutional Violation Audit Service for comprehensive audit trail management.
Implements violation logging, history tracking, analytics, and compliance reporting
with GDPR/privacy compliance for violation data storage.

Classes:
    ViolationAuditService: Main service for violation audit trail
    AuditEventType: Enumeration of audit event types
    ViolationAnalytics: Analytics data structure
    ComplianceReport: Compliance reporting structure
"""

import asyncio
import logging
import time
import json
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, text
from sqlalchemy.orm import selectinload

from shared.models import (
    ConstitutionalViolation, ViolationAlert, ViolationEscalation,
    AuditLog, User
)
from shared.database import get_async_db

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events for violations."""
    VIOLATION_DETECTED = "violation_detected"
    VIOLATION_ESCALATED = "violation_escalated"
    VIOLATION_RESOLVED = "violation_resolved"
    ALERT_TRIGGERED = "alert_triggered"
    ALERT_ACKNOWLEDGED = "alert_acknowledged"
    THRESHOLD_UPDATED = "threshold_updated"
    MANUAL_INTERVENTION = "manual_intervention"
    SYSTEM_RECOVERY = "system_recovery"


class AnalyticsPeriod(Enum):
    """Time periods for analytics."""
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


@dataclass
class ViolationAnalytics:
    """Analytics data for violations."""
    period: AnalyticsPeriod
    start_time: datetime
    end_time: datetime
    total_violations: int
    violations_by_type: Dict[str, int]
    violations_by_severity: Dict[str, int]
    escalations_count: int
    resolution_rate: float
    average_resolution_time_minutes: float
    top_violation_sources: List[Dict[str, Any]]
    trend_analysis: Dict[str, Any]


@dataclass
class ComplianceReport:
    """Compliance report for violations."""
    report_id: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    total_violations: int
    critical_violations: int
    unresolved_violations: int
    compliance_score: float
    policy_adherence_rate: float
    escalation_effectiveness: float
    recommendations: List[str]
    detailed_metrics: Dict[str, Any]


class ViolationAuditService:
    """
    Constitutional Violation Audit Service.
    
    Provides comprehensive audit trail management, analytics, and compliance
    reporting for constitutional violations with GDPR/privacy compliance.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the violation audit service.
        
        Args:
            config: Configuration dictionary for audit settings
        """
        self.config = config or self._get_default_config()
        
        # Audit configuration
        self.retention_days = self.config.get("retention_days", 2555)  # 7 years default
        self.anonymization_enabled = self.config.get("anonymization_enabled", True)
        self.encryption_enabled = self.config.get("encryption_enabled", True)
        
        logger.info("Violation Audit Service initialized")
    
    async def log_violation_event(
        self,
        event_type: AuditEventType,
        violation: ConstitutionalViolation,
        user: Optional[User] = None,
        additional_data: Optional[Dict[str, Any]] = None,
        db: Optional[AsyncSession] = None
    ) -> str:
        """
        Log a violation-related audit event.
        
        Args:
            event_type: Type of audit event
            violation: Related violation
            user: User who performed the action (if applicable)
            additional_data: Additional event data
            db: Database session
            
        Returns:
            Audit log ID
        """
        if db is None:
            async for db_session in get_async_db():
                return await self.log_violation_event(
                    event_type, violation, user, additional_data, db_session
                )
        
        try:
            # Prepare audit data
            audit_data = {
                "event_type": event_type.value,
                "violation_id": str(violation.id),
                "violation_type": violation.violation_type,
                "severity": violation.severity,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Add user information (with privacy considerations)
            if user:
                audit_data["user_id"] = str(user.id)
                audit_data["user_role"] = user.role
                if not self.anonymization_enabled:
                    audit_data["username"] = user.username
            
            # Add additional data
            if additional_data:
                audit_data.update(additional_data)
            
            # Apply privacy protection
            if self.anonymization_enabled:
                audit_data = self._apply_privacy_protection(audit_data)
            
            # Create audit log entry
            audit_log = AuditLog(
                entity_type="constitutional_violation",
                entity_id=violation.id,
                action=event_type.value,
                changes=audit_data,
                user_id=user.id if user else None
            )
            
            db.add(audit_log)
            await db.commit()
            
            logger.debug(f"Logged violation audit event: {event_type.value} for violation {violation.id}")
            return str(audit_log.id)
            
        except Exception as e:
            logger.error(f"Error logging violation audit event: {e}")
            if db:
                await db.rollback()
            return ""
    
    async def get_violation_history(
        self,
        violation_id: str,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        Get complete audit history for a violation.
        
        Args:
            violation_id: Violation ID
            db: Database session
            
        Returns:
            List of audit events for the violation
        """
        try:
            result = await db.execute(
                select(AuditLog).where(
                    and_(
                        AuditLog.entity_type == "constitutional_violation",
                        AuditLog.entity_id == violation_id
                    )
                ).order_by(desc(AuditLog.created_at))
            )
            
            audit_logs = result.scalars().all()
            
            # Format audit history
            history = []
            for log in audit_logs:
                event = {
                    "id": str(log.id),
                    "action": log.action,
                    "timestamp": log.created_at.isoformat(),
                    "changes": log.changes or {},
                    "user_id": str(log.user_id) if log.user_id else None
                }
                
                # Apply privacy protection for output
                if self.anonymization_enabled:
                    event = self._apply_privacy_protection(event)
                
                history.append(event)
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting violation history: {e}")
            return []
    
    async def generate_analytics(
        self,
        period: AnalyticsPeriod,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        db: Optional[AsyncSession] = None
    ) -> ViolationAnalytics:
        """
        Generate violation analytics for specified period.
        
        Args:
            period: Analytics period
            start_time: Start time (defaults based on period)
            end_time: End time (defaults to now)
            db: Database session
            
        Returns:
            ViolationAnalytics with aggregated data
        """
        if db is None:
            async for db_session in get_async_db():
                return await self.generate_analytics(period, start_time, end_time, db_session)
        
        try:
            # Set default time range
            if end_time is None:
                end_time = datetime.now(timezone.utc)
            
            if start_time is None:
                start_time = self._get_period_start_time(period, end_time)
            
            # Get violation statistics
            violations_result = await db.execute(
                select(ConstitutionalViolation).where(
                    and_(
                        ConstitutionalViolation.detected_at >= start_time,
                        ConstitutionalViolation.detected_at <= end_time
                    )
                )
            )
            violations = violations_result.scalars().all()
            
            # Calculate metrics
            total_violations = len(violations)
            violations_by_type = {}
            violations_by_severity = {}
            resolution_times = []
            
            for violation in violations:
                # Count by type
                violations_by_type[violation.violation_type] = violations_by_type.get(
                    violation.violation_type, 0
                ) + 1
                
                # Count by severity
                violations_by_severity[violation.severity] = violations_by_severity.get(
                    violation.severity, 0
                ) + 1
                
                # Calculate resolution time
                if violation.resolved_at:
                    resolution_time = (violation.resolved_at - violation.detected_at).total_seconds() / 60
                    resolution_times.append(resolution_time)
            
            # Get escalation count
            escalations_result = await db.execute(
                select(func.count(ViolationEscalation.id)).where(
                    and_(
                        ViolationEscalation.escalated_at >= start_time,
                        ViolationEscalation.escalated_at <= end_time
                    )
                )
            )
            escalations_count = escalations_result.scalar() or 0
            
            # Calculate derived metrics
            resolved_count = len(resolution_times)
            resolution_rate = (resolved_count / total_violations * 100) if total_violations > 0 else 0
            avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0
            
            # Get top violation sources (simplified)
            top_sources = await self._get_top_violation_sources(start_time, end_time, db)
            
            # Generate trend analysis
            trend_analysis = await self._generate_trend_analysis(period, start_time, end_time, db)
            
            return ViolationAnalytics(
                period=period,
                start_time=start_time,
                end_time=end_time,
                total_violations=total_violations,
                violations_by_type=violations_by_type,
                violations_by_severity=violations_by_severity,
                escalations_count=escalations_count,
                resolution_rate=resolution_rate,
                average_resolution_time_minutes=avg_resolution_time,
                top_violation_sources=top_sources,
                trend_analysis=trend_analysis
            )
            
        except Exception as e:
            logger.error(f"Error generating violation analytics: {e}")
            return ViolationAnalytics(
                period=period,
                start_time=start_time or datetime.now(timezone.utc),
                end_time=end_time or datetime.now(timezone.utc),
                total_violations=0,
                violations_by_type={},
                violations_by_severity={},
                escalations_count=0,
                resolution_rate=0.0,
                average_resolution_time_minutes=0.0,
                top_violation_sources=[],
                trend_analysis={}
            )
    
    async def generate_compliance_report(
        self,
        start_time: datetime,
        end_time: datetime,
        db: Optional[AsyncSession] = None
    ) -> ComplianceReport:
        """
        Generate compliance report for specified period.
        
        Args:
            start_time: Report start time
            end_time: Report end time
            db: Database session
            
        Returns:
            ComplianceReport with compliance metrics
        """
        if db is None:
            async for db_session in get_async_db():
                return await self.generate_compliance_report(start_time, end_time, db_session)
        
        try:
            # Generate analytics for the period
            analytics = await self.generate_analytics(
                AnalyticsPeriod.DAY, start_time, end_time, db
            )
            
            # Calculate compliance metrics
            critical_violations = analytics.violations_by_severity.get("critical", 0)
            unresolved_violations = await self._count_unresolved_violations(start_time, end_time, db)
            
            # Calculate compliance score (simplified formula)
            compliance_score = max(0, 100 - (critical_violations * 10) - (unresolved_violations * 5))
            compliance_score = min(100, compliance_score)
            
            # Calculate policy adherence rate
            policy_adherence_rate = 100 - (analytics.total_violations / max(1, analytics.total_violations + 100) * 100)
            
            # Calculate escalation effectiveness
            escalation_effectiveness = analytics.resolution_rate
            
            # Generate recommendations
            recommendations = self._generate_compliance_recommendations(analytics, critical_violations)
            
            # Prepare detailed metrics
            detailed_metrics = {
                "total_violations": analytics.total_violations,
                "violations_by_type": analytics.violations_by_type,
                "violations_by_severity": analytics.violations_by_severity,
                "escalations_count": analytics.escalations_count,
                "resolution_rate": analytics.resolution_rate,
                "average_resolution_time": analytics.average_resolution_time_minutes,
                "trend_analysis": analytics.trend_analysis
            }
            
            report_id = f"compliance_report_{int(time.time())}"
            
            return ComplianceReport(
                report_id=report_id,
                generated_at=datetime.now(timezone.utc),
                period_start=start_time,
                period_end=end_time,
                total_violations=analytics.total_violations,
                critical_violations=critical_violations,
                unresolved_violations=unresolved_violations,
                compliance_score=compliance_score,
                policy_adherence_rate=policy_adherence_rate,
                escalation_effectiveness=escalation_effectiveness,
                recommendations=recommendations,
                detailed_metrics=detailed_metrics
            )
            
        except Exception as e:
            logger.error(f"Error generating compliance report: {e}")
            return ComplianceReport(
                report_id=f"error_report_{int(time.time())}",
                generated_at=datetime.now(timezone.utc),
                period_start=start_time,
                period_end=end_time,
                total_violations=0,
                critical_violations=0,
                unresolved_violations=0,
                compliance_score=0.0,
                policy_adherence_rate=0.0,
                escalation_effectiveness=0.0,
                recommendations=["Error generating report - check system logs"],
                detailed_metrics={"error": str(e)}
            )

    async def export_audit_trail(
        self,
        start_time: datetime,
        end_time: datetime,
        format_type: str = "json",
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Export audit trail for compliance reporting.

        Args:
            start_time: Export start time
            end_time: Export end time
            format_type: Export format (json, csv)
            db: Database session

        Returns:
            Exported audit data
        """
        if db is None:
            async for db_session in get_async_db():
                return await self.export_audit_trail(start_time, end_time, format_type, db_session)

        try:
            # Get audit logs for the period
            result = await db.execute(
                select(AuditLog).where(
                    and_(
                        AuditLog.entity_type == "constitutional_violation",
                        AuditLog.created_at >= start_time,
                        AuditLog.created_at <= end_time
                    )
                ).order_by(desc(AuditLog.created_at))
            )

            audit_logs = result.scalars().all()

            # Format export data
            export_data = {
                "export_metadata": {
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "period_start": start_time.isoformat(),
                    "period_end": end_time.isoformat(),
                    "total_records": len(audit_logs),
                    "format": format_type,
                    "privacy_protection_applied": self.anonymization_enabled
                },
                "audit_records": []
            }

            for log in audit_logs:
                record = {
                    "id": str(log.id),
                    "entity_type": log.entity_type,
                    "entity_id": str(log.entity_id),
                    "action": log.action,
                    "timestamp": log.created_at.isoformat(),
                    "changes": log.changes or {},
                    "user_id": str(log.user_id) if log.user_id else None
                }

                # Apply privacy protection
                if self.anonymization_enabled:
                    record = self._apply_privacy_protection(record)

                export_data["audit_records"].append(record)

            return export_data

        except Exception as e:
            logger.error(f"Error exporting audit trail: {e}")
            return {
                "export_metadata": {
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "error": str(e)
                },
                "audit_records": []
            }

    def _apply_privacy_protection(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply privacy protection to audit data."""
        if not self.anonymization_enabled:
            return data

        # Remove or hash sensitive fields
        protected_data = data.copy()

        # Remove direct user identifiers
        if "username" in protected_data:
            del protected_data["username"]

        if "email" in protected_data:
            del protected_data["email"]

        # Hash user IDs for privacy
        if "user_id" in protected_data and protected_data["user_id"]:
            protected_data["user_id_hash"] = hash(protected_data["user_id"])
            del protected_data["user_id"]

        return protected_data

    def _get_period_start_time(self, period: AnalyticsPeriod, end_time: datetime) -> datetime:
        """Get start time for analytics period."""
        if period == AnalyticsPeriod.HOUR:
            return end_time - timedelta(hours=1)
        elif period == AnalyticsPeriod.DAY:
            return end_time - timedelta(days=1)
        elif period == AnalyticsPeriod.WEEK:
            return end_time - timedelta(weeks=1)
        elif period == AnalyticsPeriod.MONTH:
            return end_time - timedelta(days=30)
        elif period == AnalyticsPeriod.QUARTER:
            return end_time - timedelta(days=90)
        elif period == AnalyticsPeriod.YEAR:
            return end_time - timedelta(days=365)
        else:
            return end_time - timedelta(days=1)

    async def _get_top_violation_sources(
        self,
        start_time: datetime,
        end_time: datetime,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Get top sources of violations."""
        try:
            # This is a simplified implementation
            # In practice, would analyze violation sources more comprehensively
            result = await db.execute(
                text("""
                    SELECT violation_type, COUNT(*) as count
                    FROM constitutional_violations
                    WHERE detected_at >= :start_time AND detected_at <= :end_time
                    GROUP BY violation_type
                    ORDER BY count DESC
                    LIMIT 5
                """),
                {"start_time": start_time, "end_time": end_time}
            )

            sources = []
            for row in result:
                sources.append({
                    "source": row.violation_type,
                    "count": row.count,
                    "percentage": 0  # Would calculate based on total
                })

            return sources

        except Exception as e:
            logger.error(f"Error getting top violation sources: {e}")
            return []

    async def _generate_trend_analysis(
        self,
        period: AnalyticsPeriod,
        start_time: datetime,
        end_time: datetime,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Generate trend analysis for violations."""
        try:
            # This is a simplified trend analysis
            # In practice, would use more sophisticated time series analysis

            # Get violation counts by day
            result = await db.execute(
                text("""
                    SELECT DATE(detected_at) as date, COUNT(*) as count
                    FROM constitutional_violations
                    WHERE detected_at >= :start_time AND detected_at <= :end_time
                    GROUP BY DATE(detected_at)
                    ORDER BY date
                """),
                {"start_time": start_time, "end_time": end_time}
            )

            daily_counts = []
            for row in result:
                daily_counts.append({
                    "date": row.date.isoformat(),
                    "count": row.count
                })

            # Calculate trend direction (simplified)
            if len(daily_counts) >= 2:
                recent_avg = sum(d["count"] for d in daily_counts[-3:]) / min(3, len(daily_counts))
                earlier_avg = sum(d["count"] for d in daily_counts[:3]) / min(3, len(daily_counts))

                if recent_avg > earlier_avg * 1.1:
                    trend_direction = "increasing"
                elif recent_avg < earlier_avg * 0.9:
                    trend_direction = "decreasing"
                else:
                    trend_direction = "stable"
            else:
                trend_direction = "insufficient_data"

            return {
                "daily_counts": daily_counts,
                "trend_direction": trend_direction,
                "analysis_period": period.value
            }

        except Exception as e:
            logger.error(f"Error generating trend analysis: {e}")
            return {"error": str(e)}

    async def _count_unresolved_violations(
        self,
        start_time: datetime,
        end_time: datetime,
        db: AsyncSession
    ) -> int:
        """Count unresolved violations in period."""
        try:
            result = await db.execute(
                select(func.count(ConstitutionalViolation.id)).where(
                    and_(
                        ConstitutionalViolation.detected_at >= start_time,
                        ConstitutionalViolation.detected_at <= end_time,
                        ConstitutionalViolation.status != "resolved"
                    )
                )
            )
            return result.scalar() or 0

        except Exception as e:
            logger.error(f"Error counting unresolved violations: {e}")
            return 0

    def _generate_compliance_recommendations(
        self,
        analytics: ViolationAnalytics,
        critical_violations: int
    ) -> List[str]:
        """Generate compliance recommendations based on analytics."""
        recommendations = []

        if critical_violations > 0:
            recommendations.append(
                f"Address {critical_violations} critical violations immediately"
            )

        if analytics.resolution_rate < 80:
            recommendations.append(
                "Improve violation resolution processes - current rate below 80%"
            )

        if analytics.average_resolution_time_minutes > 60:
            recommendations.append(
                "Reduce average resolution time - currently exceeds 1 hour"
            )

        if analytics.escalations_count > analytics.total_violations * 0.3:
            recommendations.append(
                "Review escalation thresholds - high escalation rate detected"
            )

        # Analyze violation types
        if analytics.violations_by_type:
            most_common_type = max(analytics.violations_by_type.items(), key=lambda x: x[1])
            if most_common_type[1] > analytics.total_violations * 0.4:
                recommendations.append(
                    f"Focus on reducing {most_common_type[0]} violations - most common type"
                )

        if not recommendations:
            recommendations.append("System compliance appears satisfactory")

        return recommendations

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for audit service."""
        return {
            "retention_days": 2555,  # 7 years
            "anonymization_enabled": True,
            "encryption_enabled": True,
            "export_formats": ["json", "csv"],
            "max_export_records": 10000,
            "analytics_cache_minutes": 60
        }
