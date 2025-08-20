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

class OTelLogger:
    def __init__(self, service_name=None, service_version="1.0.0"):
        self.service_name = service_name or config.APP_NAME
        self.service_version = service_version

        # Cria recurso OTEL
        resource = Resource.create({
            SERVICE_NAME: self.service_name,
            SERVICE_VERSION: self.service_version
        })

        # Provedor de logs OTEL
        self.logger_provider = LoggerProvider(resource=resource)

        # Exportador para console
        console_exporter = ConsoleLogExporter()
        self.logger_provider.add_log_record_processor(
            SimpleLogRecordProcessor(console_exporter)
        )

        # Exportador para OTLP
        otlp_exporter = OTLPLogExporter(
            endpoint=f"{config.OTLP_ENDPOINT}/v1/logs"
        )
        self.logger_provider.add_log_record_processor(
            SimpleLogRecordProcessor(otlp_exporter)
        )

        # Define o provedor global
        set_logger_provider(self.logger_provider)

        # Handler OTEL para logging padrão Python
        self.otel_handler = LoggingHandler(logger_provider=self.logger_provider)
        self.otel_handler.setLevel(logging.INFO)

        # Configura logging básico
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(process)d - %(levelname)s - %(message)s",
        )

        # Logger da aplicação
        self.logger = logging.getLogger(self.service_name)
        self.logger.addHandler(self.otel_handler)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

    def info(self, msg, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)