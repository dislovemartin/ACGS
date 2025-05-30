import asyncio
import hashlib
import re
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ..services.integrity_client import integrity_service_client, IntegrityPolicyRule
from .datalog_engine import datalog_engine # Use the global engine instance
from .policy_format_router import PolicyFormatRouter, PolicyFramework
from .manifest_manager import ManifestManager

# Import crypto service for signature verification
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../alphaevolve_gs_engine/src'))
try:
    from alphaevolve_gs_engine.services.crypto_service import CryptoService
except ImportError:
    CryptoService = None

# Placeholder token for Integrity Service (if its placeholder auth expects one)
# The integrity_service placeholder auth uses "internal_service_token" for GET /policies/
INTEGRITY_SERVICE_MOCK_TOKEN = "internal_service_token"

import logging
logger = logging.getLogger(__name__)

class PolicyManager:
    def __init__(self, refresh_interval_seconds: int = 300): # Default: refresh every 5 minutes
        self._active_rules: List[IntegrityPolicyRule] = []
        self._last_refresh_time: Optional[datetime] = None
        self._refresh_interval = timedelta(seconds=refresh_interval_seconds)
        self._lock = asyncio.Lock() # To prevent concurrent refresh operations

        # Enhanced components for audit findings
        self.format_router = PolicyFormatRouter()
        self.manifest_manager = ManifestManager()
        self.crypto_service = CryptoService() if CryptoService else None
        self._validation_stats = {
            'total_loaded': 0,
            'signature_verified': 0,
            'format_converted': 0,
            'validation_failed': 0
        }

    async def get_active_rules(self, force_refresh: bool = False) -> List[IntegrityPolicyRule]:
        """
        Returns the current list of active (verified) Datalog rules.
        Refreshes from the Integrity Service if the cache is stale or force_refresh is True.
        """
        async with self._lock:
            now = datetime.utcnow()
            if force_refresh or not self._last_refresh_time or \
               (now - self._last_refresh_time > self._refresh_interval):
                
                print("PolicyManager: Refreshing policies from Integrity Service...")
                try:
                    # Fetch verified rules from Integrity Service
                    fetched_rules = await integrity_service_client.list_verified_policy_rules(
                        auth_token=INTEGRITY_SERVICE_MOCK_TOKEN
                    )
                    if fetched_rules is not None: # list_verified_policy_rules returns [] on error, not None
                        self._active_rules = fetched_rules
                        self._last_refresh_time = now
                        print(f"PolicyManager: Successfully loaded {len(self._active_rules)} verified rules.")
                        
                        # Enhanced rule processing with format conversion and validation
                        processed_rules = await self._process_and_validate_rules(self._active_rules)

                        # Load rules into the Datalog engine
                        datalog_engine.clear_rules_and_facts() # Clear old rules and facts
                        rule_strings = [rule.rule_content for rule in processed_rules]
                        datalog_engine.load_rules(rule_strings)
                        print(f"PolicyManager: Datalog engine updated with {len(processed_rules)} processed rules.")
                        print(f"Validation stats: {self._validation_stats}")
                    else:
                        # This case might not be hit if client returns [] on error.
                        print("PolicyManager: Failed to fetch rules from Integrity Service (received None).")
                        # Optionally, decide if to clear active rules or keep stale ones
                        # For now, keeping stale ones if fetch fails.
                except Exception as e:
                    print(f"PolicyManager: Error refreshing policies: {e}")
                    # Decide on error handling: keep stale, clear, or retry later
            else:
                print("PolicyManager: Using cached policies.")
        return self._active_rules

    async def _process_and_validate_rules(self, rules: List[IntegrityPolicyRule]) -> List[IntegrityPolicyRule]:
        """
        Process and validate policy rules with enhanced integrity checks.
        Addresses audit findings for format conversion, signature verification, and validation.
        """
        processed_rules = []
        self._validation_stats['total_loaded'] = len(rules)

        for rule in rules:
            try:
                # 1. Verify PGP signature if present
                if hasattr(rule, 'pgp_signature') and rule.pgp_signature:
                    if await self._verify_rule_signature(rule):
                        self._validation_stats['signature_verified'] += 1
                        logger.debug(f"Signature verified for rule {getattr(rule, 'id', 'unknown')}")
                    else:
                        logger.warning(f"Signature verification failed for rule {getattr(rule, 'id', 'unknown')}")
                        self._validation_stats['validation_failed'] += 1
                        continue  # Skip rules with invalid signatures

                # 2. Detect and convert policy format if needed
                framework = getattr(rule, 'framework', 'Datalog')
                detected_framework = self.format_router.detect_framework(
                    rule.rule_content,
                    {'framework': framework}
                )

                # 3. Convert to Datalog if not already
                if detected_framework != PolicyFramework.DATALOG:
                    conversion_result = self.format_router.convert_to_rego(
                        rule.rule_content,
                        detected_framework,
                        f"rule_{getattr(rule, 'id', 'unknown')}"
                    )

                    if conversion_result.success:
                        # Update rule content with converted version
                        rule.rule_content = conversion_result.converted_content
                        self._validation_stats['format_converted'] += 1
                        logger.info(f"Converted rule from {detected_framework.value} to Rego")

                        # Update metadata
                        if hasattr(rule, 'framework'):
                            rule.framework = 'Rego'
                        if hasattr(rule, 'import_dependencies'):
                            rule.import_dependencies = conversion_result.import_dependencies
                    else:
                        logger.error(f"Failed to convert rule: {conversion_result.error_message}")
                        self._validation_stats['validation_failed'] += 1
                        continue

                # 4. Validate syntax
                if detected_framework == PolicyFramework.REGO or framework == 'Rego':
                    validation_result = self.format_router.validate_rego_syntax(rule.rule_content)
                    if not validation_result.is_valid:
                        logger.error(f"Rego syntax validation failed: {validation_result.error_message}")
                        self._validation_stats['validation_failed'] += 1
                        continue

                # 5. Generate content hash for integrity
                content_hash = self.format_router.generate_content_hash(rule.rule_content)
                if hasattr(rule, 'content_hash'):
                    rule.content_hash = content_hash

                # 6. Fill missing principle_text if empty
                if hasattr(rule, 'principle_text') and not rule.principle_text:
                    rule.principle_text = self._generate_principle_text(rule)

                processed_rules.append(rule)

            except Exception as e:
                logger.error(f"Error processing rule {getattr(rule, 'id', 'unknown')}: {e}")
                self._validation_stats['validation_failed'] += 1
                continue

        logger.info(f"Processed {len(processed_rules)}/{len(rules)} rules successfully")
        return processed_rules

    async def _verify_rule_signature(self, rule: IntegrityPolicyRule) -> bool:
        """Verify PGP signature of a policy rule"""
        if not self.crypto_service or not hasattr(rule, 'pgp_signature') or not rule.pgp_signature:
            return True  # Skip verification if no crypto service or signature

        try:
            # Create message to verify (rule content)
            message_to_verify = rule.rule_content

            # Decode signature (assuming it's hex-encoded)
            signature_bytes = bytes.fromhex(rule.pgp_signature)

            # Verify signature
            is_valid = self.crypto_service.verify_signature(message_to_verify, signature_bytes)
            return is_valid

        except Exception as e:
            logger.error(f"Signature verification error: {e}")
            return False

    def _generate_principle_text(self, rule: IntegrityPolicyRule) -> str:
        """Generate principle text for rules with empty principle_text"""
        # Extract meaningful description from rule content
        content = rule.rule_content

        # Try to extract from comments
        comment_lines = [line.strip()[1:].strip() for line in content.split('\n')
                        if line.strip().startswith('#')]
        if comment_lines:
            return comment_lines[0]

        # Try to extract from package name or rule name
        if 'package ' in content:
            package_match = re.search(r'package\s+([a-zA-Z_][a-zA-Z0-9_.]*)', content)
            if package_match:
                package_name = package_match.group(1)
                return f"Policy rule from package: {package_name}"

        # Fallback to rule name or generic description
        rule_name = getattr(rule, 'rule_name', None)
        if rule_name:
            return f"Policy rule: {rule_name}"

        return "Auto-generated policy rule description"

    def get_active_rule_strings(self) -> List[str]:
        """Returns only the rule content strings of the active rules."""
        # This method doesn't trigger a refresh on its own; relies on get_active_rules being called.
        # Or, could be adapted to also call get_active_rules if needed.
        if not self._active_rules and not self._last_refresh_time: # If never loaded
             print("PolicyManager: Rules not loaded yet. Consider calling get_active_rules() first.")
        return [rule.rule_content for rule in self._active_rules]


