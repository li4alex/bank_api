from fastapi import FastAPI
from api import admin, customer

app = FastAPI(
    title="Core Banking REST API",
    description="A web API wrapping administrative and customer banking pipelines.",
    version="1.0.0"
)

# Connect the modular routers to the main application engine
app.include_router(admin.router)
app.include_router(customer.router)