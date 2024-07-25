from fastapi import FastAPI, HTTPException, Path, Depends
from starlette import status
from models import Todos, TodosRequest
from database import Base, engine, SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session

app = FastAPI()

Base.metadata.create_all(bind = engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@app.get("/")
async def get_all(db: db_dependency):
    return db.query(Todos).all()

@app.get("/todo/{todo_id}", status_code = status.HTTP_200_OK)
async def get_by_id(db: db_dependency, todo_id: int = Path(ge = 1)):
    todo = db.query(Todos).filter(Todos.id == todo_id).first()
    if todo is None:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "Todo not found.")
    
    return todo

@app.post("/todo", status_code = status.HTTP_201_CREATED)
async def create_todo(db: db_dependency, todo: TodosRequest):
    new_todo = Todos(**todo.model_dump())
    db.add(new_todo)
    db.commit()
    db.refresh(new_todo)
    return new_todo

@app.put("/todo/{todo_id}", status_code = status.HTTP_200_OK)
async def update_todo(db: db_dependency, todo: TodosRequest, todo_id: int = Path(ge = 1)):
    todo_to_update = db.query(Todos).filter(Todos.id == todo_id).first()
    if todo_to_update is None:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "Todo not found.")
    
    todo_to_update.title = todo.title
    todo_to_update.description = todo.description
    todo_to_update.priority = todo.priority
    todo_to_update.complete = todo.complete

    db.commit()
    db.refresh(todo_to_update)
    return todo_to_update

@app.delete("/todo/{todo_id}", status_code = status.HTTP_204_NO_CONTENT)
async def delete_todo(db: db_dependency, todo_id: int = Path(ge = 1)):
    todo_to_delete = db.query(Todos).filter(Todos.id == todo_id).first()
    if todo_to_delete is None:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "Todo not found.")
    
    db.delete(todo_to_delete)
    db.commit()