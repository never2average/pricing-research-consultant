from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from routes.deployment import router as deployment_router
from routes.experiments import router as experiments_router
from routes.product_routes import router as product_router
from routes.customer_segments import router as customer_segment_router
from routes.data_sources import router as data_sources_router

thread_pool = ThreadPoolExecutor(max_workers=4)

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    thread_pool.shutdown(wait=True)

app = FastAPI(lifespan=lifespan, title="Pricing Research Consultant API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(experiments_router)
app.include_router(deployment_router)
app.include_router(product_router)
app.include_router(customer_segment_router)
app.include_router(data_sources_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)