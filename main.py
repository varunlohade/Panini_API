import os
from fastapi import FastAPI, HTTPException
from firebase_admin import credentials, firestore, initialize_app

from pydantic import BaseModel
from typing import Optional, List
from google.cloud.firestore_v1 import DocumentSnapshot

# Initialize Firestore
cred = credentials.Certificate("firebase_key.json")
default_app = initialize_app(cred)
db = firestore.client()

# Initialize FastAPI app
app = FastAPI()

# Your FastAPI routes and logic will go here


class ToDoItem(BaseModel):
    title: str
    completed: Optional[bool] = False

@app.get("/")
async def root():
    return {"message": "hello"}

@app.get("/todos/", response_model=List[ToDoItem])
async def get_todos():
    todos = []
    for doc in db.collection("todos").stream():
        todos.append(ToDoItem(**doc.to_dict()))
    return todos


@app.post("/todos/")
async def create_todo(todo: ToDoItem):
    doc_ref = db.collection("todos").document()
    doc_ref.set(todo.dict())
    return {"id": doc_ref.id}


@app.put("/todos/{todo_id}")
async def update_todo(todo_id: str, todo: ToDoItem):
    doc_ref = db.collection("todos").document(todo_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="ToDo item not found")

    doc_ref.set(todo.dict())
    return {"status": "updated"}


@app.delete("/todos/{todo_id}")
async def delete_todo(todo_id: str):
    doc_ref = db.collection("todos").document(todo_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="ToDo item not found")

    doc_ref.delete()
    return {"status": "deleted"}
