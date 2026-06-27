from fastapi import FastAPI
from contextlib import asynccontextmanager
import utils
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import routers
from settings import AppSettings


@asynccontextmanager
async def lifespan(app: FastAPI):
    await utils.InitUtils.seed_db()
    
    yield



app = FastAPI(
    lifespan=lifespan
)
app_settings = AppSettings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=app_settings.ALLOWED_HOSTS
)



app.include_router(routers.root_route)
