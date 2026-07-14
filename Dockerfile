# Imagem da aplicação (produtor/consumidor de streaming e CLI do pipeline).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependências primeiro (melhor cache de camadas).
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Código-fonte e configurações.
COPY src ./src
COPY config ./config
COPY sql ./sql

# Usuário sem privilégios.
RUN useradd --create-home appuser
USER appuser

ENTRYPOINT ["python", "-m", "src.cli"]
CMD ["--help"]
