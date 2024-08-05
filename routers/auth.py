from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field 
from database import SessionLocal
from models import Users
from starlette import status
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError

router = APIRouter(
    prefix = "/auth",
    tags = ["auth"]
)

SECRET_KEY = "d2f43f318f6277c2ad3a1e57d5d649baf8a68cb2fd6e2562b4a6a437e98e5500"
ALGORITHM = "HS256"

bcrypt_context = CryptContext(schemes = ["bcrypt"], deprecated = "auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl = "auth/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
form_data = Annotated[OAuth2PasswordRequestForm, Depends()]

class UserRequest(BaseModel):
    username: str = Field(..., min_length = 3, max_length = 100, example = "username")
    password: str = Field(..., min_length = 8, max_length = 100, example = "password")
    email: str = Field(..., min_length = 3, max_length = 50, example = "Email")
    name: str = Field(..., min_length = 3, max_length = 100, example = "Name")
    role: str = Field(..., max_length = 10, example = "user")

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/register", status_code = status.HTTP_201_CREATED)
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

@router.post("/login", response_model = Token)
async def login(form_data: form_data, db: db_dependency):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Invalid username or password")
    
    access_token = create_access_token(user.username, user.id, user.role, timedelta(minutes = 30))
    return { "access_token": access_token, "token_type": "bearer" }

def authenticate_user(db: db_dependency, username: str, password: str):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user

def create_access_token(username: str, user_id: int, role: str, expires_delta: timedelta):
    payload = {
        "sub": username,
        "id": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + expires_delta
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm = ALGORITHM)
    return token

async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    credentials_exception = HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Could not validate credentials")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms = [ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        user_role: str = payload.get("role")
        if username is None or user_id is None:
            raise credentials_exception
        
        return { "username": username, "id": user_id, "role": user_role }
    except JWTError:
        raise credentials_exception