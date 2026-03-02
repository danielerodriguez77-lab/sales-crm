from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.router import api_router
from app.scheduler.scheduler import start_scheduler

app = FastAPI(title="Sales CRM API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"],
)

app.include_router(api_router)

scheduler = None


@app.on_event("startup")
def startup_event():
    global scheduler
    if settings.app_env != "test":
        scheduler = start_scheduler()


@app.on_event("shutdown")
def shutdown_event():
    global scheduler
    if scheduler:
        scheduler.shutdown()
        scheduler = None


@app.get("/health")
def health_check():
    return {"status": "ok"}
