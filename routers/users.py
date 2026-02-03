from typing import Annotated
from fastapi.params import Depends, Path
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import HTTPException, APIRouter
from starlette import status
from models import Users
from database import get_db
from .auth import get_current_user

router = APIRouter(
    prefix="/user",
    tags=["user"])


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserVerification(BaseModel):
    password: str
    new_password: str = Field(min_length=6)

@router.get('/{user_id}', status_code=status.HTTP_200_OK)
async def get_user(user: user_dependency, db: db_dependency,user_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Authentication failed")
    return db.query(Users).filter(Users.id == user_id).first()

@router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(db: db_dependency, user: user_dependency, user_verification: UserVerification):
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Authentication failed")
    user_model = db.query(Users).filter(Users.id == user.get('id')).first()

    if not bcrypt_context.verify(user_verification.password, user_model.hashed_password):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incorrect password")
    user_model.hashed_password = bcrypt_context.hash(user_verification.new_password)

    db.add(user_model)
    db.commit()



