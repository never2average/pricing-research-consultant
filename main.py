from fastapi import FastAPI
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from routes.experiments import router as experiments_router
from routes.deployment import router as deployment_router

thread_pool = ThreadPoolExecutor(max_workers=4)

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    thread_pool.shutdown(wait=True)

app = FastAPI(lifespan=lifespan)

app.include_router(experiments_router)
app.include_router(deployment_router)
