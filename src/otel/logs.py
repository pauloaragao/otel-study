# Importação das bibliotecas necessárias
import logging
import config
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import ConsoleLogExporter, SimpleLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.attributes.service_attributes import (
    SERVICE_NAME,
    SERVICE_VERSION
)
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter

# Define o nome da aplicação usando variável de ambiente ou valor padrão


# Cria um recurso OpenTelemetry com informações do serviço
# Isso ajuda a identificar a origem dos logs
resource = Resource.create({
    SERVICE_NAME: config.APP_NAME,  # Nome do serviço
    SERVICE_VERSION: "1.0.0"  # Versão do serviço
})

# Inicializa o provedor de logs do OpenTelemetry
# Este é o componente principal que gerencia os logs
logger_provider = LoggerProvider(resource=resource)

# Configura o exportador de logs para console
# Isso permite que os logs sejam exibidos no terminal
console_exporter = ConsoleLogExporter()
logger_provider.add_log_record_processor(
    SimpleLogRecordProcessor(console_exporter)
)

# Configura o exportador de logs para OTLP
otlp_exporter = OTLPLogExporter(
    endpoint=f"{config.OTLP_ENDPOINT}/v1/logs" 
)
logger_provider.add_log_record_processor(
    SimpleLogRecordProcessor(otlp_exporter)
)

# Define o provedor de logs como global
# Isso permite que outros componentes da aplicação usem o mesmo provedor
set_logger_provider(logger_provider)

# Cria um handler OpenTelemetry para processar os logs
# Este handler integra o logging padrão do Python com OpenTelemetry
otel_handler = LoggingHandler(logger_provider=logger_provider)
otel_handler.setLevel(logging.INFO)

# Configura o logging básico do Python para console
# Define o formato e nível dos logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(process)d - %(levelname)s - %(message)s",
)

# Cria um logger específico para a aplicação
# Este logger será usado para registrar eventos da aplicação
logger = logging.getLogger(config.APP_NAME)
logger.addHandler(otel_handler)
logger.setLevel(logging.INFO)

# Desativa a propagação dos logs para o root logger
# Isso evita logs duplicados
logger.propagate = False