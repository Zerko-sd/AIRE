import time
from agents.observer.prometheus_tool import query_prometheus
from datetime import datetime
from backend.models.incident import Incident
from backend.database.save_incident import save_incident

ERROR_THRESHOLD =0.05

while True:
    try:
        result = query_prometheus("rate(login_errors_total[1m])")
        value = float(result['data']['result'][0]['value'][1])
        print(f"Current login errors: {value}")

        if value > ERROR_THRESHOLD:
            incident = Incident(
                title="High Login Error Rate",
                severity="High",
                services="Authentication Service",
                metric="login_errors_total",
                value=value,
                created_at=datetime.now()
            )
            print(incident.model_dump_json(indent = 2))
            save_incident(incident)

    except Exception as e:
        print(f"Error querying Prometheus: {e}")
    time.sleep(10)  