# Pre-commit Hooks

Este proyecto utiliza pre-commit para verificar el código antes de cada commit.

## Configuración

Para configurar pre-commit, sigue estos pasos:

1. Instala pre-commit:
```bash
pip install pre-commit
pre-commit install
```

2. La configuración de pre-commit se encuentra en el archivo `.pre-commit-config.yaml`.

## Hooks configurados

- **pre-commit-hooks**: Verificaciones básicas como trailing-whitespace, end-of-file-fixer, check-yaml.
- **black**: Formateador de código Python.
- **isort**: Ordena las importaciones automáticamente.
- **flake8**: Linting para Python.
- **mypy**: Verificación de tipos estática (opcional).

## Uso

Una vez instalado, pre-commit se ejecutará automáticamente cada vez que intentes hacer un commit.

Para ejecutar los hooks manualmente en todos los archivos:
```bash
make precommit
```
o manualmente:
```bash
pre-commit run --all-files
```

## Resolver problemas

Si pre-commit detecta problemas, corregirá algunos automáticamente y para otros mostrará mensajes de error. Después de que se apliquen las correcciones automáticas, necesitarás añadir los cambios con `git add` y volver a intentar el commit.

Para omitir los hooks de pre-commit en un caso excepcional (no recomendado):
```bash
git commit -m "Tu mensaje" --no-verify
```
