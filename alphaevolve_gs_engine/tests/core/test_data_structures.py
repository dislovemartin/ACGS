"""
test_data_structures.py

This module contains unit tests for the core data structures defined in
`alphaevolve_gs_engine.core`, such as ConstitutionalPrinciple, OperationalRule,
and Amendment.
"""

import unittest
from datetime import datetime, timedelta

# Adjust import path if running tests from a different directory structure
# This assumes tests might be run from the root of the project or within `alphaevolve_gs_engine/tests/`
import sys
import os
# Add the 'src' directory to sys.path to allow direct imports of engine modules
# This is a common way to handle imports in tests when the package isn't "installed" in the traditional sense
current_dir = os.path.dirname(os.path.abspath(__file__))
# Navigate up to 'alphaevolve_gs_engine' then into 'src'
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir))) # Adjust if structure is different
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)


from alphaevolve_gs_engine.core.constitutional_principle import ConstitutionalPrinciple
from alphaevolve_gs_engine.core.operational_rule import OperationalRule
from alphaevolve_gs_engine.core.amendment import Amendment

class TestConstitutionalPrinciple(unittest.TestCase):
    """Tests for the ConstitutionalPrinciple class."""

    def test_principle_creation_minimal(self):
        """Test basic creation of a ConstitutionalPrinciple."""
        cp = ConstitutionalPrinciple(
            principle_id="CP001",
            name="Test Principle",
            description="A test description.",
            category="TestCategory",
            policy_code="package test.policy\ndefault allow = false"
        )
        self.assertEqual(cp.principle_id, "CP001")
        self.assertEqual(cp.name, "Test Principle")
        self.assertEqual(cp.version, 1)
        self.assertIsInstance(cp.creation_date, datetime)
        self.assertIsInstance(cp.last_modified, datetime)
        self.assertEqual(cp.metadata, {})
        self.assertEqual(cp.dependencies, [])

    def test_principle_creation_full(self):
        """Test creation with all optional parameters."""
        metadata = {"author": "tester", "status": "draft"}
        dependencies = ["CP000"]
        cp = ConstitutionalPrinciple(
            principle_id="CP002",
            name="Full Principle",
            description="Another test description.",
            category="FullCategory",
            policy_code="package test.full_policy\ndefault allow = true",
            version=2,
            metadata=metadata,
            dependencies=dependencies
        )
        self.assertEqual(cp.version, 2) # Version should be taken as is if provided
        self.assertEqual(cp.metadata["author"], "tester")
        self.assertEqual(cp.dependencies, ["CP000"])

    def test_principle_update(self):
        """Test updating a principle's attributes."""
        cp = ConstitutionalPrinciple("CP003", "Updatable", "Desc", "Cat", "Code")
        original_last_modified = cp.last_modified
        original_version = cp.version

        # Make an update
        new_desc = "Updated description"
        new_code = "package test.updated_code\ndefault allow = true"
        cp.update(description=new_desc, policy_code=new_code, metadata={"reviewer": "review_bot"})

        self.assertEqual(cp.description, new_desc)
        self.assertEqual(cp.policy_code, new_code)
        self.assertEqual(cp.version, original_version + 1)
        self.assertGreater(cp.last_modified, original_last_modified)
        self.assertEqual(cp.metadata["reviewer"], "review_bot")

    def test_principle_to_dict_and_from_dict(self):
        """Test serialization to and deserialization from a dictionary."""
        cp_orig = ConstitutionalPrinciple(
            principle_id="CP004",
            name="Serializable Principle",
            description="Testing to_dict and from_dict.",
            category="Serialization",
            policy_code="package test.serial\ndefault allow = false",
            metadata={"source": "test_suite"},
            dependencies=["CP001", "CP002"]
        )
        cp_orig.update(name="Updated Serializable Principle") # Increment version for test

        cp_dict = cp_orig.to_dict()

        # Check dict content
        self.assertEqual(cp_dict["principle_id"], cp_orig.principle_id)
        self.assertEqual(cp_dict["name"], cp_orig.name)
        self.assertEqual(cp_dict["version"], cp_orig.version)
        self.assertEqual(cp_dict["policy_code"], cp_orig.policy_code)
        self.assertIn("creation_date", cp_dict)
        self.assertIn("last_modified", cp_dict)
        self.assertEqual(cp_dict["metadata"]["source"], "test_suite")
        self.assertEqual(cp_dict["dependencies"], ["CP001", "CP002"])

        cp_reloaded = ConstitutionalPrinciple.from_dict(cp_dict)

        # Check reloaded object
        self.assertEqual(cp_reloaded.principle_id, cp_orig.principle_id)
        self.assertEqual(cp_reloaded.name, cp_orig.name)
        self.assertEqual(cp_reloaded.description, cp_orig.description)
        self.assertEqual(cp_reloaded.category, cp_orig.category)
        self.assertEqual(cp_reloaded.policy_code, cp_orig.policy_code)
        self.assertEqual(cp_reloaded.version, cp_orig.version)
        self.assertEqual(cp_reloaded.creation_date, cp_orig.creation_date)
        self.assertEqual(cp_reloaded.last_modified, cp_orig.last_modified)
        self.assertEqual(cp_reloaded.metadata, cp_orig.metadata)
        self.assertEqual(cp_reloaded.dependencies, cp_orig.dependencies)

    def test_principle_creation_invalid_input(self):
        """Test creation with missing required fields."""
        with self.assertRaises(ValueError):
            ConstitutionalPrinciple(principle_id="", name="Test", description="Desc", category="Cat", policy_code="Code")
        with self.assertRaises(ValueError):
            ConstitutionalPrinciple(principle_id="CP", name="", description="Desc", category="Cat", policy_code="Code")


