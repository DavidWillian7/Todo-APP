from fastapi import APIRouter, HTTPException, Path, Depends
from starlette import status
from models import Todos
from database import SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
from .auth import get_current_user

router = APIRouter(
    prefix = "/admin",
    tags = ["admin"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[Session, Depends(get_current_user)]

@router.get("/todo", status_code = status.HTTP_200_OK)
async def get_all(user: user_dependency, db: db_dependency):
    if user is None or user.get("role") != "admin":
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Authentication failed.")
    
    return db.query(Todos).all()

@router.delete("/todo/{todo_id}", status_code = status.HTTP_204_NO_CONTENT)
async def delete_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(ge = 1)):
    if user is None or user.get("role") != "admin":
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Authentication failed.")
    
    todo = db.query(Todos).filter(Todos.id == todo_id).first()
    if todo is None:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "Todo not found.")
    
    db.delete(todo)
    db.commit()