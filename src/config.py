import os
from dotenv import load_dotenv

# ================================
#  CONFIGURAÇÃO DA APLICAÇÃO
# ================================

load_dotenv()

APP_NAME = os.getenv("APP_NAME", "app-observability-otel")
APP_URL_DESTINO = os.getenv("APP_URL_DESTINO", "")

# Simulação de problemas
APP_ERRORS = int(os.getenv("APP_ERRORS", "0"))  # Porcentagem de erro (0 a 100)
APP_LATENCY = int(os.getenv("APP_LATENCY", "0"))  # Tempo máximo de atraso (em ms)

OTLP_ENDPOINT = os.getenv("OTLP_ENDPOINT", "") 