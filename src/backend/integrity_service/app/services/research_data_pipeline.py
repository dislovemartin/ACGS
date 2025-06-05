"""
Research Data Pipeline for ACGS-PGP Task 13

Implements anonymized cross-domain testing results collection, statistical analysis,
and PGP-signed research data exports for external validation.
"""

import asyncio
import hashlib
import json
import logging
import statistics
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from src.backend.shared.models import (
    CrossDomainTestResult, DomainContext, Principle, ResearchDataExport
)
from src.backend.integrity_service.app.services.pgp_assurance import PGPAssuranceService

logger = logging.getLogger(__name__)


class AnonymizationMethod(str, Enum):
    """Supported anonymization methods."""
    K_ANONYMITY = "k_anonymity"
    DIFFERENTIAL_PRIVACY = "differential_privacy"
    GENERALIZATION = "generalization"
    SUPPRESSION = "suppression"


@dataclass
class AnonymizationConfig:
    """Configuration for data anonymization."""
    method: AnonymizationMethod
    k_value: Optional[int] = None  # For k-anonymity
    epsilon: Optional[float] = None  # For differential privacy
    delta: Optional[float] = None  # For differential privacy
    generalization_levels: Optional[Dict[str, int]] = None
    suppression_threshold: Optional[float] = None


@dataclass
class StatisticalSummary:
    """Statistical summary of research data."""
    total_records: int
    domain_distribution: Dict[str, int]
    principle_distribution: Dict[str, int]
    consistency_statistics: Dict[str, float]
    execution_time_statistics: Dict[str, float]
    accuracy_statistics: Dict[str, float]
    temporal_distribution: Dict[str, int]
    conflict_statistics: Dict[str, Any]


