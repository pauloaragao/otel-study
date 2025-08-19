from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader
import time

# Configuração do OTEL para tracing e métricas (exemplo simples)
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)
span_processor = BatchSpanProcessor(ConsoleSpanExporter())
trace.get_tracer_provider().add_span_processor(span_processor)

metrics.set_meter_provider(MeterProvider())
meter = metrics.get_meter(__name__)
metric_reader = PeriodicExportingMetricReader(ConsoleMetricExporter())
metrics.get_meter_provider().register_metric_reader(metric_reader)

# Função para extrair dados de um site e instrumentar com OTEL
def extrair_dados():
    with tracer.start_as_current_span("extrair_dados_selenium"):
        # Configuração do Selenium (usando Chrome headless)
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(options=chrome_options)

        try:
            url = "https://quotes.toscrape.com/"
            driver.get(url)
            time.sleep(2)  # Espera a página carregar

            # Coleta todas as citações da página
            quotes = driver.find_elements(By.CLASS_NAME, "quote")
            total_quotes = len(quotes)

            # Exemplo de métrica: número de citações extraídas
            quote_count = meter.create_counter(
                name="quotes_extracted",
                description="Número de citações extraídas da página",
                unit="1"
            )
            quote_count.add(total_quotes)

            # Exemplo de tracing: adicionando atributos ao span
            trace.get_current_span().set_attribute("quotes.count", total_quotes)

            # Printando as citações (apenas para exemplo)
            for quote in quotes:
                texto = quote.find_element(By.CLASS_NAME, "text").text
                autor = quote.find_element(By.CLASS_NAME, "author").text
                print(f"{texto} - {autor}")

        finally:
            driver.quit()

if __name__ == "__main__":
    extrair_dados()