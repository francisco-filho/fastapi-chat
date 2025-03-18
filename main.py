import os
from fastapi import FastAPI
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

app = FastAPI()

MODEL="gpt-4o-mini"

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

class ChatMessage(BaseModel):
    role: str
    content: str


@app.post("/chat")
async def chat(msg: str):
    message = ChatMessage(role="user", content=msg)
    completion = client.chat.completions.create(
        model=MODEL,
        messages=[message]
    )
    return completion.choices[0].message.content

