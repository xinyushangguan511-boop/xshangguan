from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.projects import router as projects_router
from app.routers.market import router as market_router
from app.routers.engineering import router as engineering_router
from app.routers.finance import router as finance_router
from app.routers.attachments import router as attachments_router
from app.routers.statistics import router as statistics_router

__all__ = [
    "auth_router",
    "users_router",
    "projects_router",
    "market_router",
    "engineering_router",
    "finance_router",
    "attachments_router",
    "statistics_router",
]
