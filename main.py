from fastapi import FastAPI
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from routes.deployment import router as deployment_router
from routes.experiments import router as experiments_router

thread_pool = ThreadPoolExecutor(max_workers=4)

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    thread_pool.shutdown(wait=True)

app = FastAPI(lifespan=lifespan)

app.include_router(experiments_router)
app.include_router(deployment_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)