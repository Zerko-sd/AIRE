from tools.log_tool import search_logs
from tools.prometheus_tool import query_prometheus

TOOL_DESCRIPTIONS = """
Available tools:

1. search_logs(query)
- Search application logs
- Valid queries:
  - "database"
  - "timeout"
  - "login"
  - "connection"

2. query_prometheus(query)
- Query Prometheus metrics

VALID metrics:
- login_requests_total
- login_errors_total
- up

Examples:
query_prometheus("login_errors_total")
query_prometheus("up")
"""
TOOLS = {
    "search_logs": search_logs,
    "query_prometheus": query_prometheus
}
