# Documentación del Flujo de CI/CD con ECR

Este documento explica la configuración del pipeline de Integración Continua (CI) y Despliegue Continuo (CD) que integra Docker, Amazon ECR y GitHub Actions.

## Flujo de Ejecución de los Workflows

El proceso está orquestado a través de tres workflows de GitHub Actions que se ejecutan en una secuencia específica:

1.  **`ci.yml` (Integración Continua):**
    *   **Disparador:** Se activa con cada `push` o `pull_request` a la rama `main`.
    *   **Proceso:**
        *   Configura el entorno de Python y Docker.
        *   Se autentica en Amazon ECR para poder descargar imágenes base si es necesario.
        *   Levanta los servicios usando `docker-compose.yml`.
        *   Ejecuta pruebas de linting (isort, black, flake8) y tests de Django.
    *   **Objetivo:** Asegurar que el código nuevo es correcto y no rompe la funcionalidad existente.

2.  **`release.yml` (Gestión de Versiones):**
    *   **Disparador:** Se activa automáticamente solo si el workflow `ci.yml` termina con éxito en la rama `main`.
    *   **Proceso:**
        *   Utiliza `semantic-release` para analizar los mensajes de los commits desde la última versión.
        *   Si encuentra commits relevantes (ej. `feat:`, `fix:`), determina la nueva versión semántica (ej. `v1.2.3`).
        *   Crea un nuevo release en GitHub con notas automáticas y empuja un tag de Git con el número de la nueva versión.
    *   **Objetivo:** Automatizar la creación de versiones y el versionado del proyecto.

3.  **`cd.yml` (Despliegue Continuo):**
    *   **Disparador:** Se activa **únicamente** cuando se empuja un nuevo tag que coincide con el patrón `v*` (creado por el workflow de `release.yml`).
    *   **Proceso:**
        *   Se autentica en Amazon ECR.
        *   Construye una nueva imagen de Docker de producción.
        *   Etiqueta la imagen con el número de versión del tag (ej. `webserver:v1.2.3`) y también con `latest`.
        *   Sube la imagen etiquetada al repositorio de Amazon ECR.
    *   **Objetivo:** Publicar un artefacto (imagen de Docker) versionado y listo para ser desplegado.

## Uso de `docker-compose.yml` con una Imagen de ECR

El archivo `docker-compose.yml` ha sido configurado para utilizar una imagen de Docker almacenada en un repositorio privado de Amazon ECR como base para el servicio `web`.

```yaml
services:
  web:
    image: 978368259161.dkr.ecr.us-east-1.amazonaws.com/webserver:latest
    # ... resto de la configuración
```

Esto significa que, en lugar de construir la imagen desde un `Dockerfile` local cada vez, el sistema descarga la imagen `latest` desde ECR. Esto es especialmente útil en el workflow de CI (`ci.yml`), ya que necesita autenticarse en AWS para poder realizar esta acción.
