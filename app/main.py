from fastapi import FastAPI

from app.api.routes.webhook import router as webhook_router


app = FastAPI(title="Algorithm Insight Automator (PoC)")


app.include_router(webhook_router)

