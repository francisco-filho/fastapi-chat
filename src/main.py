import os
import psycopg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel
from datetime import datetime

load_dotenv()

DB_USER=os.environ['DB_USER']
DB_PASSWORD=os.environ['DB_PASSWORD']

origins = ["http://localhost:4200"]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=['*']
)

MODEL="gpt-4o-mini"


client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

class Chat(BaseModel):
    id: int
    created_at: datetime 

class ChatMessage(BaseModel):
    role: str
    content: str

app.history = []

@app.get("/chat/{chat_id}")
def load_chat(chat_id: int):
    with psycopg.connect(f"host=localhost dbname=localchat user={DB_USER} password={DB_PASSWORD}") as conn:
        with conn.cursor() as cur:
            cur.execute("select c.role, c.content from chat_messages c where chat_id = %s", (chat_id, ))
            app.history = ([ChatMessage(role=c[0], content=c[1]) for c in cur.fetchall()])
            print('load_chats', app.history)
            return app.history
     

@app.post("/chat/{chat_id}")
async def chat(chat_id: int, message: ChatMessage):
    app.history.append(message)
    persist_chat(chat_id, message.role, message.content)
    completion = client.chat.completions.create(
        model=MODEL,
        messages=app.history
    )
    response = completion.choices[0].message
    app.history.append(ChatMessage(role=response.role, content=response.content))
    print(app.history)
    persist_chat(chat_id, 'assistant', response.content)
    return ChatMessage(role="assistant", content=response.content)

@app.post("/chat", status_code=201)
def create_chat():
    with psycopg.connect(f"host=localhost dbname=localchat user={DB_USER} password={DB_PASSWORD}") as conn:
        with conn.cursor() as cur:
            cur.execute("insert into chat (created_at) values (now())")


@app.get("/chat")
def list_chats():
    with psycopg.connect(f"host=localhost dbname=localchat user={DB_USER} password={DB_PASSWORD}") as conn:
        with conn.cursor() as cur:
            cur.execute("select c.* from chat c")
            return [Chat(id=c[0], created_at=c[1]) for c in cur.fetchall()]

def persist_chat(chat_id: int, role: str, content: str, model: str = MODEL):
    with psycopg.connect(f"host=localhost dbname=localchat user={DB_USER} password={DB_PASSWORD}") as conn:
        with conn.cursor() as cur:
            cur.execute("""
                        insert into chat_messages (chat_id, model, role, content)
                        values (%s, %s, %s, %s);
            """, (chat_id, model, role, content,))

