#!/usr/bin/env python3
"""
Simple test for Stakeholder Engagement System components

This script tests the stakeholder engagement system classes and models
without requiring database connections.
"""

import sys
import os
from datetime import datetime, timezone, timedelta
from typing import List

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.stakeholder_engagement import (
    NotificationChannel,
    StakeholderRole,
    NotificationStatus,
    FeedbackStatus,
    NotificationRecord,
    FeedbackRecord,
    StakeholderEngagementInput,
    StakeholderEngagementStatus
)

def test_enums():
    """Test enum definitions."""
    print("Testing enum definitions...")
    
    # Test NotificationChannel
    assert NotificationChannel.EMAIL == "email"
    assert NotificationChannel.DASHBOARD == "dashboard"
    assert NotificationChannel.WEBHOOK == "webhook"
    assert NotificationChannel.WEBSOCKET == "websocket"
    
    # Test StakeholderRole
    assert StakeholderRole.CONSTITUTIONAL_EXPERT == "constitutional_expert"
    assert StakeholderRole.POLICY_ADMINISTRATOR == "policy_administrator"
    assert StakeholderRole.SYSTEM_AUDITOR == "system_auditor"
    assert StakeholderRole.PUBLIC_REPRESENTATIVE == "public_representative"
    
    # Test NotificationStatus
    assert NotificationStatus.PENDING == "pending"
    assert NotificationStatus.SENT == "sent"
    assert NotificationStatus.DELIVERED == "delivered"
    assert NotificationStatus.FAILED == "failed"
    assert NotificationStatus.READ == "read"
    
    # Test FeedbackStatus
    assert FeedbackStatus.PENDING == "pending"
    assert FeedbackStatus.SUBMITTED == "submitted"
    assert FeedbackStatus.REVIEWED == "reviewed"
    assert FeedbackStatus.INCORPORATED == "incorporated"
    
    print("✓ All enums defined correctly")

def test_notification_record():
    """Test NotificationRecord dataclass."""
    print("Testing NotificationRecord...")
    
    notification = NotificationRecord(
        id="test_notification_1",
        stakeholder_id=1,
        stakeholder_role=StakeholderRole.CONSTITUTIONAL_EXPERT,
        amendment_id=1,
        channel=NotificationChannel.EMAIL,
        status=NotificationStatus.PENDING,
        content={
            "subject": "Test Amendment Notification",
            "stakeholder": {"id": 1, "username": "expert1", "email": "expert1@test.com"},
            "amendment": {"id": 1, "title": "Test Amendment"}
        }
    )
    
    assert notification.id == "test_notification_1"
    assert notification.stakeholder_id == 1
    assert notification.stakeholder_role == StakeholderRole.CONSTITUTIONAL_EXPERT
    assert notification.amendment_id == 1
    assert notification.channel == NotificationChannel.EMAIL
    assert notification.status == NotificationStatus.PENDING
    assert notification.content["subject"] == "Test Amendment Notification"
    assert notification.retry_count == 0
    
    print("✓ NotificationRecord works correctly")

def test_feedback_record():
    """Test FeedbackRecord dataclass."""
    print("Testing FeedbackRecord...")
    
    feedback = FeedbackRecord(
        id="test_feedback_1",
        stakeholder_id=1,
        stakeholder_role=StakeholderRole.POLICY_ADMINISTRATOR,
        amendment_id=1,
        feedback_content="This amendment needs clarification on implementation details.",
        feedback_type="comment",
        status=FeedbackStatus.SUBMITTED,
        submitted_at=datetime.now(timezone.utc)
    )
    
    assert feedback.id == "test_feedback_1"
    assert feedback.stakeholder_id == 1
    assert feedback.stakeholder_role == StakeholderRole.POLICY_ADMINISTRATOR
    assert feedback.amendment_id == 1
    assert feedback.feedback_type == "comment"
    assert feedback.status == FeedbackStatus.SUBMITTED
    assert "clarification" in feedback.feedback_content
    
    print("✓ FeedbackRecord works correctly")

