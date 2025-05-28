from fastapi import FastAPI
from fv_service.app.api.v1.verify import router as verify_router
from fv_service.app.services.ac_client import ac_service_client
from fv_service.app.services.integrity_client import integrity_service_client
from shared.security_middleware import add_security_headers # Import the shared middleware

app = FastAPI(title="Formal Verification (FV) Service")

# Apply the security headers middleware
app.middleware("http")(add_security_headers)

# Include the API router for verification
app.include_router(verify_router, prefix="/api/v1/verify", tags=["Formal Verification"])

@app.on_event("startup")
async def on_startup():
    # HTTP clients are initialized when their modules are imported.
    # Add health check pings to dependent services here if needed.
    print("FV Service startup: Ready for formal verification tasks.")

@app.on_event("shutdown")
async def on_shutdown():
    # Gracefully close HTTPX clients
    await ac_service_client.close()
    await integrity_service_client.close()
    print("FV Service shutdown: HTTP clients closed.")

@app.get("/")
async def root():
    return {"message": "Formal Verification Service is running. Use /api/v1/verify/docs for API documentation."}

# Placeholder for future health check endpoint
@app.get("/health")
async def health_check():
    # A more comprehensive health check might try to connect to dependent services.
    return {"status": "ok", "message": "FV Service is operational."}
