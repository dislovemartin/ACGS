import os
import httpx
from typing import List, Optional
from ..schemas import ACPrinciple # Using the schema defined in fv_service
from shared.auth import get_service_token, get_auth_headers
from shared import get_config

# Load centralized configuration
config = get_config()

# Determine if running in Docker (internal) or external environment
is_docker_env = os.getenv('DOCKER_ENV', 'false').lower() == 'true'
AC_SERVICE_URL = config.get_service_url('ac', internal=is_docker_env, api_path='')

class ACServiceClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        timeout_config = httpx.Timeout(10.0, connect=5.0)
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=timeout_config)

    async def get_principle_by_id(self, principle_id: int, auth_token: Optional[str] = None) -> Optional[ACPrinciple]:
        # Use service token if no auth token provided
        if not auth_token:
            auth_token = await get_service_token()

        headers = get_auth_headers(auth_token)

        try:
            response = await self.client.get(f"/principles/{principle_id}", headers=headers)
            response.raise_for_status()
            data = response.json()
            return ACPrinciple(**data)
        except httpx.HTTPStatusError as e:
            print(f"AC Client: HTTP error fetching principle {principle_id}: {e.response.status_code} - {e.response.text}")
            return None
        except httpx.RequestError as e:
            print(f"AC Client: Request error fetching principle {principle_id}: {str(e)}")
            return None
        except Exception as e:
            print(f"AC Client: Unexpected error fetching principle {principle_id}: {str(e)}")
            return None

    async def list_principles_by_ids(self, principle_ids: List[int], auth_token: Optional[str] = None) -> List[ACPrinciple]:
        """Fetches multiple principles by their IDs."""
        # Note: This assumes ac_service might not have a batch endpoint.
        # If it did, that would be more efficient.
        principles = []
        for pid in principle_ids:
            principle = await self.get_principle_by_id(pid, auth_token=auth_token)
            if principle:
                principles.append(principle)
            # else: handle error or missing principle as needed
        return principles
        
    async def close(self):
        await self.client.aclose()

# Global client instance
ac_service_client = ACServiceClient(base_url=AC_SERVICE_URL)

# Example Usage
if __name__ == "__main__":
    import asyncio
    async def test_ac_client_for_fv():
        print(f"Testing AC Client for FV Service against URL: {AC_SERVICE_URL}")
        # test_token = "admin_token" # Placeholder token for ac_service
        # fetched_principle = await ac_service_client.get_principle_by_id(1, auth_token=test_token)
        # if fetched_principle:
        #     print(f"Fetched principle 1: {fetched_principle.name}")
        # else:
        #     print("Principle 1 not found or error.")
        # fetched_principles_list = await ac_service_client.list_principles_by_ids([1,2], auth_token=test_token)
        # print(f"Fetched {len(fetched_principles_list)} principles by list.")
        await ac_service_client.close()
        print("Run with a live AC service to see results.")
    # asyncio.run(test_ac_client_for_fv())
    print("AC Service client for FV defined.")