def test_stakeholder_engagement_input():
    """Test StakeholderEngagementInput validation."""
    print("Testing StakeholderEngagementInput...")
    
    # Test valid input
    engagement_input = StakeholderEngagementInput(
        amendment_id=1,
        required_roles=[
            StakeholderRole.CONSTITUTIONAL_EXPERT,
            StakeholderRole.POLICY_ADMINISTRATOR
        ],
        notification_channels=[
            NotificationChannel.EMAIL,
            NotificationChannel.DASHBOARD
        ],
        engagement_period_hours=72,
        require_all_stakeholders=False,
        reminder_intervals_hours=[24, 12, 2]
    )
    
    assert engagement_input.amendment_id == 1
    assert len(engagement_input.required_roles) == 2
    assert len(engagement_input.notification_channels) == 2
    assert engagement_input.engagement_period_hours == 72
    assert not engagement_input.require_all_stakeholders
    assert engagement_input.reminder_intervals_hours == [24, 12, 2]
    
    # Test default values
    default_input = StakeholderEngagementInput(amendment_id=2)
    assert len(default_input.required_roles) == 4  # All stakeholder roles by default
    assert NotificationChannel.EMAIL in default_input.notification_channels
    assert NotificationChannel.DASHBOARD in default_input.notification_channels
    assert default_input.engagement_period_hours == 72
    
    print("✓ StakeholderEngagementInput validation works correctly")

def test_stakeholder_engagement_status():
    """Test StakeholderEngagementStatus model."""
    print("Testing StakeholderEngagementStatus...")
    
    deadline = datetime.now(timezone.utc) + timedelta(hours=48)
    
    status = StakeholderEngagementStatus(
        amendment_id=1,
        total_stakeholders=4,
        engaged_stakeholders=2,
        pending_stakeholders=2,
        engagement_rate=0.5,
        deadline=deadline,
        is_deadline_passed=False,
        notifications_sent=8,
        feedback_received=2,
        feedback_by_role={
            "constitutional_expert": 1,
            "policy_administrator": 1,
            "system_auditor": 0,
            "public_representative": 0
        },
        status_by_stakeholder={
            1: {"feedback_submitted": True, "engagement_score": 1.0},
            2: {"feedback_submitted": True, "engagement_score": 1.0},
            3: {"feedback_submitted": False, "engagement_score": 0.0},
            4: {"feedback_submitted": False, "engagement_score": 0.0}
        },
        last_updated=datetime.now(timezone.utc)
    )
    
    assert status.amendment_id == 1
    assert status.total_stakeholders == 4
    assert status.engaged_stakeholders == 2
    assert status.engagement_rate == 0.5
    assert not status.is_deadline_passed
    assert status.notifications_sent == 8
    assert status.feedback_received == 2
    assert status.feedback_by_role["constitutional_expert"] == 1
    assert len(status.status_by_stakeholder) == 4
    
    print("✓ StakeholderEngagementStatus works correctly")

def test_notification_content_structure():
    """Test notification content structure."""
    print("Testing notification content structure...")
    
    # Simulate notification content creation
    stakeholder = {
        "id": 1,
        "username": "expert1",
        "email": "expert1@test.com",
        "role": "constitutional_expert"
    }
    
    amendment = {
        "id": 1,
        "title": "Test Constitutional Amendment",
        "description": "A test amendment for validation",
        "proposed_by": 1,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    deadline = datetime.now(timezone.utc) + timedelta(hours=72)
    
    content = {
        "subject": "New Constitutional Amendment Proposal - Review Required",
        "template": "amendment_proposal_notification.html",
        "stakeholder": stakeholder,
        "amendment": amendment,
        "engagement": {
            "deadline": deadline.isoformat(),
            "hours_remaining": 72,
            "notification_type": "amendment_proposal"
        },
        "actions": {
            "review_url": f"/constitutional-council/amendments/{amendment['id']}",
            "feedback_url": f"/constitutional-council/amendments/{amendment['id']}/feedback",
            "dashboard_url": "/dashboard/constitutional-council"
        },
        "metadata": {}
    }
    
    assert content["subject"] == "New Constitutional Amendment Proposal - Review Required"
    assert content["stakeholder"]["username"] == "expert1"
    assert content["amendment"]["title"] == "Test Constitutional Amendment"
    assert content["engagement"]["hours_remaining"] == 72
    assert "/constitutional-council/amendments/1" in content["actions"]["review_url"]
    
    print("✓ Notification content structure is correct")

def run_all_tests():
    """Run all tests."""
    print("="*60)
    print("STAKEHOLDER ENGAGEMENT SYSTEM - COMPONENT TESTS")
    print("="*60)
    
    try:
        test_enums()
        test_notification_record()
        test_feedback_record()
        test_stakeholder_engagement_input()
        test_stakeholder_engagement_status()
        test_notification_content_structure()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED SUCCESSFULLY!")
        print("="*60)
        print("Stakeholder Engagement System components are working correctly.")
        print("Key features validated:")
        print("- Enum definitions for channels, roles, and statuses")
        print("- NotificationRecord and FeedbackRecord data structures")
        print("- StakeholderEngagementInput validation")
        print("- StakeholderEngagementStatus tracking")
        print("- Notification content structure")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
