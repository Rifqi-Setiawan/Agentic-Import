import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.api.admin_routes import router as admin_router
from src.api.auth import router as auth_router
from src.api.clarifications import router as clarifications_router
from src.api.health import router as health_router
from src.api.hs import router as hs_router
from src.api.regulations import router as regulations_router
from src.api.reviews import router as reviews_router
from src.api.shipments import router as shipments_router
from src.api.run_reads import router as run_reads_router
from src.api.sse import router as sse_router
from src.core.config import settings

app = FastAPI(
    title="Artha API",
    description="Artha — Import Compliance Workspace (MVP v1.1)",
    version="1.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API v1 Router inclusion
api_prefix = "/api/v1"
app.include_router(auth_router, prefix=api_prefix)
app.include_router(shipments_router, prefix=api_prefix)
app.include_router(run_reads_router, prefix=api_prefix)
app.include_router(clarifications_router, prefix=api_prefix)
app.include_router(reviews_router, prefix=api_prefix)
app.include_router(regulations_router, prefix=api_prefix)
app.include_router(hs_router, prefix=api_prefix)
app.include_router(admin_router, prefix=api_prefix)
app.include_router(sse_router, prefix=api_prefix)

# Health router
app.include_router(health_router)
app.include_router(health_router, prefix=api_prefix)


# Public fixtures contain only explicitly fictitious demo PDFs, never uploads.
demo_invoice_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "demo", "invoices")
if os.path.isdir(demo_invoice_dir):
    app.mount("/data/demo/invoices", StaticFiles(directory=demo_invoice_dir), name="demo-invoices")

# Static frontend serving
frontend_dist = "/srv/hermes-control/services/agentic-import/frontend/dist"
if os.path.exists(frontend_dist):
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(frontend_dist, "index.html"))
else:
    @app.get("/")
    def root():
        return {
            "name": "Artha API",
            "version": "1.1.0",
            "documentation": "/docs",
            "health": "/health",
        }
