# =============================================================================
# MÓDULO DE MÉTRICAS - OPENTELEMETRY
# =============================================================================
# Este módulo demonstra como implementar métricas usando OpenTelemetry
# Métricas são valores numéricos que representam o comportamento de um sistema
# em um ponto específico no tempo (ex: número de requisições, uso de CPU, etc.)

import random
from typing import Iterable
import os
import psutil
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.metrics import CallbackOptions, Observation
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
import config


class MetricsOTEL:
    def __init__(self, app_name=None):
        self.app_name = app_name or os.getenv("APP_NAME", "app-a")
        self.prometheus_reader = PrometheusMetricReader()
        self.otlp_exporter = OTLPMetricExporter(
            endpoint=f"{config.OTLP_ENDPOINT}/v1/metrics"
        )
        self.otlp_reader = PeriodicExportingMetricReader(
            exporter=self.otlp_exporter,
            export_interval_millis=1000
        )
        metrics.set_meter_provider(
            MeterProvider(
                metric_readers=[self.prometheus_reader, self.otlp_reader]
            )
        )
        self.meter = metrics.get_meter(self.app_name)
        self.process = psutil.Process()
        self._init_metrics()

    def _init_metrics(self):

        # =============================================================================
        # COUNTER (CONTADOR) - MÉTRICA CUMULATIVA
        # =============================================================================
        # Counter: Só aumenta, nunca diminui (ex: número total de requisições)
        # Ideal para contar eventos que acontecem ao longo do tempo
        self.requests_counter = self.meter.create_counter(
            name="app_requests_total",
            description="Número de requisições processadas",
            unit="1",
        )

        # Observable Counter
        # =============================================================================
        # OBSERVABLE COUNTER (CONTADOR OBSERVÁVEL) - MÉTRICA COM CALLBACK
        # =============================================================================
        # Observable Counter: Valor calculado dinamicamente através de uma função callback
        # Útil quando você não pode incrementar manualmente, mas pode calcular o valor atual
        def get_random_value(options: CallbackOptions) -> Iterable[Observation]:
            random_value = random.randint(1, 100)
            yield Observation(
                random_value,
                {"service": self.app_name}
            )
        self.random_counter = self.meter.create_observable_counter(
            name="app_random_value",
            description="Contador de valores aleatórios",
            callbacks=[get_random_value],
        )

        # Gauge
        # =============================================================================
        # GAUGE (MEDIDOR) - MÉTRICA DE VALOR ATUAL
        # =============================================================================
        # Gauge: Representa um valor atual que pode subir ou descer
        # Ex: temperatura, uso de memória, número de conexões ativas
        self.active_requests_gauge = self.meter.create_gauge(
            name="app_active_requests",
            description="Número de requisições ativas",
            unit="1",
        )

        # Observable Gauge
        # =============================================================================
        # OBSERVABLE GAUGE (MEDIDOR OBSERVÁVEL) - GAUGE COM CALLBACK
        # =============================================================================
        # Observable Gauge: Valor atual calculado dinamicamente
        # Perfeito para métricas do sistema que mudam constantemente
        def get_memory_usage(options: CallbackOptions) -> Iterable[Observation]:
            memory_usage = self.process.memory_percent()
            yield Observation(
                memory_usage,
                {"service": self.app_name}
            )
        self.memory_gauge = self.meter.create_observable_gauge(
            name="app_memory_usage",
            description="Uso de memória do processo",
            callbacks=[get_memory_usage]
        )

        # Histogram
        # =============================================================================
        # HISTOGRAM (HISTOGRAMA) - MÉTRICA DE DISTRIBUIÇÃO
        # =============================================================================
        # Histogram: Agrupa observações em buckets (caixas) baseado em valores
        # Ideal para medir latência, tamanho de requisições, etc.
        # Permite analisar percentis (ex: 95% das requisições respondem em menos de X segundos)
        self.response_time_histogram = self.meter.create_histogram(
            name="app_response_time_seconds",
            description="Tempo de resposta das requisições em segundos",
            unit="s",
            explicit_bucket_boundaries_advisory=[
                0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5
            ]
        )
