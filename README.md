# RadSolutions Reports

Sistema de informes para soluciones radiológicas.

## Descripción

RadSolutions Reports es una aplicación web basada en Django para la gestión de informes radiológicos en entornos médicos. Permite crear, almacenar y gestionar informes de estudios de imagen.

## Requisitos

- Python 3.12+
- Poetry (para gestión de dependencias y entorno virtual)
- Docker y Docker Compose
- PostgreSQL

## Configuración del entorno

1. Clona este repositorio:
   ```
   git clone https://github.com/rad-solutions/webserver.git
   cd webserver
   ```

2. Asegúrate de tener Poetry instalado. Puedes encontrar las instrucciones de instalación en [https://python-poetry.org/docs/#installation](https://python-poetry.org/docs/#installation).

3. Crea un archivo `.env` en la raíz del proyecto con las siguientes variables (o edita el existente):
   ```
   DEBUG=True
   DJANGO_SECRET_KEY=<tu-clave-secreta>
   DATABASE_NAME=radsolutions_db
   DATABASE_USER=radsolutions_user
   DATABASE_PASSWORD=radsolutions_pass
   DATABASE_HOST=db
   DATABASE_PORT=5432
   ALLOWED_HOSTS=localhost,127.0.0.1
   USE_MOCK_STORAGE=True
   ```

## Instalación y ejecución

**Nota para usuarios de Windows:** Los comandos `make` de este proyecto están pensados para entornos tipo Unix. Si estás en Windows, necesitarás usar WSL (Windows Subsystem for Linux) o una herramienta similar que proporcione la utilidad `make` (como Git Bash o Cygwin) para ejecutar estos comandos. Alternativamente, puedes ejecutar los comandos equivalentes directamente (por ejemplo, `poetry run python manage.py runserver` en lugar de `make run`).

### Con Docker (recomendado)

1. Construye y levanta los contenedores:
   ```
   make setup
   ```

2. Para detener los servicios:
   ```
   make down
   ```

### Sin Docker (desarrollo local con Poetry)

1. Configura Poetry para crear el entorno virtual dentro del proyecto (opcional, pero recomendado para algunos editores):
   ```
   poetry config virtualenvs.in-project true
   ```

2. Instala las dependencias (esto también creará y activará el entorno virtual si no existe):
   ```
   poetry install
   ```
   Si solo necesitas las dependencias principales (sin las de desarrollo):
   ```
   poetry install --only main
   ```

3. Para activar el entorno virtual manualmente (si no lo activa tu editor o terminal automáticamente):
   ```
   poetry shell
   ```
   Alternativamente, puedes prefijar tus comandos con `poetry run` (ej. `poetry run python manage.py migrate`).

4. Aplica las migraciones:
   ```
   make migrate  # o poetry run python manage.py migrate
   ```

5. Inicia el servidor de desarrollo:
   ```
   make run  # o poetry run python manage.py runserver
   ```

## Comandos útiles (Makefile)

Todos los comandos de Python (como `pytest`, `manage.py`, `flake8`, `black`, `isort`) ahora se ejecutan dentro del entorno de Poetry usando `poetry run`.

- `make help` - Muestra los comandos disponibles
- `make run` - Inicia el servidor de desarrollo (`poetry run python manage.py runserver`)
- `make migrate` - Aplica migraciones pendientes (`poetry run python manage.py migrate`)
- `make makemigrations` - Crea nuevas migraciones (`poetry run python manage.py makemigrations`)
- `make test` - Ejecuta los tests (`poetry run pytest`)
- `make lint` - Verifica el estilo del código (`poetry run flake8 . && poetry run black --check . && poetry run isort --check-only .`)
- `make format` - Formatea el código automáticamente (`poetry run black . && poetry run isort .`)

## Estructura del proyecto

```
radsolutions_reports/
├── app/                 # Aplicación principal
├── app_server/          # Configuración del proyecto Django
├── .venv/               # Entorno virtual de Poetry (si virtualenvs.in-project=true, ignorado en git)
├── .env                 # Variables de entorno
├── .gitignore           # Archivos ignorados por git
├── docker-compose.yml   # Configuración de Docker Compose
├── Dockerfile           # Configuración de Docker
├── makefile             # Comandos útiles
├── manage.py            # Script de administración de Django
├── pyproject.toml       # Archivo de configuración del proyecto y dependencias (Poetry)
├── poetry.lock          # Archivo de bloqueo de dependencias (Poetry)
└── README.md            # Este archivo
```

## Contribuir

1. Crea un fork del proyecto
2. Crea una rama para tu funcionalidad (`git checkout -b feature/nueva-funcionalidad`)
3. Realiza los cambios y haz commit (`git commit -am 'Agrega nueva funcionalidad'`)
4. Envía los cambios a tu fork (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request
