from typing import Annotated
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field 
from database import SessionLocal
from models import Users
from starlette import status
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter()

bcrypt_context = CryptContext(schemes = ["bcrypt"], deprecated = "auto")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
form_data = Annotated[OAuth2PasswordRequestForm, Depends()]

class UserRequest(BaseModel):
    username: str = Field(..., min_length = 3, max_length = 100, example = "Username")
    password: str = Field(..., min_length = 8, max_length = 100, example = "Password")
    email: str = Field(..., min_length = 3, max_length = 50, example = "Email")
    name: str = Field(..., min_length = 3, max_length = 100, example = "Name")
    role: str = Field(..., max_length = 10, example = "user")

@router.post("/auth/register", status_code = status.HTTP_201_CREATED)
async def create_user(db: db_dependency, user_request: UserRequest):
    new_user = Users(
        username = user_request.username,
        hashed_password = bcrypt_context.hash(user_request.password),
        email = user_request.email,
        name = user_request.name,
        role = user_request.role,
        is_active = True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/auth/login")
async def login(form_data: form_data, db: db_dependency):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        return { "message": "Invalid credentials." }
    
    return { "message": "Successful Authentication." }

def authenticate_user(db: db_dependency, username: str, password: str):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return True