# =============================================================================
# MÓDULO DE MÉTRICAS - OPENTELEMETRY
# =============================================================================
# Este módulo demonstra como implementar métricas usando OpenTelemetry
# Métricas são valores numéricos que representam o comportamento de um sistema
# em um ponto específico no tempo (ex: número de requisições, uso de CPU, etc.)

# Importações necessárias para trabalhar com métricas OpenTelemetry
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.prometheus import PrometheusMetricReader
import random
from typing import Iterable
from opentelemetry.metrics import CallbackOptions, Observation
import psutil
import os
import config

from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter


# Nome da aplicação - usado para identificar de qual serviço vêm as métricas
APP_NAME = os.getenv("APP_NAME", "app-a")

# =============================================================================
# CONFIGURAÇÃO DO SISTEMA DE MÉTRICAS
# =============================================================================
# PrometheusMetricReader: Responsável por expor as métricas no formato que o Prometheus entende
# O Prometheus é uma ferramenta de monitoramento que coleta e armazena métricas
prometheus_reader = PrometheusMetricReader()

otlp_exporter = OTLPMetricExporter(
    endpoint=f"{config.OTLP_ENDPOINT}/v1/metrics"
)

otlp_reader = PeriodicExportingMetricReader(
    exporter=otlp_exporter,
    export_interval_millis=1000 # Exporta a cada 1 segundo
)

# MeterProvider: É o ponto central de configuração para métricas
# Define como as métricas serão coletadas e exportadas
metrics.set_meter_provider(
    MeterProvider(
        metric_readers=[prometheus_reader, otlp_reader]  # Lista de leitores que coletam as métricas
    )
)

# Meter: É o instrumento principal para criar métricas
# Funciona como uma "fábrica" de métricas para uma aplicação específica
meter = metrics.get_meter(APP_NAME)

# =============================================================================
# COUNTER (CONTADOR) - MÉTRICA CUMULATIVA
# =============================================================================
# Counter: Só aumenta, nunca diminui (ex: número total de requisições)
# Ideal para contar eventos que acontecem ao longo do tempo
requests_counter = meter.create_counter(
    name="app_requests_total",           # Nome da métrica (padrão: nome_total)
    description="Número de requisições processadas",  # Descrição humana
    unit="1",                            # Unidade de medida (1 = contagem)
)

# =============================================================================
# OBSERVABLE COUNTER (CONTADOR OBSERVÁVEL) - MÉTRICA COM CALLBACK
# =============================================================================
# Observable Counter: Valor calculado dinamicamente através de uma função callback
# Útil quando você não pode incrementar manualmente, mas pode calcular o valor atual

def get_random_value(options: CallbackOptions) -> Iterable[Observation]:
    """
    Callback function que gera um valor aleatório
    Esta função é chamada automaticamente pelo OpenTelemetry para coletar a métrica
    """
    random_value = random.randint(1, 100)
    # Observation: Representa uma observação da métrica com valor e atributos
    yield Observation(
        random_value,                    # Valor da métrica
        {"service": APP_NAME}           # Atributos (labels) para categorização
    )

# Criação do observable counter com a função callback
random_counter = meter.create_observable_counter(
    name="app_random_value",
    description="Contador de valores aleatórios",
    callbacks=[get_random_value],       # Lista de funções que calculam o valor
)

# =============================================================================
# GAUGE (MEDIDOR) - MÉTRICA DE VALOR ATUAL
# =============================================================================
# Gauge: Representa um valor atual que pode subir ou descer
# Ex: temperatura, uso de memória, número de conexões ativas
active_requests_gauge = meter.create_gauge(
    name="app_active_requests",
    description="Número de requisições ativas",
    unit="1",
)

# =============================================================================
# OBSERVABLE GAUGE (MEDIDOR OBSERVÁVEL) - GAUGE COM CALLBACK
# =============================================================================
# Observable Gauge: Valor atual calculado dinamicamente
# Perfeito para métricas do sistema que mudam constantemente

# Obtém referência ao processo atual para monitorar recursos
process = psutil.Process()

def get_memory_usage(options: CallbackOptions) -> Iterable[Observation]:
    """
    Callback function que monitora o uso de memória do processo
    Demonstra como coletar métricas do sistema operacional
    """
    memory_usage = process.memory_percent()  # Uso de memória em porcentagem
    yield Observation(
        memory_usage,                    # Valor da métrica (porcentagem)
        {"service": APP_NAME}           # Atributos para identificação
    )

# Criação do observable gauge para monitoramento de memória
memory_gauge = meter.create_observable_gauge(
    name="app_memory_usage",
    description="Uso de memória do processo",
    callbacks=[get_memory_usage]        # Função que calcula o uso de memória
)

# =============================================================================
# HISTOGRAM (HISTOGRAMA) - MÉTRICA DE DISTRIBUIÇÃO
# =============================================================================
# Histogram: Agrupa observações em buckets (caixas) baseado em valores
# Ideal para medir latência, tamanho de requisições, etc.
# Permite analisar percentis (ex: 95% das requisições respondem em menos de X segundos)
response_time_histogram = meter.create_histogram(
    name="app_response_time_seconds",
    description="Tempo de resposta das requisições em segundos",
    unit="s",                           # Unidade: segundos
    explicit_bucket_boundaries_advisory=[  # Limites dos buckets em segundos
        0.005,  # 5ms
        0.01,   # 10ms
        0.025,  # 25ms
        0.05,   # 50ms
        0.1,    # 100ms
        0.25,   # 250ms
        0.5     # 500ms
    ]
)
