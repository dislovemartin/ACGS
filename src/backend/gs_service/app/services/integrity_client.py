import os
import httpx
from typing import List, Optional
from ..schemas import PolicyRuleCreate, PolicyRule # Using schemas defined in gs_service

# Load environment variables
INTEGRITY_SERVICE_URL = os.getenv("INTEGRITY_SERVICE_URL", "http://integrity_service:8000/api/v1")

class IntegrityServiceClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        timeout_config = httpx.Timeout(10.0, connect=5.0)
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=timeout_config)

    async def store_policy_rule(
        self, 
        rule_data: PolicyRuleCreate, 
        auth_token: Optional[str] = None # Placeholder for auth
    ) -> Optional[PolicyRule]:
        """
        Stores a new policy rule in the Integrity Service.
        """
        headers = {}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}" # Assuming Bearer token auth for Integrity Service

        try:
            # The Integrity Service expects POST requests to /policies/
            response = await self.client.post("/policies/", json=rule_data.model_dump(), headers=headers)
            response.raise_for_status()
            data = response.json()
            return PolicyRule(**data) # Assuming Integrity Service returns the created rule including its ID
        except httpx.HTTPStatusError as e:
            print(f"HTTP error storing policy rule in Integrity Service: {e.response.status_code} - {e.response.text}")
            # Attempt to parse error response if available
            try:
                error_details = e.response.json()
                print(f"Error details: {error_details}")
            except Exception:
                pass # Ignore if error response is not JSON or unparseable
            return None
        except httpx.RequestError as e:
            print(f"Request error storing policy rule in Integrity Service: {str(e)}")
            return None
        except Exception as e:
            print(f"Unexpected error storing policy rule: {str(e)}")
            return None

    async def get_policy_rule_by_id(self, rule_id: int, auth_token: Optional[str] = None) -> Optional[PolicyRule]:
        """
        Fetches a policy rule by its ID from the Integrity Service.
        """
        headers = {}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        
        try:
            response = await self.client.get(f"/policies/{rule_id}", headers=headers)
            response.raise_for_status()
            data = response.json()
            return PolicyRule(**data)
        except httpx.HTTPStatusError as e:
            print(f"HTTP error fetching rule {rule_id} from Integrity Service: {e.response.status_code} - {e.response.text}")
            return None
        except httpx.RequestError as e:
            print(f"Request error fetching rule {rule_id} from Integrity Service: {str(e)}")
            return None
        except Exception as e:
            print(f"Unexpected error fetching rule {rule_id}: {str(e)}")
            return None

    async def close(self):
        await self.client.aclose()

# Global client instance
integrity_service_client = IntegrityServiceClient(base_url=INTEGRITY_SERVICE_URL)

# Example Usage (for testing this file)
if __name__ == "__main__":
    import asyncio

    async def test_integrity_client():
        print(f"Testing Integrity Client against URL: {INTEGRITY_SERVICE_URL}")
        # This test will only work if integrity_service is running and accessible.
        # For local testing, you might need to run `docker-compose up integrity_service` first.

        # Placeholder token for Integrity Service (if its placeholder auth expects one)
        # The integrity_service placeholder auth uses "internal_service_token" for POST /policies/
        test_auth_token = "internal_service_token" 

        # Example: Store a new rule
        new_rule_data = PolicyRuleCreate(
            rule_content="test_rule(X) :- condition(X).",
            source_principle_ids=[101, 102]
        )
        # created_rule = await integrity_service_client.store_policy_rule(new_rule_data, auth_token=test_auth_token)
        # if created_rule:
        #     print(f"\nStored Rule: {created_rule.model_dump_json(indent=2)}")
        #     rule_id_to_fetch = created_rule.id
            
        #     # Example: Fetch the stored rule
        #     fetched_rule = await integrity_service_client.get_policy_rule_by_id(rule_id_to_fetch, auth_token=test_auth_token)
        #     if fetched_rule:
        #         print(f"\nFetched Rule by ID {rule_id_to_fetch}: {fetched_rule.model_dump_json(indent=2)}")
        #     else:
        #         print(f"\nCould not fetch rule ID {rule_id_to_fetch}.")
        # else:
        #     print("\nCould not store the new rule.")
        
        await integrity_service_client.close()
        print("\nNote: Actual data operations depend on running integrity_service.")
        print("If integrity_service is not running, 'None' or errors are expected.")

    # To run this test, ensure integrity_service is running.
    # asyncio.run(test_integrity_client())
    print("Integrity Service client defined. Run test_integrity_client() with a running Integrity service to test.")
