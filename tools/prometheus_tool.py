import requests 
PROMETHEUS_URL = "http://localhost:9090"

def query_prometheus(query):
    response = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": query})
    data =  response.json()

    try:
        value = data["data"]["result"][0]["value"][1]
        return value
    except:
        return data