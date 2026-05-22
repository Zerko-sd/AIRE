from fastapi import FastAPI
import random
import time
from prometheus_client import Counter, generate_latest, Histogram
from fastapi.responses import Response
from loguru import logger

app = FastAPI()

REQUEST_COUNT = Counter("request_count", "Total Request Count")
ERROR_COUNT = Counter(
    "login_errors_total","Total login requests"
)
LATENCY = Histogram("login_latency_seconds", "Login latency")




@app.get("/login")
def login():
    REQUEST_COUNT.inc()
    start = time.time()
    dice = random.randint(1,10)
    logger.info("Login request received")
    #simulate slow db
    if dice > 7:
        logger.warning("Database responding slowly")
        time.sleep(3)

    if dice > 8:
        ERROR_COUNT.inc()
        logger.error("database timeout occurred:")

        LATENCY.observe(time.time() - start)

        return {
            "status" : "error",
            "message": "Database timeout"
        }
    
    LATENCY.observe(time.time() - start)
    return {"status":"success"}


@app.get("/health")
def health():
    return {"status": "healthy}"}

@app.get("/metrics")
def metrics():
    return Response(generate_latest())
