from fastapi import FastAPI
from api import admin, customer
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Core Banking REST API",
    description="A web API wrapping administrative and customer banking pipelines.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with your exact frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect the modular routers to the main application engine
app.include_router(admin.router)
app.include_router(customer.router)