FROM python:3.11

WORKDIR /app

COPY . .

RUN pip install fastapi uvicorn prometheus_client loguru

CMD ["uvicorn","app:app","--host","0.0.0.0","--port","8000"]