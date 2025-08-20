# Imports padrão
import time
import random
import sys
from typing import List

# Imports de terceiros
import requests
from fastapi import FastAPI, Response, status, Request
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from opentelemetry.trace import Status, StatusCode, get_current_span
from opentelemetry.semconv.attributes.http_attributes import (
    HTTP_ROUTE, HTTP_REQUEST_METHOD, HttpRequestMethodValues
)

# Imports do projeto (usando as classes dos módulos otel/)
from otel.metrics import MetricsOTEL
from otel.tracing import TracingOTEL
from otel.logs import OTelLogger
import config

# Instanciando as classes OTEL
metrics_otel = MetricsOTEL()
tracing_otel = TracingOTEL()
logger = OTelLogger().logger  # Usa o logger padrão da classe

# Acessando os instrumentos de métricas
requests_counter = metrics_otel.requests_counter
active_requests_gauge = metrics_otel.active_requests_gauge
response_time_histogram = metrics_otel.response_time_histogram

# Acessando tracer e propagator
tracer = tracing_otel.get_tracer()
propagator = tracing_otel.get_propagator()

app = FastAPI()

# ===================== Funções Auxiliares =====================

def get_log_context(operation: str) -> dict:
    span_context = get_current_span().get_span_context()
    context = {
        "service_name": config.APP_NAME,
        "operation": operation
    }
    if span_context.is_valid:
        context.update({
            "trace_id": format(span_context.trace_id, "032x"),
            "span_id": format(span_context.span_id, "016x")
        })
    return context

def simulate_latency():
    if config.APP_LATENCY > 0:
        simulated_latency = random.randint(0, config.APP_LATENCY)
        logger.debug("Simulando latência", extra={"simulated_latency_ms": simulated_latency})
        time.sleep(simulated_latency / 1000)
        return simulated_latency
    return 0

def propagate_downstream(original_payload, log_context, response):
    if not config.APP_URL_DESTINO:
        return original_payload
    urls = config.APP_URL_DESTINO.split(',')
    for url in urls:
        with tracer.start_as_current_span("send-request") as child_span:
            try:
                logger.debug("Enviando requisição para serviço downstream", extra={**log_context, "destination_url": url})
                headers = {}
                propagator.inject(headers)
                resp = requests.post(f"{url}/process", json=original_payload, headers=headers, timeout=5)
                child_span.set_attribute("http.status_code", resp.status_code)
                if resp.status_code == 200:
                    original_payload = resp.json()
                else:
                    response.status_code = status.HTTP_502_BAD_GATEWAY
                    logger.error("Erro de status na requisição externa", extra={**log_context, "destination_url": url, "response_status": resp.status_code})
                    return {"error": f"Erro ao enviar para {url}: {resp.status_code}"}
            except requests.RequestException as e:
                response.status_code = status.HTTP_400_BAD_REQUEST
                logger.error("Falha na requisição externa", extra={**log_context, "error_message": str(e), "destination_url": url}, exc_info=True)
                get_current_span().record_exception(Exception(e))
                get_current_span().set_status(Status(StatusCode.ERROR))
                return {"error": f"Falha na requisição para {url}: {str(e)}"}
    return original_payload

# ===================== Endpoints =====================

@app.get("/")
def read_root():
    logger.info("Endpoint raiz acessado", extra={"service_name": config.APP_NAME, "endpoint": "/", "operation": "health_check"})
    active_requests_gauge.set(1, {"app": config.APP_NAME})
    requests_counter.add(1, {"app": config.APP_NAME, "endpoint": "/"})
    start_time = time.time()
    elapsed_time = time.time() - start_time
    response_time_histogram.record(elapsed_time, {"app": config.APP_NAME, "endpoint": "/"})
    return {"message": f"Esse é o serviço {config.APP_NAME}"}

@app.get("/metrics")
def metrics():
    logger.debug("Endpoint de métricas acessado", extra={"service_name": config.APP_NAME, "endpoint": "/metrics", "operation": "metrics_export"})
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/process")
def process_request(payload: List[str], response: Response, request: Request):
    log_context = get_log_context("process_request")
    logger.info("Iniciando processamento de requisição", extra={**log_context, "payload": payload, "payload_size": len(payload)})
    context = propagator.extract(request.headers)
    with tracer.start_as_current_span("process-request", context=context) as main_span:
        original_payload = payload.copy() + [config.APP_NAME]
        main_span.set_attribute(HTTP_ROUTE, "/process")
        main_span.set_attribute(HTTP_REQUEST_METHOD, HttpRequestMethodValues.POST)
        main_span.set_attribute("app.name", config.APP_NAME)
        main_span.set_attribute("payload.original", str(payload))
        main_span.set_attribute("payload.modified", str(original_payload))
        main_span.add_event("Início do processamento", {"payload_tamanho": f"{sys.getsizeof(payload)} bytes"})
        logger.debug("Span principal iniciado", extra={**log_context, "span_name": "process-request", "payload_bytes": sys.getsizeof(payload)})
        start_time = time.time()
        active_requests_gauge.set(10, {"app": config.APP_NAME})
        requests_counter.add(1, {"app": config.APP_NAME, "endpoint": "/process"})
        simulate_latency()
        result = propagate_downstream(original_payload, log_context, response)
        elapsed_time = time.time() - start_time
        main_span.set_status(Status(StatusCode.OK))
        logger.info("Processamento concluido com sucesso", extra={**log_context, "result_payload": result, "processing_duration": elapsed_time})
    response_time_histogram.record(elapsed_time, {"app": config.APP_NAME, "endpoint": "/process"})
    return result