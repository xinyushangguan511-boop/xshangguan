from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.routers import (
    auth_router,
    users_router,
    projects_router,
    market_router,
    engineering_router,
    finance_router,
    attachments_router,
    statistics_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown
    pass


app = FastAPI(
    title="Cross-Department MIS",
    description="Management Information System for Marketing, Engineering, and Finance departments",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(projects_router)
app.include_router(market_router)
app.include_router(engineering_router)
app.include_router(finance_router)
app.include_router(attachments_router)
app.include_router(statistics_router)


@app.get("/")
async def root():
    return {"message": "Cross-Department MIS API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
