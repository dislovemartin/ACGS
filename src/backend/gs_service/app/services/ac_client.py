import os
import httpx
from typing import List, Optional
from ..schemas import ACPrinciple # Using the schema defined in gs_service

# Load environment variables
AC_SERVICE_URL = os.getenv("AC_SERVICE_URL", "http://ac_service:8000/api/v1") # Default for Docker Compose

class ACServiceClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        # Use a timeout configuration suitable for your environment
        timeout_config = httpx.Timeout(10.0, connect=5.0) # 10s read, 5s connect
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=timeout_config)

    async def get_principle_by_id(self, principle_id: int, auth_token: Optional[str] = None) -> Optional[ACPrinciple]:
        """
        Fetches a single principle by its ID from the AC Service.
        Placeholder for auth_token usage.
        """
        headers = {}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        
        try:
            response = await self.client.get(f"/principles/{principle_id}", headers=headers)
            response.raise_for_status() # Raise an exception for 4XX or 5XX status codes
            data = response.json()
            return ACPrinciple(**data)
        except httpx.HTTPStatusError as e:
            print(f"HTTP error fetching principle {principle_id} from AC Service: {e.response.status_code} - {e.response.text}")
            return None
        except httpx.RequestError as e:
            print(f"Request error fetching principle {principle_id} from AC Service: {str(e)}")
            return None
        except Exception as e: # Catch other potential errors like JSON decoding
            print(f"Unexpected error fetching principle {principle_id}: {str(e)}")
            return None

    async def list_principles(self, auth_token: Optional[str] = None) -> List[ACPrinciple]:
        """
        Fetches all principles from the AC Service.
        Placeholder for auth_token usage.
        """
        headers = {}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        
        try:
            response = await self.client.get("/principles/", headers=headers)
            response.raise_for_status()
            data = response.json() # AC service returns {"principles": [...], "total": ...}
            return [ACPrinciple(**p) for p in data.get("principles", [])]
        except httpx.HTTPStatusError as e:
            print(f"HTTP error listing principles from AC Service: {e.response.status_code} - {e.response.text}")
            return []
        except httpx.RequestError as e:
            print(f"Request error listing principles from AC Service: {str(e)}")
            return []
        except Exception as e:
            print(f"Unexpected error listing principles: {str(e)}")
            return []

    async def get_principles_for_context(self, context: str, category: Optional[str] = None, auth_token: Optional[str] = None) -> List[ACPrinciple]:
        """
        Get active principles applicable to a specific context.
        Uses the new enhanced AC service endpoint.
        """
        return await self.get_principles_by_context(context, category, auth_token)

    async def get_principles_by_context(self, context: str, category: Optional[str] = None, auth_token: Optional[str] = None) -> List[ACPrinciple]:
        """
        Get active principles applicable to a specific context.
        Uses the new enhanced AC service endpoint.
        """
        headers = {}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        try:
            url = f"/principles/active/context/{context}"
            params = {}
            if category:
                params["category"] = category

            response = await self.client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            return [ACPrinciple(**p) for p in data.get("principles", [])]
        except httpx.HTTPStatusError as e:
            print(f"HTTP error fetching principles for context {context}: {e.response.status_code} - {e.response.text}")
            return []
        except httpx.RequestError as e:
            print(f"Request error fetching principles for context {context}: {str(e)}")
            return []
        except Exception as e:
            print(f"Unexpected error fetching principles for context {context}: {str(e)}")
            return []

    async def get_principles_by_category(self, category: str, auth_token: Optional[str] = None) -> List[ACPrinciple]:
        """Get principles filtered by category."""
        headers = {}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        try:
            response = await self.client.get(f"/principles/category/{category}", headers=headers)
            response.raise_for_status()
            data = response.json()
            return [ACPrinciple(**p) for p in data.get("principles", [])]
        except httpx.HTTPStatusError as e:
            print(f"HTTP error fetching principles by category {category}: {e.response.status_code} - {e.response.text}")
            return []
        except httpx.RequestError as e:
            print(f"Request error fetching principles by category {category}: {str(e)}")
            return []
        except Exception as e:
            print(f"Unexpected error fetching principles by category {category}: {str(e)}")
            return []

    async def search_principles_by_keywords(self, keywords: List[str], auth_token: Optional[str] = None) -> List[ACPrinciple]:
        """Search principles by keywords."""
        headers = {}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        try:
            response = await self.client.post("/principles/search/keywords", json=keywords, headers=headers)
            response.raise_for_status()
            data = response.json()
            return [ACPrinciple(**p) for p in data.get("principles", [])]
        except httpx.HTTPStatusError as e:
            print(f"HTTP error searching principles by keywords: {e.response.status_code} - {e.response.text}")
            return []
        except httpx.RequestError as e:
            print(f"Request error searching principles by keywords: {str(e)}")
            return []
        except Exception as e:
            print(f"Unexpected error searching principles by keywords: {str(e)}")
            return []

    async def close(self):
        await self.client.aclose()

# Global client instance
ac_service_client = ACServiceClient(base_url=AC_SERVICE_URL)

# Example Usage (for testing this file)
if __name__ == "__main__":
    import asyncio

    async def test_ac_client():
        print(f"Testing AC Client against URL: {AC_SERVICE_URL}")
        # This test will only work if ac_service is running and accessible at AC_SERVICE_URL
        # and has some data.
        # For local testing, you might need to run `docker-compose up ac_service` first.
        
        # To simulate a token for AC service (if its placeholder auth expects one):
        # test_token = "admin_token" # This is the placeholder token for ac_service's admin
        
        # Fetch a specific principle (assuming principle ID 1 exists)
        # principle = await ac_service_client.get_principle_by_id(1, auth_token=test_token)
        # if principle:
        #     print(f"\nFetched Principle 1: {principle.model_dump_json(indent=2)}")
        # else:
        #     print("\nCould not fetch principle 1 or it does not exist.")

        # List all principles
        # principles = await ac_service_client.list_principles(auth_token=test_token)
        # if principles:
        #     print(f"\nFetched {len(principles)} Principles:")
        #     for p in principles:
        #         print(f"  - ID: {p.id}, Name: {p.name}, Content: {p.content[:30]}...")
        # else:
        #     print("\nNo principles found or error fetching them.")
        
        await ac_service_client.close()
        print("\nNote: Actual data fetching depends on running ac_service and its data.")
        print("If ac_service is not running or has no data, 'None' or empty lists are expected.")


    # To run this test, ensure ac_service is running.
    # You can try: `python -m gs_service.app.services.ac_client` from the root directory
    # However, due to relative imports (e.g. ..schemas), it's better to run tests via a test runner
    # or a script that adjusts Python path. For now, it's illustrative.
    # asyncio.run(test_ac_client())
    print("AC Service client defined. Run test_ac_client() with a running AC service to test.")
