#!/usr/bin/env python3
"""
Test script for Stakeholder Engagement System

This script tests the stakeholder engagement system functionality
including notification dispatch, feedback collection, and real-time updates.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timezone

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from shared.database import Base
from shared.models import User
from app.models import ACAmendment
from app.services.stakeholder_engagement import (
    StakeholderNotificationService,
    StakeholderEngagementInput,
    NotificationChannel,
    StakeholderRole
)
from shared.langgraph_config import ConstitutionalCouncilConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test database URL (in-memory SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

async def create_test_database():
    """Create test database and tables."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    return engine

async def create_test_data(db: AsyncSession):
    """Create test users and amendment data."""
    # Create test users with stakeholder roles
    test_users = [
        User(
            id=1,
            username="constitutional_expert_1",
            email="expert1@acgs-pgp.org",
            hashed_password="hashed_password",
            role="constitutional_expert",
            is_active=True
        ),
        User(
            id=2,
            username="policy_admin_1",
            email="admin1@acgs-pgp.org",
            hashed_password="hashed_password",
            role="policy_administrator",
            is_active=True
        ),
        User(
            id=3,
            username="system_auditor_1",
            email="auditor1@acgs-pgp.org",
            hashed_password="hashed_password",
            role="system_auditor",
            is_active=True
        ),
        User(
            id=4,
            username="public_rep_1",
            email="public1@acgs-pgp.org",
            hashed_password="hashed_password",
            role="public_representative",
            is_active=True
        )
    ]
    
    for user in test_users:
        db.add(user)
    
    # Create test amendment
    test_amendment = ACAmendment(
        id=1,
        principle_id=1,
        title="Test Constitutional Amendment",
        description="A test amendment for stakeholder engagement testing",
        amendment_type="modify",
        proposed_changes="Update principle to include new requirements",
        justification="Testing stakeholder engagement system",
        status="proposed",
        proposed_by_user_id=1,
        created_at=datetime.now(timezone.utc)
    )
    
    db.add(test_amendment)
    await db.commit()
    
    logger.info("Test data created successfully")
    return test_users, test_amendment

async def test_stakeholder_engagement():
    """Test the stakeholder engagement system."""
    logger.info("Starting stakeholder engagement system test")
    
    # Create test database
    engine = await create_test_database()
    
    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as db:
        # Create test data
        test_users, test_amendment = await create_test_data(db)
        
        # Initialize stakeholder engagement service
        config = ConstitutionalCouncilConfig()
        engagement_service = StakeholderNotificationService(db=db, config=config)
        
        logger.info("Testing stakeholder engagement initiation...")
        
        # Test 1: Initiate stakeholder engagement
        engagement_input = StakeholderEngagementInput(
            amendment_id=test_amendment.id,
            required_roles=[
                StakeholderRole.CONSTITUTIONAL_EXPERT,
                StakeholderRole.POLICY_ADMINISTRATOR,
                StakeholderRole.SYSTEM_AUDITOR,
                StakeholderRole.PUBLIC_REPRESENTATIVE
            ],
            notification_channels=[
                NotificationChannel.EMAIL,
                NotificationChannel.DASHBOARD
            ],
            engagement_period_hours=72,
            require_all_stakeholders=False,
            reminder_intervals_hours=[24, 12, 2]
        )
        
        engagement_status = await engagement_service.initiate_stakeholder_engagement(engagement_input)
        
        logger.info(f"Engagement initiated: {engagement_status.total_stakeholders} stakeholders, {engagement_status.notifications_sent} notifications sent")
        
        # Test 2: Collect feedback from stakeholders
        logger.info("Testing feedback collection...")
        
        feedback_tests = [
            (1, "This amendment looks good but needs clarification on implementation details.", "comment"),
            (2, "I support this amendment with minor modifications.", "vote"),
            (3, "Security implications need to be addressed before approval.", "concern"),
            (4, "The public impact assessment is missing key considerations.", "suggestion")
        ]
        
        for user_id, feedback_content, feedback_type in feedback_tests:
            feedback_record = await engagement_service.collect_stakeholder_feedback(
                amendment_id=test_amendment.id,
                stakeholder_id=user_id,
                feedback_content=feedback_content,
                feedback_type=feedback_type
            )
            logger.info(f"Feedback collected from user {user_id}: {feedback_record.id}")
        
        # Test 3: Check engagement status
        logger.info("Testing engagement status retrieval...")
        
        updated_status = await engagement_service.get_engagement_status(test_amendment.id)
        if updated_status:
            logger.info(f"Updated engagement status: {updated_status.engaged_stakeholders}/{updated_status.total_stakeholders} stakeholders engaged ({updated_status.engagement_rate:.1%})")
            logger.info(f"Feedback by role: {updated_status.feedback_by_role}")
        
        # Test 4: Get stakeholder notifications
        logger.info("Testing notification retrieval...")
        
        for user in test_users:
            notifications = await engagement_service.get_stakeholder_notifications(
                stakeholder_id=user.id,
                amendment_id=test_amendment.id
            )
            logger.info(f"User {user.username} has {len(notifications)} notifications")
        
        # Test 5: Get feedback records
        logger.info("Testing feedback retrieval...")
        
        all_feedback = await engagement_service.get_stakeholder_feedback(
            amendment_id=test_amendment.id
        )
        logger.info(f"Total feedback records: {len(all_feedback)}")
        
        for feedback in all_feedback:
            logger.info(f"Feedback {feedback.id}: {feedback.stakeholder_role.value} - {feedback.feedback_type}")
        
        logger.info("All tests completed successfully!")
        
        # Print summary
        print("\n" + "="*60)
        print("STAKEHOLDER ENGAGEMENT SYSTEM TEST SUMMARY")
        print("="*60)
        print(f"Amendment ID: {test_amendment.id}")
        print(f"Total Stakeholders: {updated_status.total_stakeholders if updated_status else 0}")
        print(f"Engaged Stakeholders: {updated_status.engaged_stakeholders if updated_status else 0}")
        print(f"Engagement Rate: {updated_status.engagement_rate:.1%}" if updated_status else "0%")
        print(f"Notifications Sent: {updated_status.notifications_sent if updated_status else 0}")
        print(f"Feedback Received: {len(all_feedback)}")
        print(f"Feedback by Role: {updated_status.feedback_by_role if updated_status else {}}")
        print("="*60)

if __name__ == "__main__":
    asyncio.run(test_stakeholder_engagement())
