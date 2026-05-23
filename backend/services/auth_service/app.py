from fastapi import FastAPI
import random
import time
from prometheus_client import Counter, generate_latest, Histogram, CONTENT_TYPE_LATEST
from fastapi.responses import Response
from loguru import logger

app = FastAPI()

REQUEST_COUNT = Counter("login_request_total", "Total Login Requests")
ERROR_COUNT = Counter(
    "login_errors_total","Total Login Errors"
)
LATENCY = Histogram("login_latency_seconds", "Login Latency")




@app.get("/login")
def login():
    REQUEST_COUNT.inc()
    start = time.time()
    dice = random.randint(1,10)
    logger.info("Login request received")
    #simulate slow db
    if dice > 6:
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
    
    if dice > 9:
        ERROR_COUNT.inc()
        logger.critical("Database connection pool exhausted")
        raise Exception("DB Crashed")
    
    LATENCY.observe(time.time() - start)
    return {"status":"success"}


@app.get("/health")
def health():
    return {"status": "healthy}"}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
