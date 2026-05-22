from fastapi import FastAPI
import random
import time
from prometheus_client import Counter, generate_latest
from fastapi.responses import Response
from loguru import logger

app = FastAPI()

REQUEST_COUNT = Counter("request_count", "Total Request Count")


@app.get("/login")
def login():
    if random.randint(1,10) > 7:
        return {"error: db timeout"}
        logger.error("database timeout")
    
    return {"status":"success"}


@app.get("/health")
def health():
    return {"status": "healthy}"}

@app.get("/metrics")
def metrics():
    return Response(generate_latest())