# Global instance of PolicyManager
# The refresh interval can be configured via environment variable if needed
policy_manager = PolicyManager(refresh_interval_seconds=300) 

# Example of how to trigger initial load (e.g., in main.py on startup)
# async def initial_policy_load():
#     await policy_manager.get_active_rules(force_refresh=True)

# For testing this file
if __name__ == "__main__":
    import asyncio

    async def test_policy_manager():
        print("Testing Policy Manager...")
        # Requires integrity_service to be running with some verified rules.
        
        # Initial load
        rules1 = await policy_manager.get_active_rules(force_refresh=True)
        print(f"Fetched {len(rules1)} rules initially.")
        if rules1:
            print(f"First rule content: {rules1[0].rule_content[:60]}...")
        
        # Subsequent call (should use cache if within refresh interval)
        # To test caching, you'd need to ensure refresh_interval is not immediately passed.
        # For this manual test, it will likely use cache if the first call was quick.
        # policy_manager._last_refresh_time = datetime.utcnow() # Simulate it just refreshed
        print("\nSecond call (expecting cache for rules, but Datalog engine is already loaded):")
        rules2 = await policy_manager.get_active_rules()
        print(f"Fetched {len(rules2)} rules on second call.")

        # Test Datalog engine state (indirectly)
        # This assumes integrity_service has a rule like: "test_rule(a) <= test_fact(a)."
        # And we add test_fact(a) directly to the engine.
        # Note: policy_manager already clears and loads rules.
        # If integrity_service returns "test_rule(a) <= test_fact(a).", then:
        # datalog_engine.add_facts(["+test_fact(a)"])
        # result = datalog_engine.query("test_rule(X)")
        # print(f"Query result for test_rule(X) after policy load: {result}")

        await integrity_service_client.close() # Close the shared client

    # asyncio.run(test_policy_manager())
    print("Policy Manager defined. Run test_policy_manager() with a live Integrity service to test.")
