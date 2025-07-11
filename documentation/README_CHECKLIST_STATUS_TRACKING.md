# Seguimiento de Estado de Ítems de Checklist

Este documento detalla la implementación del sistema de seguimiento de estado para los ítems individuales de un checklist de proceso. Esta funcionalidad permite un control más granular sobre el progreso de cada tarea dentro de un proceso.

## 1. Modelo de Datos

Se han introducido y modificado los siguientes modelos para soportar esta funcionalidad:

### `ChecklistItemStatusChoices`

Se ha añadido una nueva clase `TextChoices` en `app/models.py` para definir los posibles estados de un ítem de checklist:

-   **Pendiente**: El estado inicial por defecto.
-   **En Progreso**: La tarea ha sido iniciada.
-   **En Revisión**: La tarea está completada y pendiente de aprobación.
-   **Aprobado**: La tarea ha sido revisada y aprobada. Este estado marca el ítem como "completado".
-   **Rechazado**: La tarea ha sido revisada pero no cumple los criterios.

### `ProcessChecklistItem`

Este modelo ha sido modificado para incluir un seguimiento de estado detallado:

-   **`status`**: Un `CharField` que utiliza `ChecklistItemStatusChoices` para almacenar el estado actual del ítem. Su valor por defecto es `Pendiente`.
-   **`is_completed`**: Este campo booleano se mantiene por compatibilidad, pero su valor ahora se deriva automáticamente del campo `status`. Será `True` si el `status` es `Aprobado`, y `False` en caso contrario.

#### Lógica de Guardado (`save` method)

El método `save` de `ProcessChecklistItem` ha sido sobrescrito para:
1.  Detectar si el campo `status` ha cambiado.
2.  Actualizar automáticamente el campo `is_completed` basándose en si el nuevo `status` es `Aprobado`.
3.  Crear una entrada en `ChecklistItemStatusLog` cada vez que el estado cambia, registrando el estado anterior, el nuevo estado y el usuario que realizó la modificación.

### `ChecklistItemStatusLog`

Un nuevo modelo para registrar el historial de cambios de estado de cada ítem del checklist. Almacena:

-   Una referencia al `ProcessChecklistItem` (`item`).
-   El estado anterior (`estado_anterior`).
-   El nuevo estado (`estado_nuevo`).
-   La fecha del cambio (`fecha_cambio`).
-   El usuario que modificó el estado (`usuario_modifico`).

## 2. Lógica de Negocio

### Cálculo del Progreso del Proceso

El método `get_progress_percentage` en el modelo `Process` ha sido actualizado. Ahora, el porcentaje de progreso se calcula sumando los porcentajes de los `ProcessChecklistItem` cuyo `status` es **`Aprobado`**.

### Reseteo de Checklist

El método `_reset_checklist_items` en el modelo `Process` (utilizado cuando un proceso entra en estado de "En Modificación") ahora resetea el `status` de todos los ítems a **`Pendiente`**.

## 3. Implementación de Pruebas

Se ha creado un nuevo archivo de pruebas `app/tests/test_checklist_status.py` para validar la nueva funcionalidad. Las pruebas cubren:

-   El estado inicial de un nuevo ítem de checklist.
-   La creación de un `ChecklistItemStatusLog` cuando el estado de un ítem cambia.
-   La actualización correcta del campo `is_completed` cuando el `status` cambia a `Aprobado`.
-   El cálculo correcto del porcentaje de progreso del proceso.
-   El reseteo del estado de los ítems del checklist.

## 4. Pasos Futuros

-   **Actualizar Vistas y Formularios**: Las interfaces de usuario que interactúan con los ítems del checklist deben ser actualizadas para permitir a los usuarios modificar el nuevo campo `status` en lugar del booleano `is_completed`.
-   **Refactorizar `is_completed`**: Una vez que toda la lógica de la aplicación dependa del campo `status`, el campo `is_completed` podría ser eliminado para simplificar el modelo `ProcessChecklistItem`. Esto requeriría una nueva migración de base de datos.
