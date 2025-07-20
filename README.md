# Aplicação para Exemplo de Telemetria

Este projeto consiste em uma aplicação FastAPI simples projetada para demonstrar a instrumentação com OpenTelemetry em um sistema distribuído. A aplicação simula um ambiente de microsserviços com múltiplos componentes que se comunicam entre si.

## Sobre o Projeto

O projeto inclui:

- Uma API básica construída com FastAPI
- Simulação de latência variável e erros
- Encadeamento de chamadas entre múltiplos serviços
- Configuração completa de Docker e Docker Compose para execução fácil
- Implementação completa dos três pilares da observabilidade:
  - Traces distribuídos com OpenTelemetry e Jaeger
  - Métricas com Prometheus
  - Logs estruturados com Loki
- Visualização unificada através do Grafana

## Estrutura do Projeto

```
.
├── src/
│   ├── app.py                # Aplicação principal FastAPI
│   ├── config.py             # Configurações da aplicação
│   ├── requirements.txt      # Dependências Python
│   ├── Dockerfile           # Instruções para build da imagem Docker
│   └── otel/                # Módulos de telemetria
│       ├── tracing.py       # Configuração de traces
│       ├── metrics.py       # Configuração de métricas
│       └── logs.py          # Configuração de logs
├── k8s/                     # Configurações do Kubernetes
├── .docker/                 # Arquivos de configuração Docker
├── compose.yaml             # Configuração de múltiplos serviços
└── teste_request.http       # Exemplos de requisições HTTP
```

## Pré-requisitos

- Docker
- Docker Compose
- Python 3.8+ (para desenvolvimento local)
- Kubernetes (opcional, para deploy em cluster)

## Como Executar

1. Clone o repositório:

```bash
git clone <url-do-repositorio>
cd <diretorio-do-projeto>
```

2. Inicie o serviço com Docker Compose:

```bash
docker-compose up --build
```

Isso iniciará uma instância da aplicação:
- `app-a` - acessível em http://localhost:8000

## Testando a Aplicação

### Verificar o status do serviço:

```bash
curl http://localhost:8000/
```

Você deverá receber uma resposta como:
```json
{"message": "Esse é o serviço app-a"}
```

### Enviar uma requisição de processamento:

```bash
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '["dado-inicial"]'
```

## Configuração

O arquivo `compose.yaml` está configurado inicialmente para executar apenas o serviço `app-a`. Você pode descomentar as seções dos serviços `app-b` e `app-c`, bem como as variáveis de ambiente adicionais, para criar um ambiente distribuído mais complexo.

```yaml
version: '3.8'

services:
  app-a:
    build: .
    ports:
      - "8000:8000"
    environment:
      - APP_NAME=app-a
      # - APP_URL_DESTINO=http://app-b:8000
      # - APP_ERRORS=5
      # - APP_LATENCY=100
    networks:
      - app-network

  # app-b:
  #   build: .
  #   ports:
  #     - "8001:8000"
  #   environment:
  #     - APP_NAME=app-b
  #     - APP_URL_DESTINO=http://app-c:8000
  #     - APP_ERRORS=10
  #     - APP_LATENCY=150
  #   networks:
  #     - app-network

  # app-c:
  #   build: .
  #   ports:
  #     - "8002:8000"
  #   environment:
  #     - APP_NAME=app-c
  #     - APP_ERRORS=15
  #     - APP_LATENCY=200
  #   networks:
  #     - app-network

networks:
  app-network:
```

### Variáveis de Ambiente

Você pode personalizar o comportamento dos serviços modificando as variáveis de ambiente:

- `APP_NAME`: Nome do serviço
- `APP_URL_DESTINO`: URL para qual o serviço deve propagar a requisição
- `APP_ERRORS`: Porcentagem de requisições que resultarão em erro (0-100)
- `APP_LATENCY`: Latência máxima em milissegundos (atraso aleatório entre 0 e esse valor)

## Endpoints Disponíveis

### Serviço Principal (app-a)

- `GET /`: Health check do serviço
- `GET /metrics`: Endpoint para métricas Prometheus
- `POST /process`: Processa payloads e propaga para outros serviços

### Observabilidade

- Jaeger UI: http://localhost:16686
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090
- Loki: http://localhost:3100

