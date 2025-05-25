from fastapi import FastAPI
from ac_service.app.api.v1.principles import router as principles_router
from ac_service.app.db.database import create_db_tables
from shared.security_middleware import add_security_headers # Import the shared middleware

app = FastAPI(title="Artificial Constitution (AC) Service")

# Apply the security headers middleware
app.middleware("http")(add_security_headers)

# Include the API router for principles
app.include_router(principles_router, prefix="/api/v1/principles", tags=["Principles"])

@app.on_event("startup")
def on_startup():
    # Create database tables if they don't exist
    create_db_tables()
    print("AC Service startup: Database tables check/creation initiated.")

@app.get("/")
async def root():
    return {"message": "Artificial Constitution Service is running. Use /api/v1/principles/docs for API documentation."}

# Placeholder for future health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}
