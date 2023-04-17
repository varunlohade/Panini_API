import os
from fastapi import FastAPI, HTTPException,File, UploadFile, HTTPException
from firebase_admin import credentials, firestore, initialize_app
from google.cloud import storage
from google.cloud.exceptions import NotFound
from uuid import uuid4
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

@app.post("/audio")
async def upload_audio(file: UploadFile = File(...), title: str = ""):
    # Generate a unique identifier for the audio file
    unique_id = str(uuid4())

    # Upload the file to Firebase Storage
    try:
        bucket = client.bucket("your-bucket-name.appspot.com")
        blob = bucket.blob(f"audio/{unique_id}.mp3")
        blob.upload_from_file(file.file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")

    # Store the file metadata in a Firestore collection
    db = firestore.client()
    audio_collection = db.collection('audio')
    audio_collection.add({
        'id': unique_id,
        'filename': file.filename,
        'title': title,
        'url': f"https://firebasestorage.googleapis.com/v0/b/your-bucket-name.appspot.com/o/audio%2F{unique_id}.mp3?alt=media"
    })

    return {"status": "success"}

@app.get("/audio/{audio_id}")
async def retrieve_audio(audio_id: str):
    # Retrieve the file metadata from the Firestore collection
    db = firestore.client()
    audio_collection = db.collection('audio')
    audio_doc = audio_collection.where('id', '==', audio_id).get()[0].to_dict()

    # Retrieve the file from Firebase Storage
    try:
        bucket = client.bucket("your-bucket-name.appspot.com")
        blob = bucket.blob(f"audio/{audio_id}.mp3")
        file_contents = blob.download_as_bytes()
    except NotFound:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve file: {str(e)}")

    return StreamingResponse(BytesIO(file_contents), media_type="audio/mpeg", headers={"Content-Disposition": f'attachment; filename="{audio_doc["filename"]}"'})