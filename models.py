from pydantic import BaseModel, Field
from database import Base
from sqlalchemy import Column, Integer, String, Boolean

class Todos(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key = True, index = True)
    title = Column(String)
    description = Column(String)
    priority = Column(Integer)
    complete = Column(Boolean, default = False)

class TodosRequest(BaseModel):
    title: str = Field(..., min_length = 3, max_length = 100,example = "Title of the todo")
    description: str = Field(..., min_length = 3, max_length = 200, example = "Description of the todo")
    priority: int = Field(..., ge = 1, le = 5, example = 1)
    complete: bool = Field(..., example = False)