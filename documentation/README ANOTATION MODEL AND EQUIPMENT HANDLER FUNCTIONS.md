## Anotacion Model and Tests

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