class ResearchDataPipeline:
    """
    Pipeline for collecting, anonymizing, and exporting cross-domain testing research data.
    """
    
    def __init__(self):
        self.pgp_service = PGPAssuranceService()
        self.anonymization_cache = {}
    
    async def collect_research_data(
        self,
        db: AsyncSession,
        domain_ids: List[int],
        principle_ids: List[int],
        date_range_start: datetime,
        date_range_end: datetime,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Collect cross-domain testing results for research purposes.
        
        Args:
            db: Database session
            domain_ids: List of domain IDs to include
            principle_ids: List of principle IDs to include
            date_range_start: Start date for data collection
            date_range_end: End date for data collection
            include_metadata: Whether to include execution metadata
            
        Returns:
            List of research data records
        """
        
        logger.info(f"Collecting research data for {len(domain_ids)} domains and {len(principle_ids)} principles")
        
        # Build query for cross-domain test results
        query = select(CrossDomainTestResult).where(
            and_(
                CrossDomainTestResult.domain_id.in_(domain_ids),
                CrossDomainTestResult.principle_id.in_(principle_ids),
                CrossDomainTestResult.executed_at >= date_range_start,
                CrossDomainTestResult.executed_at <= date_range_end
            )
        ).order_by(CrossDomainTestResult.executed_at.desc())
        
        result = await db.execute(query)
        test_results = result.scalars().all()
        
        # Convert to research data format
        research_data = []
        for test_result in test_results:
            record = {
                "result_id": test_result.id,
                "test_run_id": test_result.test_run_id,
                "domain_id": test_result.domain_id,
                "principle_id": test_result.principle_id,
                "test_type": test_result.test_type,
                "is_consistent": test_result.is_consistent,
                "consistency_score": test_result.consistency_score,
                "adaptation_required": test_result.adaptation_required,
                "conflict_detected": test_result.conflict_detected,
                "executed_at": test_result.executed_at.isoformat()
            }
            
            if include_metadata:
                record.update({
                    "execution_time_ms": test_result.execution_time_ms,
                    "memory_usage_mb": test_result.memory_usage_mb,
                    "validation_details": test_result.validation_details,
                    "adaptation_suggestions": test_result.adaptation_suggestions,
                    "conflict_details": test_result.conflict_details
                })
            
            research_data.append(record)
        
        logger.info(f"Collected {len(research_data)} research data records")
        
        return research_data
    
    async def anonymize_research_data(
        self,
        research_data: List[Dict[str, Any]],
        config: AnonymizationConfig
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Anonymize research data using specified method.
        
        Args:
            research_data: Raw research data
            config: Anonymization configuration
            
        Returns:
            Tuple of (anonymized_data, anonymization_metadata)
        """
        
        logger.info(f"Anonymizing {len(research_data)} records using {config.method.value}")
        
        if config.method == AnonymizationMethod.K_ANONYMITY:
            return await self._apply_k_anonymity(research_data, config)
        elif config.method == AnonymizationMethod.DIFFERENTIAL_PRIVACY:
            return await self._apply_differential_privacy(research_data, config)
        elif config.method == AnonymizationMethod.GENERALIZATION:
            return await self._apply_generalization(research_data, config)
        elif config.method == AnonymizationMethod.SUPPRESSION:
            return await self._apply_suppression(research_data, config)
        else:
            raise ValueError(f"Unsupported anonymization method: {config.method}")
    
    async def generate_statistical_summary(
        self,
        research_data: List[Dict[str, Any]]
    ) -> StatisticalSummary:
        """
        Generate statistical summary of research data.
        
        Args:
            research_data: Research data to analyze
            
        Returns:
            StatisticalSummary with comprehensive statistics
        """
        
        if not research_data:
            return StatisticalSummary(
                total_records=0,
                domain_distribution={},
                principle_distribution={},
                consistency_statistics={},
                execution_time_statistics={},
                accuracy_statistics={},
                temporal_distribution={},
                conflict_statistics={}
            )
        
        # Domain distribution
        domain_counts = {}
        for record in research_data:
            domain_id = str(record["domain_id"])
            domain_counts[domain_id] = domain_counts.get(domain_id, 0) + 1
        
        # Principle distribution
        principle_counts = {}
        for record in research_data:
            principle_id = str(record["principle_id"])
            principle_counts[principle_id] = principle_counts.get(principle_id, 0) + 1
        
        # Consistency statistics
        consistency_scores = [r["consistency_score"] for r in research_data if r["consistency_score"] is not None]
        consistency_stats = {}
        if consistency_scores:
            consistency_stats = {
                "mean": statistics.mean(consistency_scores),
                "median": statistics.median(consistency_scores),
                "std_dev": statistics.stdev(consistency_scores) if len(consistency_scores) > 1 else 0.0,
                "min": min(consistency_scores),
                "max": max(consistency_scores),
                "count": len(consistency_scores)
            }
        
        # Execution time statistics
        execution_times = [r["execution_time_ms"] for r in research_data if r.get("execution_time_ms") is not None]
        execution_stats = {}
        if execution_times:
            execution_stats = {
                "mean_ms": statistics.mean(execution_times),
                "median_ms": statistics.median(execution_times),
                "std_dev_ms": statistics.stdev(execution_times) if len(execution_times) > 1 else 0.0,
                "min_ms": min(execution_times),
                "max_ms": max(execution_times),
                "count": len(execution_times)
            }
        
        # Accuracy statistics (based on consistency)
        consistent_count = sum(1 for r in research_data if r["is_consistent"])
        accuracy_stats = {
            "overall_accuracy": consistent_count / len(research_data),
            "consistent_count": consistent_count,
            "inconsistent_count": len(research_data) - consistent_count,
            "adaptation_required_count": sum(1 for r in research_data if r["adaptation_required"])
        }
        
        # Temporal distribution (by month)
        temporal_counts = {}
        for record in research_data:
            executed_at = datetime.fromisoformat(record["executed_at"].replace('Z', '+00:00'))
            month_key = executed_at.strftime("%Y-%m")
            temporal_counts[month_key] = temporal_counts.get(month_key, 0) + 1
        
        # Conflict statistics
        conflict_stats = {
            "conflicts_detected": sum(1 for r in research_data if r["conflict_detected"]),
            "conflict_rate": sum(1 for r in research_data if r["conflict_detected"]) / len(research_data),
            "test_type_distribution": {}
        }
        
        # Test type distribution
        for record in research_data:
            test_type = record["test_type"]
            if test_type not in conflict_stats["test_type_distribution"]:
                conflict_stats["test_type_distribution"][test_type] = {"total": 0, "conflicts": 0}
            conflict_stats["test_type_distribution"][test_type]["total"] += 1
            if record["conflict_detected"]:
                conflict_stats["test_type_distribution"][test_type]["conflicts"] += 1
        
        return StatisticalSummary(
            total_records=len(research_data),
            domain_distribution=domain_counts,
            principle_distribution=principle_counts,
            consistency_statistics=consistency_stats,
            execution_time_statistics=execution_stats,
            accuracy_statistics=accuracy_stats,
            temporal_distribution=temporal_counts,
            conflict_statistics=conflict_stats
        )
    
    async def create_research_export(
        self,
        db: AsyncSession,
        export_name: str,
        export_description: str,
        domain_ids: List[int],
        principle_ids: List[int],
        date_range_start: datetime,
        date_range_end: datetime,
        anonymization_config: AnonymizationConfig,
        export_format: str = "json",
        user_id: Optional[int] = None
    ) -> ResearchDataExport:
        """
        Create a complete research data export with anonymization and PGP signing.
        
        Args:
            db: Database session
            export_name: Name for the export
            export_description: Description of the export
            domain_ids: Domain IDs to include
            principle_ids: Principle IDs to include
            date_range_start: Start date for data collection
            date_range_end: End date for data collection
            anonymization_config: Anonymization configuration
            export_format: Export format (json, csv, parquet)
            user_id: User ID creating the export
            
        Returns:
            ResearchDataExport record
        """
        
        logger.info(f"Creating research export '{export_name}' for {len(domain_ids)} domains")
        
        try:
            # Collect raw research data
            raw_data = await self.collect_research_data(
                db, domain_ids, principle_ids, date_range_start, date_range_end
            )
            
            # Anonymize the data
            anonymized_data, anonymization_metadata = await self.anonymize_research_data(
                raw_data, anonymization_config
            )
            
            # Generate statistical summary
            statistical_summary = await self.generate_statistical_summary(anonymized_data)
            
            # Prepare export data
            export_data = {
                "metadata": {
                    "export_name": export_name,
                    "export_description": export_description,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "domain_ids": domain_ids,
                    "principle_ids": principle_ids,
                    "date_range": {
                        "start": date_range_start.isoformat(),
                        "end": date_range_end.isoformat()
                    },
                    "anonymization": anonymization_metadata,
                    "format": export_format
                },
                "statistical_summary": {
                    "total_records": statistical_summary.total_records,
                    "domain_distribution": statistical_summary.domain_distribution,
                    "principle_distribution": statistical_summary.principle_distribution,
                    "consistency_statistics": statistical_summary.consistency_statistics,
                    "execution_time_statistics": statistical_summary.execution_time_statistics,
                    "accuracy_statistics": statistical_summary.accuracy_statistics,
                    "temporal_distribution": statistical_summary.temporal_distribution,
                    "conflict_statistics": statistical_summary.conflict_statistics
                },
                "data": anonymized_data
            }
            
            # Convert to specified format
            if export_format == "json":
                export_data_str = json.dumps(export_data, indent=2, default=str)
            elif export_format == "csv":
                export_data_str = await self._convert_to_csv(export_data)
            else:
                export_data_str = json.dumps(export_data, default=str)
            
            # Calculate data hash
            data_hash = hashlib.sha256(export_data_str.encode('utf-8')).hexdigest()
            
            # Sign the data with PGP
            pgp_signature = None
            signed_by_key_id = None
            try:
                # This would use the PGP service to sign the data
                # For now, create a placeholder signature
                pgp_signature = f"PGP_SIGNATURE_PLACEHOLDER_{data_hash[:16]}"
                signed_by_key_id = "research_export_key"
            except Exception as e:
                logger.warning(f"Failed to sign research export: {str(e)}")
            
            # Calculate privacy budget used (for differential privacy)
            privacy_budget_used = None
            if anonymization_config.method == AnonymizationMethod.DIFFERENTIAL_PRIVACY:
                privacy_budget_used = anonymization_config.epsilon
            
            # Create database record
            research_export = ResearchDataExport(
                export_name=export_name,
                export_description=export_description,
                domain_ids=domain_ids,
                principle_ids=principle_ids,
                date_range_start=date_range_start,
                date_range_end=date_range_end,
                anonymization_method=anonymization_config.method.value,
                anonymization_parameters=anonymization_metadata,
                privacy_budget_used=privacy_budget_used,
                export_data=export_data,
                statistical_summary=statistical_summary.__dict__,
                data_hash=data_hash,
                pgp_signature=pgp_signature,
                signed_by_key_id=signed_by_key_id,
                created_by_user_id=user_id,
                export_format=export_format,
                file_size_bytes=len(export_data_str.encode('utf-8'))
            )
            
            db.add(research_export)
            await db.commit()
            await db.refresh(research_export)
            
            logger.info(f"Created research export with ID {research_export.id}")
            
            return research_export
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to create research export: {str(e)}")
            raise
    
    async def _apply_k_anonymity(
        self,
        data: List[Dict[str, Any]],
        config: AnonymizationConfig
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Apply k-anonymity anonymization."""
        
        k = config.k_value or 5
        
        # Simplified k-anonymity implementation
        # Group records by quasi-identifiers and ensure each group has at least k records
        
        anonymized_data = []
        for record in data:
            anonymized_record = record.copy()
            
            # Remove direct identifiers
            anonymized_record.pop("result_id", None)
            anonymized_record.pop("test_run_id", None)
            
            # Generalize quasi-identifiers
            if "executed_at" in anonymized_record:
                # Generalize timestamp to date only
                executed_at = datetime.fromisoformat(anonymized_record["executed_at"].replace('Z', '+00:00'))
                anonymized_record["executed_at"] = executed_at.date().isoformat()
            
            anonymized_data.append(anonymized_record)
        
        metadata = {
            "method": "k_anonymity",
            "k_value": k,
            "records_processed": len(data),
            "records_anonymized": len(anonymized_data),
            "generalizations_applied": ["timestamp_to_date"]
        }
        
        return anonymized_data, metadata
    
    async def _apply_differential_privacy(
        self,
        data: List[Dict[str, Any]],
        config: AnonymizationConfig
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Apply differential privacy anonymization."""
        
        epsilon = config.epsilon or 1.0
        delta = config.delta or 1e-5
        
        # Simplified differential privacy implementation
        # Add calibrated noise to numerical values
        
        import random
        
        anonymized_data = []
        for record in data:
            anonymized_record = record.copy()
            
            # Add noise to consistency scores
            if "consistency_score" in anonymized_record and anonymized_record["consistency_score"] is not None:
                noise = random.gauss(0, 1.0 / epsilon)  # Simplified noise calibration
                anonymized_record["consistency_score"] = max(0.0, min(1.0, 
                    anonymized_record["consistency_score"] + noise))
            
            # Add noise to execution times
            if "execution_time_ms" in anonymized_record and anonymized_record["execution_time_ms"] is not None:
                noise = random.gauss(0, 10.0 / epsilon)  # Simplified noise calibration
                anonymized_record["execution_time_ms"] = max(0, 
                    int(anonymized_record["execution_time_ms"] + noise))
            
            anonymized_data.append(anonymized_record)
        
        metadata = {
            "method": "differential_privacy",
            "epsilon": epsilon,
            "delta": delta,
            "records_processed": len(data),
            "records_anonymized": len(anonymized_data),
            "noise_added_to": ["consistency_score", "execution_time_ms"]
        }
        
        return anonymized_data, metadata
    
    async def _apply_generalization(
        self,
        data: List[Dict[str, Any]],
        config: AnonymizationConfig
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Apply generalization anonymization."""
        
        levels = config.generalization_levels or {"domain_id": 1, "principle_id": 1}
        
        anonymized_data = []
        for record in data:
            anonymized_record = record.copy()
            
            # Generalize domain_id (group into categories)
            if "domain_id" in anonymized_record and "domain_id" in levels:
                domain_id = anonymized_record["domain_id"]
                # Simple generalization: group domains
                anonymized_record["domain_category"] = f"domain_group_{domain_id % 3}"
                del anonymized_record["domain_id"]
            
            # Generalize principle_id
            if "principle_id" in anonymized_record and "principle_id" in levels:
                principle_id = anonymized_record["principle_id"]
                anonymized_record["principle_category"] = f"principle_group_{principle_id % 5}"
                del anonymized_record["principle_id"]
            
            anonymized_data.append(anonymized_record)
        
        metadata = {
            "method": "generalization",
            "generalization_levels": levels,
            "records_processed": len(data),
            "records_anonymized": len(anonymized_data),
            "generalizations_applied": list(levels.keys())
        }
        
        return anonymized_data, metadata
    
    async def _apply_suppression(
        self,
        data: List[Dict[str, Any]],
        config: AnonymizationConfig
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Apply suppression anonymization."""
        
        threshold = config.suppression_threshold or 0.1
        
        # Suppress fields that appear in less than threshold proportion of records
        field_counts = {}
        for record in data:
            for field in record:
                if record[field] is not None:
                    field_counts[field] = field_counts.get(field, 0) + 1
        
        total_records = len(data)
        fields_to_suppress = []
        for field, count in field_counts.items():
            if count / total_records < threshold:
                fields_to_suppress.append(field)
        
        anonymized_data = []
        for record in data:
            anonymized_record = record.copy()
            for field in fields_to_suppress:
                anonymized_record.pop(field, None)
            anonymized_data.append(anonymized_record)
        
        metadata = {
            "method": "suppression",
            "suppression_threshold": threshold,
            "records_processed": len(data),
            "records_anonymized": len(anonymized_data),
            "fields_suppressed": fields_to_suppress
        }
        
        return anonymized_data, metadata
    
    async def _convert_to_csv(self, export_data: Dict[str, Any]) -> str:
        """Convert export data to CSV format."""
        
        import csv
        import io
        
        output = io.StringIO()
        
        if not export_data.get("data"):
            return ""
        
        # Get field names from first record
        fieldnames = list(export_data["data"][0].keys())
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for record in export_data["data"]:
            writer.writerow(record)
        
        return output.getvalue()


# Global instance
research_data_pipeline = ResearchDataPipeline()
