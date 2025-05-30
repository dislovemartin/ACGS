import os
import httpx
from typing import List, Optional
from ..schemas import PolicyRule, PolicyRuleStatusUpdate # Using schemas defined in fv_service

# Load environment variables
INTEGRITY_SERVICE_URL = os.getenv("INTEGRITY_SERVICE_URL", "http://integrity_service:8000/api/v1")

class IntegrityServiceClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        timeout_config = httpx.Timeout(10.0, connect=5.0)
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=timeout_config)

    async def get_policy_rule_by_id(self, rule_id: int, auth_token: Optional[str] = None) -> Optional[PolicyRule]:
        headers = {}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        
        try:
            response = await self.client.get(f"/policies/{rule_id}", headers=headers)
            response.raise_for_status()
            data = response.json()
            return PolicyRule(**data)
        except httpx.HTTPStatusError as e:
            print(f"Integrity Client: HTTP error fetching rule {rule_id}: {e.response.status_code} - {e.response.text}")
            return None
        except httpx.RequestError as e:
            print(f"Integrity Client: Request error fetching rule {rule_id}: {str(e)}")
            return None
        except Exception as e:
            print(f"Integrity Client: Unexpected error fetching rule {rule_id}: {str(e)}")
            return None

    async def get_policy_rules_by_ids(self, rule_ids: List[int], auth_token: Optional[str] = None) -> List[PolicyRule]:
        """Fetches multiple policy rules by their IDs."""
        # Assumes integrity_service does not have a batch endpoint.
        rules = []
        for rid in rule_ids:
            rule = await self.get_policy_rule_by_id(rid, auth_token=auth_token)
            if rule:
                rules.append(rule)
        return rules

    async def update_policy_rule_status(
        self, 
        rule_id: int, 
        status: str, 
        auth_token: Optional[str] = None
    ) -> Optional[PolicyRule]:
        headers = {}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        
        status_update_data = PolicyRuleStatusUpdate(verification_status=status)
        
        try:
            # Integrity service endpoint for status update is PUT /policies/{rule_id}/status
            response = await self.client.put(
                f"/policies/{rule_id}/status", 
                json=status_update_data.model_dump(), 
                headers=headers
            )
            response.raise_for_status()
            data = response.json()
            return PolicyRule(**data) # Assuming it returns the updated rule
        except httpx.HTTPStatusError as e:
            print(f"Integrity Client: HTTP error updating status for rule {rule_id}: {e.response.status_code} - {e.response.text}")
            try:
                error_details = e.response.json()
                print(f"Error details: {error_details}")
            except Exception:
                pass
            return None
        except httpx.RequestError as e:
            print(f"Integrity Client: Request error updating status for rule {rule_id}: {str(e)}")
            return None
        except Exception as e:
            print(f"Integrity Client: Unexpected error updating rule status {rule_id}: {str(e)}")
            return None

    async def close(self):
        await self.client.aclose()

# Global client instance
integrity_service_client = IntegrityServiceClient(base_url=INTEGRITY_SERVICE_URL)

# Example Usage
if __name__ == "__main__":
    import asyncio
    async def test_integrity_client_for_fv():
        print(f"Testing Integrity Client for FV Service against URL: {INTEGRITY_SERVICE_URL}")
        # test_token = "internal_service_token" # Placeholder token for integrity_service
        # fetched_rule = await integrity_service_client.get_policy_rule_by_id(1, auth_token=test_token) # Assuming rule ID 1 exists
        # if fetched_rule:
        #     print(f"Fetched rule 1: {fetched_rule.rule_content[:30]}...")
        #     updated_rule = await integrity_service_client.update_policy_rule_status(1, "verified", auth_token=test_token)
        #     if updated_rule:
        #         print(f"Updated rule 1 status to: {updated_rule.verification_status}")
        #     else:
        #         print("Failed to update rule 1 status.")
        # else:
        #     print("Rule 1 not found or error.")
        await integrity_service_client.close()
        print("Run with a live Integrity service to see results.")
    # asyncio.run(test_integrity_client_for_fv())
    print("Integrity Service client for FV defined.")
