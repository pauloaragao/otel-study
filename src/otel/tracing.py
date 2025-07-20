# =============================================================================
# MÓDULO DE TRACING - OPENTELEMETRY
# =============================================================================
# Este módulo demonstra como implementar tracing usando OpenTelemetry
# Tracing (Rastreamento) permite acompanhar o fluxo de uma requisição através
# de diferentes serviços, identificando onde ocorrem gargalos e erros

# Importações necessárias para trabalhar com tracing OpenTelemetry
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

# =============================================================================
# CONFIGURAÇÃO DO ENDPOINT OTLP
# =============================================================================
# OTLP (OpenTelemetry Protocol): Protocolo padrão para enviar telemetria
# Este endpoint receberá os traces e os enviará para o sistema de observabilidade
TRACE_OTLP_ENDPOINT = f"{OTLP_ENDPOINT}/v1/traces"

# =============================================================================
# RECURSO (RESOURCE) - METADADOS DO SERVIÇO
# =============================================================================
# Resource: Define informações sobre o serviço que está gerando os traces
# Essas informações ajudam a identificar de qual serviço/versão vêm os dados
resource = Resource.create({
    SERVICE_NAME: APP_NAME,        # Nome do serviço
    SERVICE_VERSION: "1.0.0"       # Versão do serviço
})

# =============================================================================
# TRACER PROVIDER - CONFIGURAÇÃO CENTRAL DO TRACING
# =============================================================================
# TracerProvider: É o ponto central de configuração para tracing
# Define como os traces serão processados e exportados
provider = TracerProvider(resource=resource)

# =============================================================================
# PROCESSADORES DE SPANS (SPAN PROCESSORS)
# =============================================================================
# Span Processor: Define como os spans (segmentos de trace) serão processados
# BatchSpanProcessor: Agrupa spans em lotes para envio eficiente

# Processador para console - útil para desenvolvimento/debug
# Envia os traces para o console (terminal) para visualização local
processor_console = BatchSpanProcessor(ConsoleSpanExporter())

# Processador para OTLP - envia traces para sistema de observabilidade
# Este é o processador usado em produção
processor_otlp = BatchSpanProcessor(OTLPSpanExporter(endpoint=TRACE_OTLP_ENDPOINT))

# =============================================================================
# CONFIGURAÇÃO DOS PROCESSADORES
# =============================================================================
# Comentado o processador de console para não poluir o terminal
# provider.add_span_processor(processor_console)

# Adiciona o processador OTLP que enviará os traces para o sistema de observabilidade
provider.add_span_processor(processor_otlp)

# =============================================================================
# CONFIGURAÇÃO GLOBAL DO TRACING
# =============================================================================
# Define o provider como global para toda a aplicação
trace.set_tracer_provider(provider)

# =============================================================================
# TRACER - INSTRUMENTO PRINCIPAL PARA CRIAR SPANS
# =============================================================================
# Tracer: É o instrumento principal para criar spans (segmentos de trace)
# Cada serviço deve ter seu próprio tracer identificado pelo nome
tracer = trace.get_tracer(APP_NAME)

# =============================================================================
# PROPAGADOR DE CONTEXTO
# =============================================================================
# TraceContextTextMapPropagator: Responsável por propagar o contexto de trace
# entre diferentes serviços através de headers HTTP ou outros meios
# Permite que uma requisição mantenha seu contexto de trace ao atravessar
# múltiplos serviços (ex: API Gateway -> Serviço A -> Serviço B)
propagator = TraceContextTextMapPropagator()