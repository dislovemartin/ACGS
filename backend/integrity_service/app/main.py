from fastapi import FastAPI
from integrity_service.app.api.v1 import policies as policies_router
from integrity_service.app.api.v1 import audit as audit_router
from integrity_service.app.db.database import create_db_tables
from shared.security_middleware import add_security_headers # Import the shared middleware

app = FastAPI(title="Integrity and Verifiability Service")

# Apply the security headers middleware
app.middleware("http")(add_security_headers)

# Include the API routers
app.include_router(policies_router.router, prefix="/api/v1/policies", tags=["Policy Rules"])
app.include_router(audit_router.router, prefix="/api/v1/audit", tags=["Audit Logs"])

@app.on_event("startup")
def on_startup():
    # Create database tables if they don't exist
    create_db_tables()
    print("Integrity Service startup: Database tables check/creation initiated.")

@app.get("/")
async def root():
    return {"message": "Integrity and Verifiability Service is running. Use /docs for API documentation."}

# Placeholder for future health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}
