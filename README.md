# RadSolutions Reports

Sistema de informes para soluciones radiológicas.

## Descripción

RadSolutions Reports es una aplicación web basada en Django para la gestión de informes radiológicos en entornos médicos. Permite crear, almacenar y gestionar informes de estudios de imagen.

## Requisitos

- Python 3.12+
- Docker y Docker Compose
- PostgreSQL

## Configuración del entorno

1. Clona este repositorio:
   ```
   git clone <url-del-repositorio>
   cd radsolutions_reports
   ```

2. Crea un archivo `.env` en la raíz del proyecto con las siguientes variables (o edita el existente):
   ```
   DEBUG=True
   DJANGO_SECRET_KEY=<tu-clave-secreta>
   DATABASE_NAME=radsolutions_db
   DATABASE_USER=radsolutions_user
   DATABASE_PASSWORD=radsolutions_pass
   DATABASE_HOST=db
   DATABASE_PORT=5433
   ALLOWED_HOSTS=localhost,127.0.0.1
   USE_MOCK_STORAGE=True
   ```

## Instalación y ejecución

### Con Docker (recomendado)

1. Construye y levanta los contenedores:
   ```
   make setup
   ```

2. Para detener los servicios:
   ```
   make down
   ```

### Sin Docker (desarrollo local)

1. Crea un entorno virtual y actívalo:
   ```
   python -m venv env
   source env/bin/activate  # En Windows: env\Scripts\activate
   ```

2. Instala las dependencias:
   ```
   pip install -r requirements.txt
   ```

3. Aplica las migraciones:
   ```
   make migrate
   ```

4. Inicia el servidor de desarrollo:
   ```
   make run
   ```

## Comandos útiles (Makefile)

- `make help` - Muestra los comandos disponibles
- `make run` - Inicia el servidor de desarrollo
- `make migrate` - Aplica migraciones pendientes
- `make makemigrations` - Crea nuevas migraciones
- `make test` - Ejecuta los tests
- `make lint` - Verifica el estilo del código
- `make format` - Formatea el código automáticamente

## Estructura del proyecto

```
radsolutions_reports/
├── app/                 # Aplicación principal
├── app_server/          # Configuración del proyecto Django
├── env/                 # Entorno virtual (ignorado en git)
├── .env                 # Variables de entorno
├── .gitignore           # Archivos ignorados por git
├── docker-compose.yml   # Configuración de Docker Compose
├── Dockerfile           # Configuración de Docker
├── makefile             # Comandos útiles
├── manage.py            # Script de administración de Django
├── README.md            # Este archivo
└── requirements.txt     # Dependencias del proyecto
```

## Contribuir

1. Crea un fork del proyecto
2. Crea una rama para tu funcionalidad (`git checkout -b feature/nueva-funcionalidad`)
3. Realiza los cambios y haz commit (`git commit -am 'Agrega nueva funcionalidad'`)
4. Envía los cambios a tu fork (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request
