import os
from dotenv import load_dotenv

# ================================
#  CONFIGURAÇÃO DA APLICAÇÃO
# ================================

load_dotenv()

APP_NAME = os.getenv("APP_NAME", "app-observability-otel")
APP_URL_DESTINO = os.getenv("APP_URL_DESTINO", "")
OTLP_ENDPOINT = os.getenv("OTLP_ENDPOINT", "") 