from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "hello world"}

@app.get("/item/{item_id}")
def get_item(item_id: int):
    return {"item_id": item_id}
