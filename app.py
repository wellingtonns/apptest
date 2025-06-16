from flask import Flask, request, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time

app = Flask(__name__)

# Métrica: contador de requisições, com label por rota
REQUEST_COUNT = Counter(
    "app_requests_total", "Total de requisições por rota", ["method", "endpoint"]
)

# Métrica: tempo de resposta por rota
REQUEST_LATENCY = Histogram(
    "app_request_latency_seconds", "Tempo de resposta por rota", ["method", "endpoint"]
)

# Middleware para métricas automáticas
@app.before_request
def start_timer():
    request.start_time = time.time()

@app.after_request
def record_metrics(response):
    latency = time.time() - request.start_time
    REQUEST_COUNT.labels(request.method, request.path).inc()
    REQUEST_LATENCY.labels(request.method, request.path).observe(latency)
    return response

@app.route("/")
def home():
    return "Olá, mundo!"

@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
