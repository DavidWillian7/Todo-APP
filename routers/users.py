from fastapi import APIRouter, HTTPException, Path, Depends
from pydantic import BaseModel, Field
from starlette import status
from models import Todos, Users
from database import SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
from .auth import get_current_user
from passlib.context import CryptContext

router = APIRouter(
    prefix = "/user",
    tags = ["user"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[Session, Depends(get_current_user)]
bcrypt_context = CryptContext(schemes = ["bcrypt"], deprecated = "auto")

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    name: str
    role: str

class PasswordVerification(BaseModel):
    password: str = Field(..., min_length = 8, max_length = 100, example = "password")
    new_password: str = Field(..., min_length = 8, max_length = 100, example = "new_password")

@router.get("", status_code = status.HTTP_200_OK)
async def get_user(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Authentication failed.")
    
    user = db.query(Users).filter(Users.id == user.get("id")).first()
    user_response = UserResponse(
        id = user.id,
        username = user.username,
        email = user.email,
        name = user.name,
        role = user.role
    )
    return user_response

@router.put("/password", status_code = status.HTTP_204_NO_CONTENT)
async def change_password(user: user_dependency, db: db_dependency, password_verification: PasswordVerification):
    if user is None:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Authentication failed.")
    
    user = db.query(Users).filter(Users.id == user.get("id")).first()
    if not bcrypt_context.verify(password_verification.password, user.hashed_password):
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Invalid password.")
    
    user.hashed_password = bcrypt_context.hash(password_verification.new_password)
    db.add(user)
    db.commit()