class TestOperationalRule(unittest.TestCase):
    """Tests for the OperationalRule class."""

    def test_rule_creation_minimal(self):
        """Test basic creation of an OperationalRule."""
        op_rule = OperationalRule(
            rule_id="OR001",
            name="Test Rule",
            description="A test operational rule.",
            policy_code="package company.ops.test\ndefault allow_action = false",
            derived_from_principles=["CP001"]
        )
        self.assertEqual(op_rule.rule_id, "OR001")
        self.assertEqual(op_rule.name, "Test Rule")
        self.assertTrue(op_rule.is_active)
        self.assertEqual(op_rule.version, 1)
        self.assertEqual(op_rule.derived_from_principles, ["CP001"])
        self.assertEqual(op_rule.priority, 100) # Default priority

    def test_rule_creation_full(self):
        """Test creation with all optional parameters."""
        metadata = {"author": "rule_writer", "tags": ["finance", "compliance"]}
        op_rule = OperationalRule(
            rule_id="OR002",
            name="Full Rule",
            description="Another test rule.",
            policy_code="package company.ops.full\ndefault allow_payment = true",
            derived_from_principles=["CP001", "CP002"],
            version=3,
            is_active=False,
            metadata=metadata,
            priority=50
        )
        self.assertEqual(op_rule.version, 3)
        self.assertFalse(op_rule.is_active)
        self.assertEqual(op_rule.metadata["tags"], ["finance", "compliance"])
        self.assertEqual(op_rule.priority, 50)

    def test_rule_update(self):
        """Test updating a rule's attributes."""
        op_rule = OperationalRule("OR003", "Updatable Rule", "Desc", "Code", ["CP001"])
        original_modified_time = op_rule.last_modified
        original_version = op_rule.version

        op_rule.update(
            name="Updated Rule Name",
            is_active=False,
            priority=75,
            metadata={"status": "reviewed"}
        )
        self.assertEqual(op_rule.name, "Updated Rule Name")
        self.assertFalse(op_rule.is_active)
        self.assertEqual(op_rule.priority, 75)
        self.assertEqual(op_rule.version, original_version + 1)
        self.assertGreater(op_rule.last_modified, original_modified_time)
        self.assertEqual(op_rule.metadata["status"], "reviewed")

    def test_rule_activate_deactivate(self):
        """Test activating and deactivating a rule."""
        op_rule = OperationalRule("OR004", "Activatable Rule", "Desc", "Code", ["CP001"])
        self.assertTrue(op_rule.is_active) # Default active

        op_rule.deactivate()
        self.assertFalse(op_rule.is_active)
        last_mod_after_deactivate = op_rule.last_modified

        op_rule.activate()
        self.assertTrue(op_rule.is_active)
        self.assertGreater(op_rule.last_modified, last_mod_after_deactivate)

    def test_rule_to_dict_and_from_dict(self):
        """Test serialization to and deserialization from a dictionary."""
        op_rule_orig = OperationalRule(
            rule_id="OR005",
            name="Serializable Rule",
            description="Testing rule to_dict and from_dict.",
            policy_code="package company.ops.serial\ndefault check_ok = true",
            derived_from_principles=["CP003"],
            metadata={"source_system": "legacy_importer"},
            priority=60,
            is_active=False
        )
        op_rule_orig.update(description="Updated rule description.") # Increment version

        rule_dict = op_rule_orig.to_dict()

        # Check dict content
        self.assertEqual(rule_dict["rule_id"], op_rule_orig.rule_id)
        self.assertEqual(rule_dict["name"], op_rule_orig.name)
        self.assertEqual(rule_dict["version"], op_rule_orig.version)
        self.assertEqual(rule_dict["policy_code"], op_rule_orig.policy_code)
        self.assertEqual(rule_dict["derived_from_principles"], op_rule_orig.derived_from_principles)
        self.assertEqual(rule_dict["is_active"], op_rule_orig.is_active)
        self.assertEqual(rule_dict["priority"], op_rule_orig.priority)
        self.assertEqual(rule_dict["metadata"]["source_system"], "legacy_importer")

        rule_reloaded = OperationalRule.from_dict(rule_dict)

        # Check reloaded object
        self.assertEqual(rule_reloaded.rule_id, op_rule_orig.rule_id)
        self.assertEqual(rule_reloaded.name, op_rule_orig.name)
        # ... (check all other attributes similar to ConstitutionalPrinciple test)
        self.assertEqual(rule_reloaded.version, op_rule_orig.version)
        self.assertEqual(rule_reloaded.creation_date, op_rule_orig.creation_date)
        self.assertEqual(rule_reloaded.last_modified, op_rule_orig.last_modified)
        self.assertEqual(rule_reloaded.is_active, op_rule_orig.is_active)
        self.assertEqual(rule_reloaded.priority, op_rule_orig.priority)
        self.assertEqual(rule_reloaded.metadata, op_rule_orig.metadata)

    def test_rule_creation_invalid_input(self):
        """Test rule creation with missing required fields."""
        with self.assertRaises(ValueError):
            OperationalRule(rule_id="", name="N", description="D", policy_code="C", derived_from_principles=["CP"])
        with self.assertRaises(ValueError):
            OperationalRule(rule_id="R", name="N", description="D", policy_code="C", derived_from_principles=[]) # Must derive from something