## Arquitetura do Projeto
```mermaid
flowchart TD
    %% Definição dos Serviços de Aplicação
    subgraph Microsserviços
        app-a["app-a"]
        app-b["app-b"]
        app-c["app-c"]
    end

    %% Fluxo de requisições entre serviços
    app-a -->|HTTP Request| app-b
    app-b -->|HTTP Request| app-c

    %% Subgráfico para Observabilidade
    subgraph "Observabilidade"
        subgraph "Coleta de Telemetria"
            collector["OpenTelemetry Collector (Porta HTTP: 4318)"]
        end

        subgraph "Armazenamento e Análise"
            jaeger["Jaeger (Traces)"]
            prometheus["Prometheus (Métricas)"]
            loki["Loki (Logs)"]
        end

        subgraph "Visualização"
            grafana["Grafana (Dashboards)"]
        end
    end

    %% Fluxo de Telemetria
    app-a -->|Telemetria via OTLP HTTP| collector
    app-b -->|Telemetria via OTLP HTTP| collector
    app-c -->|Telemetria via OTLP HTTP| collector

    %% Fluxo do Collector para os backends
    collector -->|Traces| jaeger
    collector -->|Métricas| prometheus
    collector -->|Logs| loki

    %% Fluxo para visualização
    jaeger -->|Fonte de Dados| grafana
    prometheus -->|Fonte de Dados| grafana
    loki -->|Fonte de Dados| grafana

    %% Estilo dos nós com fonte preta
    classDef microservice fill:#d9f7be,stroke:#389e0d,stroke-width:2px,color:#000;
    classDef collector fill:#bae7ff,stroke:#1890ff,stroke-width:2px,color:#000;
    classDef storage fill:#d3adf7,stroke:#722ed1,stroke-width:2px,color:#000;
    classDef visualization fill:#ffe58f,stroke:#faad14,stroke-width:2px,color:#000;

    class app-a,app-b,app-c microservice
    class collector collector
    class jaeger,prometheus,loki storage
    class grafana visualization
```

## Fluxo dos Dados de Telemetria 
```mermaid
flowchart LR
    %% Entrada de dados
    otlp-http["OTLP HTTP Receiver - Porta 4318"]
    otlp-grpc["OTLP gRPC Receiver - Porta 4317"]
    
    %% Processadores
    mem["Memory Limiter"]
    batch["Batch Processor"]
    
    %% Exportadores
    jaeger-exp["Jaeger Exporter"]
    prom-exp["Prometheus Exporter"]
    loki-exp["Loki Exporter"]
    log-exp["Console Logger (Debug)"]
    
    %% Destinos
    jaeger-dest["Jaeger - Porta 14250"]
    prom-dest["Prometheus - Porta 8889"]
    loki-dest["Loki - Porta 3100"]
    
    %% Fluxo de dados para traces
    otlp-http --> mem
    otlp-grpc --> mem
    mem --> batch
    batch --> jaeger-exp
    batch --> log-exp
    jaeger-exp --> jaeger-dest
    
    %% Fluxo de dados para métricas
    batch --> prom-exp
    prom-exp --> prom-dest
    
    %% Fluxo de dados para logs
    batch --> loki-exp
    loki-exp --> loki-dest
    
    %% Estilo dos nós com fonte preta
    classDef receiver fill:#d9f7be,stroke:#389e0d,stroke-width:1px,color:#000;
    classDef processor fill:#bae7ff,stroke:#1890ff,stroke-width:1px,color:#000;
    classDef exporter fill:#d3adf7,stroke:#722ed1,stroke-width:1px,color:#000;
    classDef destination fill:#ffe58f,stroke:#faad14,stroke-width:1px,color:#000;
    
    class otlp-http,otlp-grpc receiver
    class mem,batch processor
    class jaeger-exp,prom-exp,loki-exp,log-exp exporter
    class jaeger-dest,prom-dest,loki-dest destination
```

## Implementação de Telemetria

### Traces
- Implementação usando OpenTelemetry
- Propagação de contexto entre serviços
- Atributos personalizados para cada span
- Integração com Jaeger para visualização

### Métricas
- Contadores de requisições
- Medidores de requisições ativas
- Histogramas de tempo de resposta
- Exportação para Prometheus

### Logs
- Logs estruturados com contexto
- Correlação com traces
- Níveis de log configuráveis
- Integração com Loki

