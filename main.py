from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api import search_router, recommendations_router, comparison_router
from src.core import Database, PanelSearchException


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await Database.close_pool()


app = FastAPI(
    title="Panel Search API",
    version="2.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["root"])
async def root():
    return {
        "message": "Panel Search API",
        "version": "2.1.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "status": "running",
        "endpoints": {
            "search": "/api/search",
            "recommendations": "/api/quick-search",
            "comparison": "/api/cohort-comparison",
        }
    }


@app.get("/health", tags=["system"])
async def health_check():
    return {
        "status": "healthy",
        "version": "2.1.0",
        "service": "panel-search-api"
    }


@app.get("/api/info", tags=["system"])
async def api_info():
    return {
        "title": "Panel Search API",
        "version": "2.1.0",
        "endpoints": {
            "search": {
                "prefix": "/api/search",
                "description": "패널 검색 API",
                "endpoints": [
                    "POST /api/search/",
                    "POST /api/search/search-result/{search_id}/refine",
                    "GET /api/search/search-result/{search_id}/info",
                    "GET /api/search/available-filters"
                ]
            },
            "recommendations": {
                "prefix": "/api/quick-search",
                "description": "개인화 추천 API",
                "endpoints": [
                    "POST /api/quick-search/recommendations",
                    "POST /api/quick-search/recommendations/by-member",
                    "GET /api/quick-search/health"
                ]
            },
            "comparison": {
                "prefix": "/api/cohort-comparison",
                "description": "코호트 비교 분석 API",
                "endpoints": [
                    "POST /api/cohort-comparison/compare",
                    "GET /api/cohort-comparison/metrics"
                ]
            }
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json"
        }
    }


app.include_router(search_router)
app.include_router(recommendations_router)
app.include_router(comparison_router)


@app.exception_handler(PanelSearchException)
async def panel_search_exception_handler(request, exc: PanelSearchException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.code,
            "message": exc.message,
            "details": exc.details
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": str(exc),
            "path": str(request.url)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
