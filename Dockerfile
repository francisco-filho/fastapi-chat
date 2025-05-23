FROM python:3.11-alpine3.21
#FROM python:3.11.11-bookworm

RUN mkdir /app
WORKDIR /app

COPY src ./src
COPY requirements.txt ./

RUN pip install --no-cache-dir -r /app/requirements.txt

EXPOSE 8000

CMD ["fastapi", "run", "src/fastapi_chat/main.py"]
