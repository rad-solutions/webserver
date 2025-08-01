FROM python:3.12-slim


WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev curl bash \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Instalar Poetry
ENV POETRY_HOME="/opt/poetry"
ENV PATH="$POETRY_HOME/bin:$PATH"
RUN curl -sSL https://install.python-poetry.org | python3 - --version 1.8.2 \
    && poetry config virtualenvs.create false

# Copiar archivos de dependencias y del proyecto
COPY pyproject.toml poetry.lock* ./

# Instalar dependencias de Python con Poetry
# --no-root es para no instalar el paquete actual (el proyecto en sí) como editable,
# lo cual es bueno para producción.
# --only main es para no instalar dependencias de desarrollo en la imagen final.
RUN poetry install --no-root --only main

# Copiar el proyecto
COPY . .

# Crear directorios necesarios
RUN mkdir -p /app/media /app/staticfiles

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--timeout", "120", "app_server.wsgi:application"]
