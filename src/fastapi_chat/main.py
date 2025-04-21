import os
import json
import psycopg
import asyncio
from time import sleep
from fastapi import FastAPI
from fastapi.responses import Response, StreamingResponse
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

#MODEL="gpt-4o-mini"

config = {
    'gpt-4o-mini': {
        'url': 'https://api.openai.com/v1',
        'api_key': os.environ.get("OPENAI_API_KEY"),
    },
    'deepseek-r1:14b': {
        'url': 'http://127.0.0.1:11434/v1',
        'api_key': 'ollama',
    },
    'deepseek-r1:8b': {
        'url': 'http://127.0.0.1:11434/v1',
        'api_key': 'ollama',
    },
    'deepseek-r1:7b': {
        'url': 'http://127.0.0.1:11434/v1',
        'api_key': 'ollama',
    },
}


MODEL = 'deepseek-r1:8b'


class NewChat(BaseModel):
    name: str

class Chat(BaseModel):
    id: int
    name: str
    created_at: datetime 

class Message(BaseModel):
    role: str
    content: str

class ChatMessage(BaseModel):
    model: str = 'gpt-4o-mini'
    messages: list[Message] = []


app.history = []

def get_client(model: str):
    return OpenAI(
        base_url=config[model]['url'],
        api_key=config[model]['api_key']
    )

@app.get("/chat/{chat_id}")
def load_chat(chat_id: int):
    with psycopg.connect(f"host=localhost dbname=localchat user={DB_USER} password={DB_PASSWORD}") as conn:
        with conn.cursor() as cur:
            cur.execute("select c.role, c.content from chat_messages c where chat_id = %s", (chat_id, ))
            app.history = ([Message(role=c[0], content=c[1]) for c in cur.fetchall() if c[0] != 'string'])
            print('load_chats', app.history)
            return app.history

@app.delete("/chat/{chat_id}", status_code=204)
def delete_chat(chat_id: int):
    with psycopg.connect(f"host=localhost dbname=localchat user={DB_USER} password={DB_PASSWORD}") as conn:
        with conn.cursor() as cur:
            cur.execute("delete from chat_messages where chat_id = %s", (chat_id, ))
            cur.execute("delete from chat where id = %s", (chat_id, ))
    return Response(status_code=204)


@app.post("/chat/{chat_id}")
def chat(chat_id: int, chat_message: ChatMessage):
    client = get_client(chat_message.model)

    message = chat_message.messages[0]
    app.history.append(message)
    persist_chat(chat_id, message.role, message.content, model=chat_message.model)
    completion = client.chat.completions.create(
        model=chat_message.model,
        messages=app.history
    )
    response = completion.choices[0].message
    app.history.append(Message(role=response.role, content=response.content))
    persist_chat(chat_id, 'assistant', response.content, model=chat_message.model)
    return Message(role="assistant", content=response.content)


@app.post("/stream/{chat_id}")
async def stream(chat_id: int, chat_message: ChatMessage):
    client = get_client(chat_message.model)
    message = chat_message.messages[0]

    app.history.append(message)
    persist_chat(chat_id, message.role, message.content, model=chat_message.model)
    completion = client.chat.completions.create(
        model=chat_message.model,
        messages=app.history,
        stream=True
    )

    async def response_generator(comp):
        response = ""
        for chunk in comp:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                response += delta.content
                yield delta.content
            await asyncio.sleep(0.05)

        persist_chat(chat_id, 'assistant', response, model=chat_message.model)

    return StreamingResponse(response_generator(completion), media_type="text/event-stream")


@app.post("/chat", status_code=201)
def create_chat(new_chat: NewChat):
    with psycopg.connect(f"host=localhost dbname=localchat user={DB_USER} password={DB_PASSWORD}") as conn:
        with conn.cursor() as cur:
            cur.execute("insert into chat (name, created_at) values (%s, now())", (new_chat.name, ))


@app.get("/chat")
def list_chats():
    with psycopg.connect(f"host=localhost dbname=localchat user={DB_USER} password={DB_PASSWORD}") as conn:
        with conn.cursor() as cur:
            cur.execute("select c.id, c.name, c.created_at from chat c")
            return [Chat(id=c[0], name=c[1], created_at=c[2]) for c in cur.fetchall()]

def persist_chat(chat_id: int, role: str, content: str, model: str = MODEL):
    with psycopg.connect(f"host=localhost dbname=localchat user={DB_USER} password={DB_PASSWORD}") as conn:
        with conn.cursor() as cur:
            cur.execute("""
                        insert into chat_messages (chat_id, model, role, content)
                        values (%s, %s, %s, %s);
            """, (chat_id, model, role, content,))

