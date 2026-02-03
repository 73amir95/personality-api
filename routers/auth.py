import os
from datetime import timedelta, datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, Request, Form, Response
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import HTMLResponse, RedirectResponse
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from starlette import status
from database import get_db
from models import Users
from fastapi.templating import Jinja2Templates

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

templates = Jinja2Templates(directory="templates")
SECRET_KEY = os.getenv("SECRET_KEY", "your-very-secret-key-change-me")
ALGORITHM = "HS256"

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token", auto_error=False)

db_dependency = Annotated[Session, Depends(get_db)]

def authenticate_user(username: str, password: str, db):
    user = db.query(Users).filter(Users.username == username).first()
    if not user or not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user


def create_access_token(username: str, user_id: int, expires_delta: timedelta):
    encode = {'sub': username, 'id': user_id}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(request: Request):

    token = request.cookies.get("access_token")
    if not token or not token.startswith("Bearer "):
        return None

    try:
        token = token.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        if username is None or user_id is None:
            return None
        return {'username': username, 'id': user_id}
    except JWTError:
        return None


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    token = request.cookies.get("access_token")
    if token:
        try:
            token_str = token.split(" ")[1]
            jwt.decode(token_str, SECRET_KEY, algorithms=[ALGORITHM])
            return RedirectResponse(url="/predict/", status_code=302)
        except:
            pass

    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register-process")
async def register_process(
        db: db_dependency,
        username: str = Form(...),
        email: str = Form(...),
        first_name: str = Form(...),
        last_name: str = Form(...),
        password: str = Form(...)
):
    existing_user = db.query(Users).filter(Users.username == username).first()
    if existing_user:
        return HTMLResponse("Username already exists. <a href='/auth/register'>Go back</a>")

    new_user = Users(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        hashed_password=bcrypt_context.hash(password),
        is_active=True
    )
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)


@router.post("/login-process")
async def login_process(
        response: Response,
        db: db_dependency,
        username: str = Form(...),
        password: str = Form(...)
):
    user = authenticate_user(username, password, db)
    if not user:
        return HTMLResponse("Invalid Credentials. <a href='/auth/login'>Try again</a>")

    token = create_access_token(user.username, user.id, timedelta(minutes=60))
    redirect = RedirectResponse(url="/predict/", status_code=status.HTTP_302_FOUND)
    redirect.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        max_age=3600,
        samesite="lax"
    )
    return redirect


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response