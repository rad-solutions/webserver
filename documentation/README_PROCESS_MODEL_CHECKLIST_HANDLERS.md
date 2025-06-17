# Process Model Enhancements: Checklist Management and Status Logging

This document outlines recent enhancements to the `Process` model in `app/models.py`, focusing on the implementation of a dynamic checklist system and detailed status logging.

## Overview

The `Process` model now incorporates a checklist feature that automatically generates and manages tasks based on the `process_type`. This allows for standardized workflows and progress tracking for different types of processes (e.g., "Cálculo de Blindajes", "Control de Calidad").

Key changes include:
- New models: `ChecklistItemDefinition` and `ProcessChecklistItem`.
- A new process status: `EN_MODIFICACION`.
- Modifications to the `Process.save()` method to handle checklist logic and status logging.
- Helper methods within the `Process` model for checklist management: `_create_checklist_items`, `_reset_checklist_items`, and `get_progress_percentage`.

## New Models

### `ChecklistItemDefinition`
- Stores the template for checklist items.
- Each definition is tied to a `process_type` and includes a `name`, `order`, and `percentage` (contribution to overall process completion).

### `ProcessChecklistItem`
- Represents an instance of a checklist item for a specific `Process`.
- Links a `Process` to a `ChecklistItemDefinition`.
- Tracks `is_completed` status and `completed_at` timestamp.

## `Process.save()` Method Enhancements

The `save()` method of the `Process` model has been significantly updated to orchestrate checklist management and status logging:

1.  **User Tracking**: It now accepts an optional `user_who_modified` argument to log which user triggered a status change.
2.  **Status Logging**:
    -   When a new `Process` is created, a `ProcessStatusLog` entry is made with `estado_anterior` as `None`.
    -   When an existing `Process`'s `estado` (status) changes, a `ProcessStatusLog` entry is created, recording the `estado_anterior`, `estado_nuevo`, and `usuario_modifico`.
3.  **Checklist Creation**:
    -   For a **new** `Process`, the `_create_checklist_items()` handler is called immediately after the initial save and status log creation.
    -   If an **existing** `Process` (which might not have had checklists previously, e.g., older records) has its status changed (and it's not changing to `EN_MODIFICACION`) and it doesn't already have checklist items, `_create_checklist_items()` is called to populate them.
4.  **Checklist Reset**:
    -   If the `Process` status (`estado`) is changed to `ProcessStatusChoices.EN_MODIFICACION`, the `_reset_checklist_items()` handler is called. This is designed to allow for corrections or revisions to a process, requiring its checklist to be re-evaluated.

```python
# Excerpt from Process.save() in app/models.py
# ...
# super().save(*args, **kwargs) # Save the process instance

# if is_new:
#     ProcessStatusLog.objects.create(
#         proceso=self,
#         estado_anterior=None,
#         estado_nuevo=self.estado,
#         usuario_modifico=user_who_modified,
#     )
#     self._create_checklist_items()
# elif old_estado != self.estado:  # Existing instance and 'estado' has changed
#     ProcessStatusLog.objects.create(
#         proceso=self,
#         estado_anterior=old_estado,
#         estado_nuevo=self.estado,
#         usuario_modifico=user_who_modified,
#     )
#     if self.estado == ProcessStatusChoices.EN_MODIFICACION.value:
#         self._reset_checklist_items()
#     # If checklist items don't exist (e.g. for older processes) and not entering modification, create them.
#     elif not self.checklist_items.exists():
#             self._create_checklist_items()
# ...
```

## Handler Functions in `Process` Model

### 1. `_create_checklist_items(self)`

-   **Purpose**: To populate the `ProcessChecklistItem` table for the current `Process` instance based on its `process_type`.
-   **Logic**:
    -   Checks if the process already has checklist items (`if not self.checklist_items.exists()`). This prevents duplicate creation.
    -   Retrieves all `ChecklistItemDefinition` objects matching the `process.process_type`.
    -   For each definition, it creates a new `ProcessChecklistItem` linked to the current process and the definition.
-   **Called From**:
    -   `Process.save()` when a new process is created.
    -   `Process.save()` when an existing process (without prior checklist items) has its status changed (and not to `EN_MODIFICACION`).

```python
# Excerpt from app/models.py
# def _create_checklist_items(self):
#     """Creates checklist items for this process based on its type if they don't already exist."""
#     if not self.checklist_items.exists():
#         definitions = ChecklistItemDefinition.objects.filter(process_type=self.process_type)
#         for definition in definitions:
#             ProcessChecklistItem.objects.create(process=self, definition=definition)
```

### 2. `_reset_checklist_items(self)`

-   **Purpose**: To mark all checklist items associated with the current `Process` as incomplete.
-   **Logic**:
    -   Updates all related `ProcessChecklistItem` instances, setting `is_completed` to `False` and `completed_at` to `None`.
-   **Called From**:
    -   `Process.save()` when the `process.estado` is changed to `EN_MODIFICACION`. This signifies that the process is undergoing changes that invalidate previous progress.

```python
# Excerpt from app/models.py
# def _reset_checklist_items(self):
#     """Resets all checklist items for this process to not completed."""
#     self.checklist_items.update(is_completed=False, completed_at=None)
```

### 3. `get_progress_percentage(self)`

-   **Purpose**: To calculate the overall completion percentage of the `Process` based on its checklist items.
-   **Logic**:
    -   If no checklist items exist for the process, returns `0`.
    -   Aggregates the `percentage` values from the `ChecklistItemDefinition` of all `ProcessChecklistItem`s that are marked as `is_completed = True`.
    -   Returns the sum of these percentages.
-   **Called From**: This is a utility method that can be called anywhere an instance of `Process` is available to determine its current progress (e.g., in views, templates, or other model methods).

```python
# Excerpt from app/models.py
# def get_progress_percentage(self):
#     """Calculates the total progress percentage based on completed checklist items."""
#     if not self.checklist_items.exists():
#         return 0

#     completed_percentage = self.checklist_items.filter(is_completed=True).aggregate(
#         total_percentage=models.Sum('definition__percentage')
#     )['total_percentage'] or 0

#     return completed_percentage
```

## `EN_MODIFICACION` Status

The `ProcessStatusChoices.EN_MODIFICACION` status was introduced to explicitly handle scenarios where a process, which might have already progressed, needs to be altered. When a process enters this state:
- Its checklist items are reset via `_reset_checklist_items()`.
- This ensures that progress is re-evaluated after modifications are made.

This systematic approach to checklist management and status logging provides better control, traceability, and clarity for processes within the application.
