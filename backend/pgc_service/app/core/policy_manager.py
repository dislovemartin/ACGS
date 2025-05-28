import asyncio
from typing import List, Optional
from datetime import datetime, timedelta

from ..services.integrity_client import integrity_service_client, IntegrityPolicyRule
from .datalog_engine import datalog_engine # Use the global engine instance

# Placeholder token for Integrity Service (if its placeholder auth expects one)
# The integrity_service placeholder auth uses "internal_service_token" for GET /policies/
INTEGRITY_SERVICE_MOCK_TOKEN = "internal_service_token" 

class PolicyManager:
    def __init__(self, refresh_interval_seconds: int = 300): # Default: refresh every 5 minutes
        self._active_rules: List[IntegrityPolicyRule] = []
        self._last_refresh_time: Optional[datetime] = None
        self._refresh_interval = timedelta(seconds=refresh_interval_seconds)
        self._lock = asyncio.Lock() # To prevent concurrent refresh operations

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
                        
                        # Load rules into the Datalog engine
                        datalog_engine.clear_rules_and_facts() # Clear old rules and facts
                        rule_strings = [rule.rule_content for rule in self._active_rules]
                        datalog_engine.load_rules(rule_strings)
                        print("PolicyManager: Datalog engine updated with new rules.")
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
