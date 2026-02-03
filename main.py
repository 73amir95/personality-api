from routers import auth, predict, users
from fastapi import FastAPI
import models
from database import engine
from fastapi.responses import RedirectResponse
from fastapi import Request
from routers.auth import get_current_user

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

@app.get("/")
async def root(request: Request):
    user = await get_current_user(request)
    if user:
        return RedirectResponse(url="/predict/")
    return RedirectResponse(url="/auth/login")
app.include_router(auth.router)
app.include_router(predict.router)
app.include_router(users.router)