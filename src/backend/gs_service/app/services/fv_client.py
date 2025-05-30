import os
import httpx
from typing import List, Optional
from ..schemas import FVVerificationRequest, FVVerificationResponse, FVPolicyRuleRef # Schemas from gs_service

# Load environment variables
FV_SERVICE_URL = os.getenv("FV_SERVICE_URL", "http://fv_service:8000/api/v1") # Default for Docker Compose

class FVServiceClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        timeout_config = httpx.Timeout(30.0, connect=5.0) # Increased timeout for potentially long verification
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=timeout_config)

    async def request_verification(
        self,
        policy_rule_ids: List[int],
        auth_token: Optional[str] = None # Placeholder for auth
    ) -> Optional[FVVerificationResponse]:
        """
        Sends a list of policy rule IDs to the FV Service for verification.
        """
        headers = {}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        # Prepare the request payload for FV Service
        fv_rule_refs = [FVPolicyRuleRef(id=rule_id) for rule_id in policy_rule_ids]
        verification_payload = FVVerificationRequest(policy_rule_refs=fv_rule_refs)
        
        try:
            # The FV Service expects POST requests to /verify/
            response = await self.client.post("/verify/", json=verification_payload.model_dump(), headers=headers)
            response.raise_for_status()
            data = response.json()
            return FVVerificationResponse(**data)
        except httpx.HTTPStatusError as e:
            print(f"HTTP error requesting verification from FV Service: {e.response.status_code} - {e.response.text}")
            try:
                error_details = e.response.json()
                print(f"Error details: {error_details}")
            except Exception:
                pass
            return None
        except httpx.RequestError as e:
            print(f"Request error requesting verification from FV Service: {str(e)}")
            return None
        except Exception as e: # Catch other potential errors like JSON decoding
            print(f"Unexpected error during FV request: {str(e)}")
            return None

    async def close(self):
        await self.client.aclose()

# Global client instance
fv_service_client = FVServiceClient(base_url=FV_SERVICE_URL)

# Example Usage (for testing this file)
if __name__ == "__main__":
    import asyncio

    async def test_fv_client():
        print(f"Testing FV Client against URL: {FV_SERVICE_URL}")
        # This test requires fv_service, integrity_service, and ac_service to be running
        # and integrity_service to have some rules (e.g., IDs 1, 2).
        
        # Placeholder token for FV Service (if its placeholder auth expects one)
        # The fv_service placeholder auth uses "internal_caller_token"
        test_auth_token = "internal_caller_token" 

        # Example: Request verification for some policy rule IDs
        # rule_ids_to_verify = [1, 2] # Assuming these rule IDs exist in integrity_service
        
        # print(f"\nRequesting verification for rule IDs: {rule_ids_to_verify}...")
        # verification_response = await fv_service_client.request_verification(
        #     policy_rule_ids=rule_ids_to_verify,
        #     auth_token=test_auth_token
        # )
        
        # if verification_response:
        #     print(f"\nVerification Response from FV Service: {verification_response.model_dump_json(indent=2)}")
        # else:
        #     print("\nFailed to get a verification response from FV Service.")
        
        await fv_service_client.close()
        print("\nNote: Actual verification depends on running fv_service and its dependencies (ac_service, integrity_service).")
        print("If services are not running or data is missing, 'None' or errors are expected.")

    # To run this test, ensure fv_service and its dependencies are running.
    # asyncio.run(test_fv_client())
    print("FV Service client defined. Run test_fv_client() with relevant services running to test.")
