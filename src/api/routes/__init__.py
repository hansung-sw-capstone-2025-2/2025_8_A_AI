from .search import router as search_router
from .recommendations import router as recommendations_router
from .comparison import router as comparison_router

__all__ = [
    "search_router",
    "recommendations_router",
    "comparison_router",
]
