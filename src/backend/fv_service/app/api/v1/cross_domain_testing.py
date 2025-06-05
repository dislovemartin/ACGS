"""
Cross-Domain Principle Testing API endpoints for ACGS-PGP Task 13

Provides REST API for cross-domain principle testing framework including:
- Domain context management
- Test scenario configuration
- Cross-domain testing execution
- Results analysis and reporting
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from shared.database import get_async_db
from shared.models import DomainContext, CrossDomainTestScenario, CrossDomainTestResult, Principle
from app.core.auth import require_verification_triggerer, User
from app.core.cross_domain_testing_engine import cross_domain_testing_engine
from app.services.ac_client import ac_service_client
from app.schemas import (
    DomainContextCreate, DomainContextUpdate, DomainContext as DomainContextSchema,
    CrossDomainTestScenarioCreate, CrossDomainTestScenarioUpdate, CrossDomainTestScenario as CrossDomainTestScenarioSchema,
    CrossDomainTestRequest, CrossDomainTestResponse, CrossDomainTestResult as CrossDomainTestResultSchema
)

logger = logging.getLogger(__name__)
router = APIRouter()

# --- Domain Context Management Endpoints ---

@router.post("/domains", response_model=DomainContextSchema, status_code=status.HTTP_201_CREATED)
async def create_domain_context(
    domain_data: DomainContextCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_verification_triggerer)
):
    """Create a new domain context for cross-domain testing."""
    
    try:
        # Check if domain already exists
        existing_domain = await db.execute(
            select(DomainContext).where(DomainContext.domain_name == domain_data.domain_name)
        )
        if existing_domain.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail=f"Domain context '{domain_data.domain_name}' already exists"
            )
        
        # Create new domain context
        domain_context = DomainContext(
            domain_name=domain_data.domain_name,
            domain_description=domain_data.domain_description,
            regulatory_frameworks=domain_data.regulatory_frameworks,
            compliance_requirements=domain_data.compliance_requirements,
            cultural_contexts=domain_data.cultural_contexts,
            domain_constraints=domain_data.domain_constraints,
            risk_factors=domain_data.risk_factors,
            stakeholder_groups=domain_data.stakeholder_groups,
            created_by_user_id=current_user.id,
            is_active=True
        )
        
        db.add(domain_context)
        await db.commit()
        await db.refresh(domain_context)
        
        logger.info(f"Created domain context '{domain_data.domain_name}' with ID {domain_context.id}")
        
        return domain_context
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create domain context: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create domain context: {str(e)}")


@router.get("/domains", response_model=List[DomainContextSchema])
async def list_domain_contexts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_async_db)
):
    """List all domain contexts."""
    
    try:
        query = select(DomainContext)
        
        if active_only:
            query = query.where(DomainContext.is_active == True)
        
        query = query.offset(skip).limit(limit).order_by(DomainContext.created_at.desc())
        
        result = await db.execute(query)
        domains = result.scalars().all()
        
        return domains
        
    except Exception as e:
        logger.error(f"Failed to list domain contexts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list domain contexts: {str(e)}")


@router.get("/domains/{domain_id}", response_model=DomainContextSchema)
async def get_domain_context(
    domain_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """Get a specific domain context by ID."""
    
    try:
        result = await db.execute(select(DomainContext).where(DomainContext.id == domain_id))
        domain = result.scalar_one_or_none()
        
        if not domain:
            raise HTTPException(status_code=404, detail=f"Domain context {domain_id} not found")
        
        return domain
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get domain context {domain_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get domain context: {str(e)}")


@router.put("/domains/{domain_id}", response_model=DomainContextSchema)
async def update_domain_context(
    domain_id: int,
    domain_data: DomainContextUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_verification_triggerer)
):
    """Update a domain context."""
    
    try:
        result = await db.execute(select(DomainContext).where(DomainContext.id == domain_id))
        domain = result.scalar_one_or_none()
        
        if not domain:
            raise HTTPException(status_code=404, detail=f"Domain context {domain_id} not found")
        
        # Update fields
        update_data = domain_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(domain, field, value)
        
        domain.updated_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(domain)
        
        logger.info(f"Updated domain context {domain_id}")
        
        return domain
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update domain context {domain_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update domain context: {str(e)}")


# --- Test Scenario Management Endpoints ---

@router.post("/scenarios", response_model=CrossDomainTestScenarioSchema, status_code=status.HTTP_201_CREATED)
async def create_test_scenario(
    scenario_data: CrossDomainTestScenarioCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_verification_triggerer)
):
    """Create a new cross-domain test scenario."""
    
    try:
        # Validate primary domain exists
        domain_result = await db.execute(
            select(DomainContext).where(DomainContext.id == scenario_data.primary_domain_id)
        )
        if not domain_result.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail=f"Primary domain {scenario_data.primary_domain_id} not found"
            )
        
        # Validate principle IDs exist (simplified check)
        if not scenario_data.principle_ids:
            raise HTTPException(status_code=400, detail="At least one principle ID is required")
        
        # Create test scenario
        scenario = CrossDomainTestScenario(
            scenario_name=scenario_data.scenario_name,
            scenario_description=scenario_data.scenario_description,
            primary_domain_id=scenario_data.primary_domain_id,
            secondary_domains=scenario_data.secondary_domains,
            test_type=scenario_data.test_type,
            test_parameters=scenario_data.test_parameters,
            expected_outcomes=scenario_data.expected_outcomes,
            principle_ids=scenario_data.principle_ids,
            principle_adaptations=scenario_data.principle_adaptations,
            status="pending",
            created_by_user_id=current_user.id
        )
        
        db.add(scenario)
        await db.commit()
        await db.refresh(scenario)
        
        logger.info(f"Created test scenario '{scenario_data.scenario_name}' with ID {scenario.id}")
        
        return scenario
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create test scenario: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create test scenario: {str(e)}")


@router.get("/scenarios", response_model=List[CrossDomainTestScenarioSchema])
async def list_test_scenarios(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[str] = Query(None),
    domain_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_async_db)
):
    """List cross-domain test scenarios."""
    
    try:
        query = select(CrossDomainTestScenario)
        
        if status_filter:
            query = query.where(CrossDomainTestScenario.status == status_filter)
        
        if domain_id:
            query = query.where(CrossDomainTestScenario.primary_domain_id == domain_id)
        
        query = query.offset(skip).limit(limit).order_by(CrossDomainTestScenario.created_at.desc())
        
        result = await db.execute(query)
        scenarios = result.scalars().all()
        
        return scenarios
        
    except Exception as e:
        logger.error(f"Failed to list test scenarios: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list test scenarios: {str(e)}")


@router.get("/scenarios/{scenario_id}", response_model=CrossDomainTestScenarioSchema)
async def get_test_scenario(
    scenario_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """Get a specific test scenario by ID."""
    
    try:
        result = await db.execute(
            select(CrossDomainTestScenario).where(CrossDomainTestScenario.id == scenario_id)
        )
        scenario = result.scalar_one_or_none()
        
        if not scenario:
            raise HTTPException(status_code=404, detail=f"Test scenario {scenario_id} not found")
        
        return scenario
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get test scenario {scenario_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get test scenario: {str(e)}")


# --- Cross-Domain Testing Execution Endpoints ---

@router.post("/execute", response_model=CrossDomainTestResponse)
async def execute_cross_domain_test(
    test_request: CrossDomainTestRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_verification_triggerer)
):
    """Execute cross-domain principle testing."""
    
    try:
        logger.info(f"Starting cross-domain test execution for {len(test_request.scenario_ids)} scenarios")
        
        # Fetch test scenarios
        scenarios_result = await db.execute(
            select(CrossDomainTestScenario).where(
                CrossDomainTestScenario.id.in_(test_request.scenario_ids)
            )
        )
        scenarios = scenarios_result.scalars().all()
        
        if len(scenarios) != len(test_request.scenario_ids):
            missing_ids = set(test_request.scenario_ids) - {s.id for s in scenarios}
            raise HTTPException(
                status_code=400,
                detail=f"Test scenarios not found: {missing_ids}"
            )
        
        # Fetch all relevant domains
        domain_ids = set()
        for scenario in scenarios:
            domain_ids.add(scenario.primary_domain_id)
            if scenario.secondary_domains:
                domain_ids.update(scenario.secondary_domains)
        
        domains_result = await db.execute(
            select(DomainContext).where(DomainContext.id.in_(domain_ids))
        )
        domains = domains_result.scalars().all()
        
        # Fetch all relevant principles from AC service
        principle_ids = set()
        for scenario in scenarios:
            principle_ids.update(scenario.principle_ids)
        
        # Get principles from AC service
        principles = []
        for principle_id in principle_ids:
            try:
                principle = await ac_service_client.get_principle(principle_id)
                principles.append(principle)
            except Exception as e:
                logger.warning(f"Failed to fetch principle {principle_id}: {str(e)}")
        
        # Execute cross-domain testing
        response = await cross_domain_testing_engine.execute_cross_domain_test(
            test_request, scenarios, domains, principles
        )
        
        # Store results in database
        for result in response.results:
            db_result = CrossDomainTestResult(
                scenario_id=result.scenario_id,
                test_run_id=result.test_run_id,
                domain_id=result.domain_id,
                principle_id=result.principle_id,
                test_type=result.test_type,
                is_consistent=result.is_consistent,
                consistency_score=result.consistency_score,
                adaptation_required=result.adaptation_required,
                adaptation_suggestions=result.adaptation_suggestions,
                validation_details=result.validation_details,
                conflict_detected=result.conflict_detected,
                conflict_details=result.conflict_details,
                execution_time_ms=result.execution_time_ms,
                memory_usage_mb=result.memory_usage_mb,
                executed_by_user_id=current_user.id
            )
            db.add(db_result)
        
        # Update scenario statuses
        for scenario in scenarios:
            scenario.status = "completed"
            scenario.last_run_at = datetime.now(timezone.utc)
            scenario.accuracy_score = response.overall_accuracy
            scenario.consistency_score = response.overall_consistency
        
        await db.commit()
        
        logger.info(f"Completed cross-domain test execution: {response.test_run_id}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to execute cross-domain test: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to execute cross-domain test: {str(e)}")


@router.get("/results/{test_run_id}", response_model=List[CrossDomainTestResultSchema])
async def get_test_results(
    test_run_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """Get test results for a specific test run."""
    
    try:
        result = await db.execute(
            select(CrossDomainTestResult).where(
                CrossDomainTestResult.test_run_id == test_run_id
            ).order_by(CrossDomainTestResult.executed_at.desc())
        )
        results = result.scalars().all()
        
        if not results:
            raise HTTPException(status_code=404, detail=f"No results found for test run {test_run_id}")
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get test results for {test_run_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get test results: {str(e)}")


@router.get("/results/scenario/{scenario_id}", response_model=List[CrossDomainTestResultSchema])
async def get_scenario_results(
    scenario_id: int,
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_async_db)
):
    """Get test results for a specific scenario."""
    
    try:
        result = await db.execute(
            select(CrossDomainTestResult).where(
                CrossDomainTestResult.scenario_id == scenario_id
            ).order_by(CrossDomainTestResult.executed_at.desc()).limit(limit)
        )
        results = result.scalars().all()
        
        return results
        
    except Exception as e:
        logger.error(f"Failed to get scenario results for {scenario_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get scenario results: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint for cross-domain testing service."""
    return {
        "status": "healthy",
        "service": "cross_domain_testing",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
