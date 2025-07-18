## Anotacion Model and Test

### Model (`app/models.py`)

The `Anotacion` model is designed to store annotations or notes related to a `Process` in the system. Each annotation is linked to a specific process, can optionally be linked to a `User` who created it, contains textual content, and automatically records its creation timestamp.

**Fields:**

*   `proceso`: ForeignKey to `Process`. This establishes a many-to-one relationship, where one process can have many annotations. If a `Process` is deleted, all its associated `Anotacion` objects will also be deleted (cascade delete).
*   `usuario`: ForeignKey to `User`. This links the annotation to the user who created it. This field is optional (`null=True`, `blank=True`). If the linked `User` is deleted, this field will be set to `NULL` (`on_delete=models.SET_NULL`), allowing the annotation to persist without an author.
*   `contenido`: TextField. Stores the main text content of the annotation.
*   `fecha_creacion`: DateTimeField. Automatically set to the date and time when the annotation is created (`auto_now_add=True`).

**Meta Options:**

*   `ordering = ['-fecha_creacion']`: Annotations will be ordered by their creation date in descending order (newest first) by default when queried.
*   `verbose_name = _("Anotación")`: User-friendly name for a single object in the admin interface.
*   `verbose_name_plural = _("Anotaciones")`: User-friendly name for multiple objects in the admin interface.

**String Representation (`__str__`)**

Provides a human-readable string representation of an `Anotacion` object, useful for debugging and in the Django admin interface. It includes the process type, process ID, the username of the author (or "Sistema" if no user is linked), and the creation timestamp.

### Tests (`app/tests/test_models.py - AnotacionModelTest`)

The `AnotacionModelTest` class contains a suite of unit tests to ensure the `Anotacion` model behaves as expected.

**Key Tests:**

*   **Creation:** Verifies that an `Anotacion` can be created successfully with all its fields correctly populated.
*   **String Representation:** Checks that the `__str__` method returns the expected format, including a case where the `usuario` is `None`.
*   **Ordering:** Confirms that annotations are correctly ordered by `fecha_creacion` in descending order.
*   **Relationships:**
    *   `test_related_name_from_process`: Ensures that annotations can be accessed from a `Process` instance using the `anotaciones` related name.
    *   `test_related_name_from_user`: Ensures that annotations created by a user can be accessed from a `User` instance using the `anotaciones_creadas` related name.
*   **Null User:** Tests the creation of an annotation where the `usuario` field is `None`.
*   **Cascade Delete with Process:** Verifies that if a `Process` is deleted, all its associated `Anotacion` objects are also deleted.
*   **Set Null on User Delete:**
    *   This is a crucial test to ensure data integrity. It verifies that if a `User` who authored an annotation is deleted, the `usuario` field in the `Anotacion` object is set to `NULL`, and the annotation itself is *not* deleted (provided its parent `Process` still exists).
    *   The test specifically creates an `Anotacion` linked to a `Process` whose `user` is different from the `Anotacion`'s `usuario`. This setup prevents the `Process` (and thus the `Anotacion`) from being cascade-deleted when the `Anotacion`'s author (`usuario`) is deleted, thereby isolating and correctly testing the `SET_NULL` behavior.

## Equipment Model Handler Functions and Tests

### Model Handler Functions (`app/models.py - Equipment`)

The `Equipment` model includes helper methods to retrieve information about related quality control reports.

*   **`get_last_quality_control_report(self)`**:
    *   Returns the most recent `Report` object associated with the equipment's current `process`, but *only if* that `process` is of type `ProcessTypeChoices.CONTROL_CALIDAD`.
    *   If the equipment has no linked `process`, or if the `process` is not a "Control de Calidad" type, or if no reports are found for that specific process, it returns `None`.
    *   The method relies on the `Report.created_at` field to determine the latest report.

*   **`get_quality_control_history(self)`**:
    *   Returns a queryset of all `Report` objects associated with the equipment's current `process`, ordered by their creation date (oldest first).
    *   Similar to `get_last_quality_control_report`, this method only considers reports if the equipment's `process` is of type `ProcessTypeChoices.CONTROL_CALIDAD`.
    *   Returns an empty queryset if the conditions (linked process, correct process type, existing reports) are not met.

### Tests (`app/tests/test_models.py - EquipmentModelTest`)

The `EquipmentModelTest` class includes tests for these handler functions.

**Key Tests for Handler Functions:**

*   **`get_last_quality_control_report` Tests:**
    *   `_no_process`: When equipment has no linked process.
    *   `_wrong_process_type`: When the linked process is not "Control de Calidad".
    *   `_qc_process_no_reports`: When linked to a "Control de Calidad" process that has no reports.
    *   `_one_report`: When there's one relevant QC report.
    *   `_multiple_reports`: When there are multiple QC reports, ensuring the latest is returned.

*   **`get_quality_control_history` Tests:**
    *   `_no_process`: When equipment has no linked process.
    *   `_wrong_process_type`: When the linked process is not "Control de Calidad".
    *   `_qc_process_no_reports`: When linked to a "Control de Calidad" process that has no reports.
    *   `_one_report`: When there's one relevant QC report in the history.
    *   `_multiple_reports_ordered`: When there are multiple QC reports, ensuring they are returned in chronological order (oldest first).

