LOGS = [
    "INFO: Login request received",
    "WARNING: Database latency spike",
    "ERROR: Database timeout",
    "CRITICAL: Database connection pool exhausted",
]

def search_logs(query):
    query = query.lower()
    results = []
    for log in LOGS:
        if query in log.lower():
            results.append(log)
    return results