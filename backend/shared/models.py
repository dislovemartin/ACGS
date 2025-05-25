# Centralized model imports for Alembic autodiscovery
# Ensure that each service's models.py file exists and its models inherit from backend.shared.database.Base

from shared.database import Base

# Import models from each service module.
# Replace '...' with actual model imports if you want to be explicit,
# or ensure the service's models.py is executed upon import.

print("Loading models from backend.shared.models...")

try:
    import backend.ac_service.models
    print("Successfully imported ac_service.models")
except ImportError as e:
    print(f"Could not import ac_service.models: {e}. Ensure it exists and has no import errors.")

try:
    import backend.auth_service.models
    print("Successfully imported auth_service.models")
except ImportError as e:
    print(f"Could not import auth_service.models: {e}. Ensure it exists and has no import errors.")

try:
    import backend.fv_service.models
    print("Successfully imported fv_service.models")
except ImportError as e:
    print(f"Could not import fv_service.models: {e}. Ensure it exists and has no import errors.")

try:
    import backend.gs_service.models
    print("Successfully imported gs_service.models")
except ImportError as e:
    print(f"Could not import gs_service.models: {e}. Ensure it exists and has no import errors.")

try:
    import backend.integrity_service.models
    print("Successfully imported integrity_service.models")
except ImportError as e:
    print(f"Could not import integrity_service.models: {e}. Ensure it exists and has no import errors.")

try:
    import backend.pgc_service.models
    print("Successfully imported pgc_service.models")
except ImportError as e:
    print(f"Could not import pgc_service.models: {e}. Ensure it exists and has no import errors.")

# Add any other service model imports here if new services are added.

print("Finished loading models in backend.shared.models.")