## Report Model Enhancement: Equipment Association

### ForeignKey to Equipment (`app/models.py - Report`)

To enable direct association between a `Report` and an `Equipment`, a ForeignKey field was added to the `Report` model:

*   **`equipment`**: `ForeignKey` to `Equipment`.
    *   `on_delete=models.SET_NULL`: If the associated `Equipment` is deleted, this field in the `Report` will be set to `NULL`. This allows the report to persist even if the equipment record is removed.
    *   `null=True`, `blank=True`: The association is optional. A report does not necessarily need to be linked to a specific piece of equipment.
    *   `related_name="reports"`: Allows accessing all reports associated with an equipment instance via `equipment_instance.reports.all()`.

### Tests for Equipment Association (`app/tests/test_models.py - ReportModelTest`)

New tests were added to `ReportModelTest` to cover the `equipment` ForeignKey:

*   **Setup Update**: The `setUp` method was updated to create an `Equipment` instance for use in tests.
*   **Creation Test Update**: `test_report_creation` was modified to include and verify the `equipment` association.
*   **Creation Without Equipment**: `test_report_creation_without_equipment` ensures reports can be created without an equipment link.
*   **Relationship Test**: `test_equipment_reports_relationship` verifies that reports can be accessed from an `Equipment` instance and handles multiple reports per equipment.
*   **SET_NULL Behavior**: `test_report_equipment_set_null_on_delete` confirms that `report.equipment` becomes `NULL` if the linked `Equipment` is deleted.

## ProcessStatusLog Model and Tests

To track the history of status changes for `Process` objects, a new model `ProcessStatusLog` was introduced.

### Model (`app/models.py - ProcessStatusLog`)

**Fields:**

*   `proceso`: `ForeignKey` to `Process`. Links the log entry to a specific process. Deleting a process will also delete its status logs (`on_delete=models.CASCADE`).
*   `estado_anterior`: `CharField` storing the status of the process *before* the change. Uses `ProcessStatusChoices`. Can be `NULL` (e.g., for the initial status of a new process).
*   `estado_nuevo`: `CharField` storing the status of the process *after* the change. Uses `ProcessStatusChoices`.
*   `fecha_cambio`: `DateTimeField` automatically recording when the status change occurred (`auto_now_add=True`).
*   `usuario_modifico`: Optional `ForeignKey` to `User`, indicating who made the status change. If the user is deleted, this field becomes `NULL` (`on_delete=models.SET_NULL`).

**Meta Options:**

*   `ordering = ['-fecha_cambio']`: Logs are ordered by change date, newest first.
*   `verbose_name = _("Log de Estado de Proceso")`
*   `verbose_name_plural = _("Logs de Estado de Procesos")`

**String Representation (`__str__`)**

Provides a descriptive string for each log entry, e.g., "Proceso Cálculo de Blindajes (123): En Progreso -> En Revisión por admin_user el 2023-10-27 10:30".

### Process Model `save()` Method Override (`app/models.py - Process`)

To automatically create `ProcessStatusLog` entries whenever a `Process` instance's `estado` field changes or when a new `Process` is created, the `save()` method of the `Process` model has been overridden.

**Functionality:**

*   **Intercepts Save Operations**: The custom `save()` method is called automatically every time a `Process` instance is saved.
*   **Handles New Instances**: When a new `Process` is created, its `save()` method is called. After the new `Process` instance is saved to the database (and thus has a primary key), a `ProcessStatusLog` entry is generated to record its initial `estado`. The `estado_anterior` in this log will be `None`, and `estado_nuevo` will be the initial status of the process.
*   **Handles Updates**: For existing `Process` instances:
    *   The method first retrieves the `Process`'s current `estado` from the database *before* the update is applied. This is the `estado_anterior`.
    *   It then compares this `estado_anterior` with the new `estado` that the instance is being updated to (which is `self.estado` within the `save` method).
    *   If the `estado` has changed, a `ProcessStatusLog` entry is created, capturing both the `estado_anterior` and the `estado_nuevo`. If the status has not changed, no log entry is made for the status.
*   **Logs Modifying User**: The `save()` method is designed to accept an optional keyword argument `user_who_modified`. If this argument is provided when `process.save(user_who_modified=some_user)` is called (for example, from a view or a management command where the acting user is known), this `some_user` will be linked to the `ProcessStatusLog` entry in its `usuario_modifico` field. If `user_who_modified` is not provided, the `usuario_modifico` field in the log will be `None` (e.g., "Sistema").

This override ensures that a comprehensive history of status transitions is maintained for every process within the `ProcessStatusLog` model, providing an audit trail of changes.

### Tests (`app/tests/test_models.py - ProcessStatusLogModelTest`)

A new test class `ProcessStatusLogModelTest` was created with the following key tests:

*   **Creation**: Tests basic log creation, including with and without `estado_anterior` and `usuario_modifico`.
*   **String Representation**: Verifies the `__str__` output for different scenarios.
*   **Ordering**: Confirms logs are ordered correctly by `fecha_cambio`.
*   **Cascade Delete with Process**: Ensures logs are deleted if their associated `Process` is deleted.
*   **Set Null on User Delete**: Checks that `usuario_modifico` is set to `NULL` if the linked `User` is deleted.
