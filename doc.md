Documentação do Sistema de Monitoramento e Métricas com Prometheus
Visão Geral
Este sistema configura uma aplicação simples em Flask, expõe métricas usando o Prometheus e cria alertas para monitoramento. O ambiente foi implementado em Kubernetes e utiliza o Prometheus para coletar métricas personalizadas da aplicação e disparar alertas quando certos limiares são atingidos. O sistema é escalável, pois a aplicação é executada com múltiplas réplicas e está configurada para ser exposta via LoadBalancer.

Objetivo
A intenção desse setup é:

Monitorar uma aplicação com Prometheus.

Expor métricas personalizadas de requisições recebidas pela aplicação.

Gerar alertas quando a aplicação estiver recebendo mais de 5 requisições por minuto.

Tornar a aplicação acessível externamente usando LoadBalancer no Kubernetes.

Componentes do Sistema
Aplicação Flask (Python)

A aplicação é uma API simples em Flask, que oferece duas rotas:

/: A cada requisição a esta rota, a aplicação incrementa um contador de requisições.

/metrics: Exibe as métricas no formato que o Prometheus consegue coletar.

Deployment Kubernetes

A aplicação é executada como um Deployment Kubernetes, com duas réplicas para alta disponibilidade. A aplicação escuta na porta 5000.

ServiceMonitor

Um ServiceMonitor é configurado para que o Prometheus consiga coletar as métricas expostas pela aplicação no endpoint /metrics.

Prometheus Alert Rules (Regras de Alerta)

O Prometheus é configurado com uma regra de alerta que verifica se a aplicação recebe mais de 5 requisições por minuto. Caso a condição seja atendida por mais de um minuto, um alerta é disparado.

Service Kubernetes

O Service do Kubernetes expõe a aplicação para o tráfego externo, usando um LoadBalancer. O tráfego é encaminhado para a porta 5000 do pod, mas é acessível externamente na porta 80.

Passo a Passo de Configuração
1. Criando a Aplicação Flask
A aplicação Flask é responsável por gerar e expor métricas para o Prometheus. O código da aplicação define um contador de requisições e expõe essas métricas na rota /metrics.

Código:

python
Copiar
Editar
from flask import Flask
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# Criando uma métrica
REQUEST_COUNT = Counter("app_requests_total", "Total de requisições")

@app.route("/")
def home():
    REQUEST_COUNT.inc()  # Incrementa o contador a cada requisição
    return "Olá, mundo!"

@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
REQUEST_COUNT.inc(): A cada requisição à rota /, incrementa o contador app_requests_total.

/metrics: Exibe as métricas geradas pela aplicação no formato que o Prometheus pode ler.

2. Dockerfile para Containerizar a Aplicação
O Dockerfile define como a aplicação Flask será empacotada e executada em um container Docker.

Código:

dockerfile
Copiar
Editar
FROM python:3.13-slim
WORKDIR /app
COPY app.py .
RUN pip install flask prometheus_client
EXPOSE 5000
CMD ["python", "app.py"]
Imagem base: Utiliza a imagem python:3.13-slim para criar o ambiente da aplicação.

Instalação das dependências: Instala o Flask e o cliente Prometheus.

Exposição da porta 5000: A aplicação Flask escutará nessa porta dentro do container.

3. Deployment Kubernetes
O Deployment Kubernetes cria a aplicação em 2 réplicas, garantindo alta disponibilidade. Ele define o número de réplicas, a imagem do container, e a porta a ser exposta.

Código:

yaml
Copiar
Editar
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-metrics
spec:
  replicas: 2  # Cria 2 réplicas da aplicação para maior disponibilidade
  selector:
    matchLabels:
      app: app-metrics
  template:
    metadata:
      labels:
        app: app-metrics
    spec:
      containers:
      - name: app-metrics
        image: welignton/app-metrics:v1  # A imagem Docker com a aplicação Flask
        ports:
        - containerPort: 5000
replicas: 2: Cria duas réplicas da aplicação para garantir que ela esteja disponível mesmo se um dos pods falhar.

containerPort: 5000: Define a porta em que a aplicação vai escutar dentro do container.

4. ServiceMonitor para o Prometheus Coletar Métricas
O ServiceMonitor configura o Prometheus para monitorar a aplicação. Ele faz a coleta das métricas a cada 15 segundos no endpoint /metrics.

Código:

yaml
Copiar
Editar
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: app-monitor
  labels:
    release: prometheus-monitoring
spec:
  selector:
    matchLabels:
      app: app-metrics
  endpoints:
  - port: http
    path: /metrics
    interval: 15s  # O Prometheus irá coletar as métricas a cada 15 segundos
selector: Garante que o Prometheus monitore o serviço correto, que tem o rótulo app: app-metrics.

interval: 15s: Define que o Prometheus irá coletar as métricas a cada 15 segundos.

5. Definindo as Regras de Alerta no Prometheus
A regra de alerta é configurada para disparar quando a aplicação receber mais de 5 requisições por minuto. A regra também define um tempo de espera de 1 minuto para evitar alertas falsos.

Código:

yaml
Copiar
Editar
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: app-alerts
  labels:
    release: prometheus-monitoring
spec:
  groups:
  - name: app.rules
    rules:
    - alert: MuitasRequisicoes
      expr: rate(app_requests_total[1m]) > 5  # Verifica se a taxa de requisições é maior que 5 por minuto
      for: 1m  # O alerta será disparado se essa condição persistir por 1 minuto
      labels:
        severity: warning
      annotations:
        summary: "Muitas requisições na aplicação"
        description: "A aplicação está recebendo muitas requisições"
expr: Define a expressão que verifica a taxa de requisições.

for: 1m: O alerta só será disparado se a condição persistir por 1 minuto, o que ajuda a evitar alertas falsos.

severity: warning: Classifica o alerta como "warning".

6. Service Kubernetes para Expor a Aplicação Externamente
O Service cria um ponto de entrada para a aplicação, expondo a porta 5000 do pod para a porta 80 no LoadBalancer, permitindo que a aplicação seja acessada externamente.

Código:

yaml
Copiar
Editar
apiVersion: v1
kind: Service
metadata:
  name: app-service
  labels:
    app: app-metrics
spec:
  selector:
    app: app-metrics
  ports:
    - name: http
      protocol: TCP
      port: 80  # Porta externa acessível
      targetPort: 5000  # Porta interna do container
  type: LoadBalancer  # Expõe o serviço externamente
type: LoadBalancer: Expõe a aplicação ao tráfego externo.

port: 80 e targetPort: 5000: Redireciona o tráfego da porta 80 para a porta 5000 dentro do pod.

Fluxo de Trabalho
Deployment cria duas réplicas da aplicação Flask.

O ServiceMonitor configura o Prometheus para coletar métricas da aplicação a cada 15 segundos.

Prometheus avalia as métricas e, caso a condição do alerta (mais de 5 requisições por minuto) seja atendida, o alerta é disparado.

O Service expõe a aplicação à internet, permitindo acessá-la através do LoadBalancer na porta 80.

Conclusão
Esse sistema oferece uma solução simples para monitorar a quantidade de requisições recebidas por uma aplicação, além de expô-la externamente para acesso público. Ele utiliza o Prometheus para monitorar e alertar sobre anomalias nas requisições e é totalmente integrado ao Kubernetes para escalabilidade e gerenciamento eficiente.