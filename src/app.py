import time
import random
import requests
from fastapi import FastAPI, Response, status, Request
from typing import List
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from otel.metrics import requests_counter, active_requests_gauge, response_time_histogram
from otel.tracing import tracer, propagator
import sys
from opentelemetry.trace import Status, StatusCode
from opentelemetry.semconv.attributes.http_attributes import (
    HTTP_ROUTE,
    HTTP_REQUEST_METHOD,
    HttpRequestMethodValues
)
import config

from otel.logs import logger
from opentelemetry.trace import get_current_span

app = FastAPI()

@app.get("/")
def read_root():
    # Log estruturado para endpoint raiz
    logger.info(
        "Endpoint raiz acessado",
        extra={
            "service_name": config.APP_NAME,
            "endpoint": "/",
            "operation": "health_check"
        }
    )
    
    active_requests_gauge.set(1, {"app": config.APP_NAME})
    requests_counter.add(1, {"app": config.APP_NAME, "endpoint": "/"})
    start_time = time.time()
    elapsed_time = time.time() - start_time
    response_time_histogram.record(elapsed_time, {"app": config.APP_NAME, "endpoint": "/"})
    return {"message": f"Esse é o serviço {config.APP_NAME}"}

@app.get("/metrics")
def metrics():
    # Log estruturado para endpoint de métricas
    logger.debug(
        "Endpoint de métricas acessado",
        extra={
            "service_name": config.APP_NAME,
            "endpoint": "/metrics",
            "operation": "metrics_export"
        }
    )
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/process")
def process_request(payload: List[str], response: Response, request: Request):
    """
    Endpoint que processa um payload, simula falhas e latência variável,
    e propaga a requisição para outros serviços.
    """

    # Obter informações do span atual para correlação
    current_span = get_current_span()
    span_context = current_span.get_span_context()
    
    # Criar contexto base para logs
    log_context = {
        "service_name": config.APP_NAME,
        "operation": "process_request"
    }
    
    # Adicionar informações de trace se disponíveis
    if span_context.is_valid:
        log_context.update({
            "trace_id": format(span_context.trace_id, "032x"),
            "span_id": format(span_context.span_id, "016x")
        })

    # Log de início do processamento com detalhes da configuração
    logger.info(
        "Iniciando processamento de requisição",
        extra={
            **log_context,
            "payload": payload.copy(),
            "payload_size": len(payload),
            "app_config": {
                "error_rate": config.APP_ERRORS,
                "max_latency": config.APP_LATENCY,
                "destinations": config.APP_URL_DESTINO.split(',') if config.APP_URL_DESTINO else []
            }
        }
    )

    context = propagator.extract(request.headers)

    with tracer.start_as_current_span("process-request", context=context) as main_span:

        original_payload = payload.copy()
        original_payload.append(config.APP_NAME)

        main_span.set_attribute(HTTP_ROUTE, "/process")
        main_span.set_attribute(HTTP_REQUEST_METHOD, HttpRequestMethodValues.POST)
        main_span.set_attribute("app.name", config.APP_NAME)
        main_span.set_attribute("payload.original", str(payload))
        main_span.set_attribute("payload.modified", str(original_payload))


        main_span.add_event("Início do processamento", 
                {"payload_tamanho": f"{sys.getsizeof(payload)} bytes"}
        )
        
        # Log do início do span principal
        logger.debug(
            "Span principal iniciado",
            extra={
                **log_context,
                "span_name": "process-request",
                "payload_bytes": sys.getsizeof(payload)
            }
        )

        start_time = time.time()

        active_requests_gauge.set(10, {"app": config.APP_NAME})

        requests_counter.add(1, {"app": config.APP_NAME, "endpoint": "/process"})

        original_payload = payload.copy()
        original_payload.append(config.APP_NAME)

        # Simulação de latência variável
        if config.APP_LATENCY > 0:
            simulated_latency = random.randint(0, config.APP_LATENCY)  # Define um atraso aleatório entre 0 e APP_LATENCY
            
            logger.debug(
                "Simulando latência",
                extra={
                    **log_context,
                    "simulated_latency_ms": simulated_latency,
                    "max_latency_ms": config.APP_LATENCY
                }
            )
            
            time.sleep(simulated_latency / 1000)  # Converte ms para segundos

        # Simulação de erro com base na porcentagem definida
        if random.randint(1, 100) <= config.APP_ERRORS:
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

            error_msg = f"Erro simulado em {config.APP_NAME}"
            
            # Log estruturado do erro
            logger.error(
                "Erro simulado durante processamento",
                extra={
                    **log_context,
                    "error_message": error_msg,
                    "error_type": "simulated_error",
                    "error_percentage": config.APP_ERRORS,
                    "payload": payload.copy()
                }
            )

            logger.critical(
                "Erro fatal simulado durante processamento",
                extra={
                    **log_context,
                    "error_message": error_msg,
                    "error_type": "simulated_error",
                    "error_percentage": config.APP_ERRORS,
                    "payload": payload.copy()
                }
            )

            main_span.record_exception(Exception(error_msg))
            main_span.set_status(Status(StatusCode.ERROR))
            main_span.set_attribute("http.status_code", status.HTTP_500_INTERNAL_SERVER_ERROR)

            return {"error": error_msg}

        # Se houver serviços de destino, propaga a requisição
        if config.APP_URL_DESTINO:
            urls = config.APP_URL_DESTINO.split(',')
            
            logger.info(
                "Iniciando propagação para serviços downstream",
                extra={
                    **log_context,
                    "destination_urls": urls,
                    "destinations_count": len(urls),
                    "payload_to_send": original_payload
                }
            )
            
            for url in urls:

                with tracer.start_as_current_span("send-request") as child_span:

                    try:
                        # Log do início da requisição externa
                        logger.debug(
                            "Enviando requisição para serviço downstream",
                            extra={
                                **log_context,
                                "destination_url": url,
                                "request_method": "POST",
                                "request_path": "/process"
                            }
                        )

                        headers = {}
                        propagator.inject(headers)

                        child_span.set_attribute("net.peer.name", url)
                        child_span.set_attribute("destination.url", url)

                        child_span.add_event("Requisição externa bem-sucedida", {"url": url})

                        resp = requests.post(
                            f"{url}/process",
                            json=original_payload,
                            headers=headers,
                            timeout=5
                        )

                        child_span.set_attribute("http.status_code", resp.status_code)

                        if resp.status_code == 200:
                            original_payload = resp.json()
                            
                            # Log de sucesso na requisição externa
                            logger.info(
                                "Requisição externa bem-sucedida",
                                extra={
                                    **log_context,
                                    "destination_url": url,
                                    "response_status": resp.status_code,
                                    "payload_sent": original_payload
                                }
                            )
                        else:
                            response.status_code = status.HTTP_502_BAD_GATEWAY
                            
                            # Log de erro de status HTTP
                            logger.error(
                                "Erro de status na requisição externa",
                                extra={
                                    **log_context,
                                    "destination_url": url,
                                    "response_status": resp.status_code,
                                    "error_type": "bad_gateway"
                                }
                            )
                            
                            return {"error": f"Erro ao enviar para {url}: {resp.status_code}"}

                    except requests.RequestException as e:
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        
                        # Log estruturado do erro de requisição externa
                        logger.error(
                            "Falha na requisição externa",
                            extra={
                                **log_context,
                                "error_type": "request_exception",
                                "error_message": str(e),
                                "destination_url": url,
                                "payload": original_payload
                            },
                            exc_info=True
                        )
                        
                        main_span.record_exception(Exception(e))
                        main_span.set_status(Status(StatusCode.ERROR))
                        return {"error": f"Falha na requisição para {url}: {str(e)}"}

        main_span.set_status(Status(StatusCode.OK))
        
        # Log de sucesso no processamento completo
        elapsed_time = time.time() - start_time
        logger.info(
            "Processamento concluido com sucesso",
            extra={
                **log_context,
                "result_payload": original_payload,
                "processing_duration": elapsed_time,
                "latency_simulation": config.APP_LATENCY,
                "destinations_count": len(config.APP_URL_DESTINO.split(',')) if config.APP_URL_DESTINO else 0
            }
        )

    response_time_histogram.record(elapsed_time, {"app": config.APP_NAME, "endpoint": "/process"})

    return original_payload