import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

origins = ["http://localhost:4200"]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=['*']
)

MODEL="gpt-4o-mini"

history=[]

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

class ChatMessage(BaseModel):
    role: str
    content: str



@app.post("/chat/{chat_id}")
async def chat(chat_id: int, message: ChatMessage):
    history.append(message)
    completion = client.chat.completions.create(
        model=MODEL,
        messages=history
    )
    response = completion.choices[0].message
    history.append(response)
    return ChatMessage(role="assistant", content=response.content)