class TestAmendment(unittest.TestCase):
    """Tests for the Amendment class."""

    def test_amendment_creation(self):
        """Test basic creation of an Amendment."""
        proposed_change = {"field_to_change": "new_value", "old_value": "old_value"}
        am = Amendment(
            amendment_id="AM001",
            target_rule_id="OR001", # Could be CP or OR ID
            proposed_change=proposed_change,
            justification="To improve clarity and efficiency.",
            proposer_id="user123"
        )
        self.assertEqual(am.amendment_id, "AM001")
        self.assertEqual(am.target_rule_id, "OR001")
        self.assertEqual(am.proposed_change["field_to_change"], "new_value")
        self.assertEqual(am.justification, "To improve clarity and efficiency.")
        self.assertEqual(am.proposer_id, "user123")
        self.assertEqual(am.status, "proposed") # Initial status
        self.assertIsInstance(am.timestamp, datetime)

    def test_amendment_status_change(self):
        """Test approving and rejecting an amendment."""
        am = Amendment("AM002", "CP002", {"text": "new text"}, "Update needed")
        
        am.approve()
        self.assertEqual(am.status, "approved")
        
        # Test idempotency or further changes if applicable (e.g. cannot reject if approved by some logic)
        # For this simple class, status can be changed multiple times.
        am.reject()
        self.assertEqual(am.status, "rejected")

        am.status = "pending_review" # Direct status change (if allowed by design)
        self.assertEqual(am.status, "pending_review")


    def test_amendment_get_details(self):
        """Test the get_details method."""
        proposed_change = {"policy_code": "package new.code\ndefault allow=true"}
        am = Amendment(
            amendment_id="AM003",
            target_rule_id="OR003",
            proposed_change=proposed_change,
            justification="Security update.",
            proposer_id="security_bot"
        )
        details = am.get_details()

        self.assertEqual(details["amendment_id"], am.amendment_id)
        self.assertEqual(details["target_rule_id"], am.target_rule_id)
        self.assertEqual(details["proposed_change"], am.proposed_change)
        self.assertEqual(details["justification"], am.justification)
        self.assertEqual(details["status"], am.status)
        self.assertEqual(details["proposer_id"], am.proposer_id)
        self.assertEqual(details["timestamp"], am.timestamp.isoformat())


if __name__ == '__main__':
    unittest.main(verbosity=2)
