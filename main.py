from fastapi import FastAPI
from routers import offer, update, view

app = FastAPI()

app.include_router(offer.router)
app.include_router(update.router)
app.include_router(view.router)
