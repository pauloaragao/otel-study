# =============================================================================
# MÓDULO DE TRACING - OPENTELEMETRY
# =============================================================================
# Este módulo demonstra como implementar tracing usando OpenTelemetry
# Tracing (Rastreamento) permite acompanhar o fluxo de uma requisição através
# de diferentes serviços, identificando onde ocorrem gargalos e erros

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from config import APP_NAME, OTLP_ENDPOINT
from opentelemetry.semconv.attributes.service_attributes import (
    SERVICE_NAME,
    SERVICE_VERSION
)
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

class TracingOTEL:
    """
    Classe para configuração e uso de tracing com OpenTelemetry.
    Permite criar spans, propagar contexto e exportar traces para OTLP.
    """

    def __init__(self, app_name=None, service_version="1.0.0"):
        # =============================================================================
        # CONFIGURAÇÃO DO ENDPOINT OTLP
        # =============================================================================
        # OTLP (OpenTelemetry Protocol): Protocolo padrão para enviar telemetria
        # Este endpoint receberá os traces e os enviará para o sistema de observabilidade
        self.app_name = app_name or APP_NAME
        self.service_version = service_version
        self.trace_otlp_endpoint = f"{OTLP_ENDPOINT}/v1/traces"

        # =============================================================================
        # RECURSO (RESOURCE) - METADADOS DO SERVIÇO
        # =============================================================================
        # Resource: Define informações sobre o serviço que está gerando os traces
        # Essas informações ajudam a identificar de qual serviço/versão vêm os dados
        self.resource = Resource.create({
            SERVICE_NAME: self.app_name,
            SERVICE_VERSION: self.service_version
        })

        # =============================================================================
        # TRACER PROVIDER - CONFIGURAÇÃO CENTRAL DO TRACING
        # =============================================================================
        # TracerProvider: É o ponto central de configuração para tracing
        # Define como os traces serão processados e exportados
        self.provider = TracerProvider(resource=self.resource)

        # =============================================================================
        # PROCESSADORES DE SPANS (SPAN PROCESSORS)
        # =============================================================================
        # Span Processor: Define como os spans (segmentos de trace) serão processados
        # BatchSpanProcessor: Agrupa spans em lotes para envio eficiente

        # Processador para console - útil para desenvolvimento/debug
        # Envia os traces para o console (terminal) para visualização local
        # self.processor_console = BatchSpanProcessor(ConsoleSpanExporter())
        # self.provider.add_span_processor(self.processor_console)

        # Processador para OTLP - envia traces para sistema de observabilidade
        # Este é o processador usado em produção
        self.processor_otlp = BatchSpanProcessor(
            OTLPSpanExporter(endpoint=self.trace_otlp_endpoint)
        )
        self.provider.add_span_processor(self.processor_otlp)

        # =============================================================================
        # CONFIGURAÇÃO GLOBAL DO TRACING
        # =============================================================================
        # Define o provider como global para toda a aplicação
        trace.set_tracer_provider(self.provider)

        # =============================================================================
        # TRACER - INSTRUMENTO PRINCIPAL PARA CRIAR SPANS
        # =============================================================================
        # Tracer: É o instrumento principal para criar spans (segmentos de trace)
        # Cada serviço deve ter seu próprio tracer identificado pelo nome
        self.tracer = trace.get_tracer(self.app_name)

        # =============================================================================
        # PROPAGADOR DE CONTEXTO
        # =============================================================================
        # TraceContextTextMapPropagator: Responsável por propagar o contexto de trace
        # entre diferentes serviços através de headers HTTP ou outros meios
        # Permite que uma requisição mantenha seu contexto de trace ao atravessar
        # múltiplos serviços (ex: API Gateway -> Serviço A -> Serviço B)
        self.propagator = TraceContextTextMapPropagator()

    def get_tracer(self):
        """
        Retorna o tracer configurado para criar spans.
        """
        return self.tracer

    def get_propagator(self):
        """
        Retorna o propagador de contexto para uso em headers HTTP.
        """
        return self.propagator

# Exemplo de uso:
# tracing = TracingOTEL()
# tracer = tracing.get_tracer()