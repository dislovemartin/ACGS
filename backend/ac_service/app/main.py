from fastapi import FastAPI
from app.api.v1.principles import router as principles_router
from app.api.v1.constitutional_council import router as constitutional_council_router
from shared.security_middleware import SecurityHeadersMiddleware # Import the shared middleware

app = FastAPI(title="Artificial Constitution (AC) Service")

# Apply the security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Include the API routers
app.include_router(principles_router, prefix="/api/v1/principles", tags=["Principles"])
app.include_router(constitutional_council_router, prefix="/api/v1/constitutional-council", tags=["Constitutional Council"])

@app.on_event("startup")
def on_startup():
    print("AC Service startup: Service initialized.")

@app.get("/")
async def root():
    return {"message": "Artificial Constitution Service is running. Use /api/v1/principles/docs for API documentation."}

# Placeholder for future health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}
