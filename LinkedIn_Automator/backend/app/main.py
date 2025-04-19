from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .db import test_connection
from .routes.User import router as user_router
from .routes.proxy import router as proxy_router
from .routes.Resume import router as resume_router


app = FastAPI(title="Job Automation API")

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # ✅ React dev server
        "http://localhost:8501",  # ✅ Streamlit (for redirects)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include only the user router
app.include_router(user_router)
app.include_router(proxy_router)
app.include_router(resume_router)

# Global OPTIONS handler for CORS preflight requests
@app.options("/{full_path:path}")
async def options_handler(request: Request):
    # Fix for React frontend - always use React URL for now
    # This ensures the Access-Control-Allow-Origin header matches the React frontend origin
    return JSONResponse(
        content="OK",
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "http://localhost:5173",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
            "Access-Control-Allow-Credentials": "true",
        }
    )

@app.get("/")
async def root():
    return {"message": "Job Automation API is running"}

@app.get("/health")
async def health_check():
    db_connected = await test_connection()
    return {
        "status": "healthy" if db_connected else "unhealthy",
        "database_connected": db_connected
    }