from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from app.storage import PDFStorage


class RoleChoices(models.TextChoices):
    CLIENTE = "cliente", _("Cliente")
    GERENTE = "gerente", _("Gerente")
    DIRECTOR_TECNICO = "director_tecnico", _("Director Técnico")
    PERSONAL_TECNICO_APOYO = "personal_tecnico_apoyo", _("Personal Técnico de Apoyo")
    PERSONAL_ADMINISTRATIVO = "personal_administrativo", _("Personal Administrativo")


class Role(models.Model):
    name = models.CharField(max_length=30, choices=RoleChoices.choices, unique=True)

    def __str__(self):
        return self.get_name_display()


class User(AbstractUser):
    created_at = models.DateTimeField(auto_now_add=True)

    roles = models.ManyToManyField(Role, blank=True, related_name="users")
    # Add fields for internal users if they are not covered by AbstractUser
    # For example, 'perfil' is essentially covered by 'roles'

    def __str__(self):

        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name} ({self.email or self.username})"
        return self.username

    class Meta(AbstractUser.Meta):
        permissions = [
            ("add_external_user", "Can add external users only"),
        ]


class ClientProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, primary_key=True, related_name="client_profile"
    )
    razon_social = models.CharField(max_length=255)
    nit = models.CharField(max_length=20, unique=True)
    representante_legal = models.CharField(max_length=255, blank=True, null=True)
    direccion_instalacion = models.CharField(max_length=255)
    departamento = models.CharField(max_length=100)
    municipio = models.CharField(max_length=100)
    persona_contacto = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.razon_social} ({self.nit})"


class PracticeCategoryChoices(models.TextChoices):
    VETERINARIA = "veterinaria", _("Veterinaria")
    INDUSTRIAL = "industrial", _("Industrial")
    INVESTIGACION = "investigacion", _("Investigación")
    MEDICA_CAT1 = "medica_cat1", _("Médica Categoría 1")
    MEDICA_CAT2 = "medica_cat2", _("Médica Categoría 2")


class ProcessTypeChoices(models.TextChoices):
    CALCULO_BLINDAJES = "calculo_blindajes", _("Cálculo de Blindajes")
    CONTROL_CALIDAD = "control_calidad", _("Control de Calidad")
    ASESORIA = "asesoria", _("Asesoría")
    OTRO = "otro", _("Otro")


class ProcessStatusChoices(models.TextChoices):
    EN_PROGRESO = "en_progreso", _("En Progreso")
    EN_REVISION = "en_revision", _("En Revisión")
    RADICADO = "radicado", _("Radicado")
    FINALIZADO = "finalizado", _("Finalizado")
    EN_MODIFICACION = "en_modificacion", _("En Modificación")


class Process(models.Model):
    process_type = models.CharField(
        max_length=20,
        choices=ProcessTypeChoices.choices,
        default=ProcessTypeChoices.OTRO,
    )
    practice_category = models.CharField(
        max_length=30,
        choices=PracticeCategoryChoices.choices,
        null=True,
        blank=True,
        verbose_name=_("Categoría de Práctica"),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="processes")
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_processes",
        verbose_name=_("Asignado a"),
        limit_choices_to={
            "roles__name__in": [
                "gerente",
                "director_tecnico",
                "personal_tecnico_apoyo",
            ]
        },
    )
    estado = models.CharField(
        max_length=15,
        choices=ProcessStatusChoices.choices,
        default=ProcessStatusChoices.EN_PROGRESO,
    )
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_final = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        user_who_modified = kwargs.pop("user_who_modified", None)
        is_new = self._state.adding
        old_estado = None

        if not is_new:
            try:
                old_instance = Process.objects.get(pk=self.pk)
                old_estado = old_instance.estado
            except Process.DoesNotExist:
                old_estado = None

        super().save(*args, **kwargs)  # Save the process instance

        if is_new:
            ProcessStatusLog.objects.create(
                proceso=self,
                estado_anterior=None,
                estado_nuevo=self.estado,
                usuario_modifico=user_who_modified,
            )
            self._create_checklist_items()
        elif old_estado != self.estado:  # Existing instance and 'estado' has changed
            ProcessStatusLog.objects.create(
                proceso=self,
                estado_anterior=old_estado,
                estado_nuevo=self.estado,
                usuario_modifico=user_who_modified,
            )
            if self.estado == ProcessStatusChoices.EN_MODIFICACION.value:
                self._reset_checklist_items()
            # If checklist items don't exist (e.g. for older processes) and not entering modification, create them.
            elif not self.checklist_items.exists():
                self._create_checklist_items()

    def _create_checklist_items(self):
        """Create checklist items for this process based on its type and practice category if they don't already exist."""
        if not self.checklist_items.exists():
            filter_kwargs = {"process_type": self.process_type}
            # Only filter by practice_category if process_type is ASESORIA
            if self.process_type == ProcessTypeChoices.ASESORIA:
                filter_kwargs["practice_category"] = self.practice_category
            definitions = ChecklistItemDefinition.objects.filter(**filter_kwargs)
            for definition in definitions:
                ProcessChecklistItem.objects.create(process=self, definition=definition)

    def _reset_checklist_items(self):
        """Reset all checklist items for this process to not completed."""
        self.checklist_items.update(
            is_completed=False, completed_at=None
        )  # Add completed_by=None if you add that field

    def get_progress_percentage(self):
        """Calculate the total progress percentage based on completed checklist items."""
        if not self.checklist_items.exists():
            return 0

        completed_percentage = (
            self.checklist_items.filter(is_completed=True).aggregate(
                total_percentage=models.Sum("definition__percentage")
            )["total_percentage"]
            or 0
        )

        return completed_percentage

    def __str__(self):
        return f"{self.get_process_type_display()} for {self.user.username} - Status: {self.get_estado_display()}"


class EstadoEquipoChoices(models.TextChoices):
    EN_USO = "en_uso", _("En Uso")
    DADO_DE_BAJA = "dado_de_baja", _("Dado de Baja")


class Equipment(models.Model):

    nombre = models.CharField(max_length=150)
    marca = models.CharField(max_length=100, blank=True, null=True)
    modelo = models.CharField(max_length=100, blank=True, null=True)
    serial = models.CharField(max_length=100, unique=True, blank=True, null=True)
    practica_asociada = models.CharField(max_length=200, blank=True, null=True)
    fecha_adquisicion = models.DateField(blank=True, null=True)
    fecha_vigencia_licencia = models.DateField(blank=True, null=True)
    fecha_ultimo_control_calidad = models.DateField(blank=True, null=True)
    fecha_vencimiento_control_calidad = models.DateField(blank=True, null=True)
    tiene_proceso_de_asesoria = models.BooleanField(default=False)
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="equipment"
    )  # This user should be the client
    process = models.ForeignKey(
        Process,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="equipment",
    )
    estado_actual = models.CharField(
        max_length=15,
        choices=EstadoEquipoChoices.choices,
        default=EstadoEquipoChoices.EN_USO,
    )
    sede = models.CharField(max_length=150, blank=True, null=True)

    def get_report_title(self):
        """Return the title for the reports section.

        This is based on the practice category of the associated process.
        """
        environmental_study_categories = [
            PracticeCategoryChoices.VETERINARIA,
            PracticeCategoryChoices.INDUSTRIAL,
            PracticeCategoryChoices.INVESTIGACION,
        ]

        if (
            self.process
            and self.process.practice_category in environmental_study_categories
        ):
            return _("Informes de Estudio Ambiental")
        return _("Informes de Control de Calidad")

    def get_current_xray_tube(self):
        """Return the current X-ray tube from the history."""
        return self.historial_tubos_rayos_x.order_by("-fecha_cambio").first()

    def get_last_quality_control_report(self):
        """Return the last quality control report for this equipment.

        This method searches through all reports directly associated with this
        equipment and filters for those linked to a 'Control de Calidad' process.
        It then returns the most recent one.

        Returns None if no such reports are found.
        """
        # Access reports directly related to this equipment instance via 'self.reports'
        # Then filter by the process_type of the associated process
        return (
            self.reports.filter(
                process__process_type=ProcessTypeChoices.CONTROL_CALIDAD
            )
            .order_by("-created_at")
            .first()
        )

    def get_quality_control_history(self):
        """Return a queryset of all quality control reports for this equipment.

        Ordered chronologically by creation date.

        This method searches through all reports directly associated with this
        equipment and filters for those linked to a 'Control de Calidad' process.

        Returns an empty queryset if no such reports are found.
        """
        # Access reports directly related to this equipment instance via 'self.reports'
        # Then filter by the process_type of the associated process
        return self.reports.filter(
            process__process_type=ProcessTypeChoices.CONTROL_CALIDAD
        ).order_by("created_at")

    def __str__(self):
        return f"{self.nombre} ({self.serial or 'No Serial'}) - Owner: {self.user.username if self.user else 'None'}"

    class Meta:
        permissions = [
            ("manage_equipment", "Can create and edit equipment"),
        ]


class HistorialTuboRayosX(models.Model):
    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        related_name="historial_tubos_rayos_x",
        verbose_name=_("Equipo"),
    )
    marca = models.CharField(_("Marca"), max_length=100)
    modelo = models.CharField(_("Modelo"), max_length=100)
    serial = models.CharField(_("Serial"), max_length=100)
    fecha_cambio = models.DateField(_("Fecha de Cambio"))

    class Meta:
        verbose_name = _("Historial de Tubo de Rayos X")
        verbose_name_plural = _("Historiales de Tubos de Rayos X")
        ordering = ["-fecha_cambio"]

    def __str__(self):
        return (
            f"Tubo para {self.equipment.nombre} - {self.serial} ({self.fecha_cambio})"
        )


class EstadoReporteChoices(models.TextChoices):
    EN_GENERACION = "en_generacion", _("En Generación")
    REVISADO = "revisado", _("Revisado")
    APROBADO = "aprobado", _("Aprobado")


class Report(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="reports"
    )  # This user is likely the creator or owner
    process = models.ForeignKey(
        Process,
        on_delete=models.CASCADE,
        related_name="reports",
        null=True,  # Allow NULL in the database
        blank=True,  # Allow the field to be blank in forms/admin
    )
    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.SET_NULL,  # If equipment is deleted, set this field to NULL
        null=True,
        blank=True,
        related_name="reports",  # Equipment.reports.all() will give reports for that equipment
    )
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=400, blank=True, null=True)
    pdf_file = models.FileField(upload_to="reports_pdfs/", storage=PDFStorage())
    created_at = models.DateTimeField(auto_now_add=True)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    estado_reporte = models.CharField(
        max_length=15,
        choices=EstadoReporteChoices.choices,
        default=EstadoReporteChoices.EN_GENERACION,
    )

    def __str__(self):
        return f"Report by {self.user.first_name}: {self.title}"

    class Meta:
        permissions = [
            ("upload_report", "Can upload reports"),
            ("approve_report", "Can approve reports"),
        ]

    def save(self, *args, **kwargs):
        user_who_modified = kwargs.pop("user_who_modified", None)
        is_new = self._state.adding
        old_instance = None

        if not is_new:
            try:
                old_instance = Report.objects.get(pk=self.pk)
            except Report.DoesNotExist:
                pass  # Should not happen on an update

        super().save(*args, **kwargs)

        # After saving, compare old and new pdf_file
        if old_instance and old_instance.pdf_file != self.pdf_file:
            if self.process:
                # Determine if the file was added, changed,or removed.
                if old_instance.pdf_file and not self.pdf_file:
                    change_description = (
                        f"Se eliminó el archivo del informe '{self.title}'."
                    )
                elif not old_instance.pdf_file and self.pdf_file:
                    change_description = f"Se agregó el archivo '{self.pdf_file.name.split('/')[-1]}' al informe '{self.title}'."
                else:  # It was changed
                    change_description = f"Se actualizó el archivo del informe '{self.title}'. Nuevo archivo: {self.pdf_file.name.split('/')[-1]}."

                Anotacion.objects.create(
                    proceso=self.process,
                    usuario=user_who_modified,
                    contenido=change_description,
                )

    def delete(self, *args, **kwargs):
        if self.pdf_file:
            storage = self.pdf_file.storage
            file_name = self.pdf_file.name

            super().delete(*args, **kwargs)

            if storage.exists(file_name):
                storage.delete(file_name)
        else:
            super().delete(*args, **kwargs)


class Anotacion(models.Model):
    proceso = models.ForeignKey(
        Process, on_delete=models.CASCADE, related_name="anotaciones"
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="anotaciones_creadas",
    )
    contenido = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        process_display = self.proceso.get_process_type_display()
        process_id = self.proceso.id
        user_display = self.usuario.username if self.usuario else "Sistema"
        # auto_now_add=True ensures fecha_creacion is set, so direct strftime is safe
        date_display = self.fecha_creacion.strftime("%Y-%m-%d %H:%M")
        return (
            f"Anotación para {process_display} ({process_id}) "
            f"por {user_display} el {date_display}"
        )

    class Meta:
        ordering = ["-fecha_creacion"]
        verbose_name = _("Anotación")
        verbose_name_plural = _("Anotaciones")


class ChecklistItemDefinition(models.Model):
    process_type = models.CharField(
        max_length=20,
        choices=ProcessTypeChoices.choices,
        verbose_name=_("Tipo de Proceso"),
    )
    practice_category = models.CharField(
        max_length=30,
        choices=PracticeCategoryChoices.choices,
        null=True,
        blank=True,
        verbose_name=_("Categoría de Práctica"),
    )
    name = models.CharField(max_length=255, verbose_name=_("Nombre del Ítem"))
    order = models.PositiveIntegerField(verbose_name=_("Orden"))
    percentage = models.PositiveIntegerField(verbose_name=_("Porcentaje"))

    class Meta:
        verbose_name = _("Definición de Ítem de Checklist")
        verbose_name_plural = _("Definiciones de Ítems de Checklist")
        ordering = ["process_type", "practice_category", "order"]
        unique_together = [
            ("process_type", "practice_category", "name"),
            ("process_type", "practice_category", "order"),
        ]

    def __str__(self):
        return f"{self.get_process_type_display()} - {self.name} ({self.percentage}%)"


class ProcessChecklistItem(models.Model):
    process = models.ForeignKey(
        Process, on_delete=models.CASCADE, related_name="checklist_items"
    )
    definition = models.ForeignKey(ChecklistItemDefinition, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False, verbose_name=_("Completado"))
    started_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Fecha de Inicio")
    )
    completed_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Fecha de Completado")
    )
    # Optional: track who completed it
    completed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="completed_checklist_items",
    )

    class Meta:
        verbose_name = _("Ítem de Checklist de Proceso")
        verbose_name_plural = _("Ítems de Checklist de Proceso")
        ordering = ["process", "definition__order"]
        unique_together = [("process", "definition")]

    def __str__(self):
        return f"{self.process} - {self.definition.name} ({'Completado' if self.is_completed else 'Pendiente'})"

    @property
    def name(self):
        return self.definition.name

    @property
    def percentage(self):
        return self.definition.percentage


class ProcessStatusLog(models.Model):
    proceso = models.ForeignKey(
        Process,
        on_delete=models.CASCADE,
        related_name="status_logs",
        verbose_name=_("Proceso"),
    )
    estado_anterior = models.CharField(
        max_length=50,  # Adjusted to match Process.estado max_length if different
        choices=ProcessStatusChoices.choices,
        null=True,
        blank=True,
        verbose_name=_("Estado Anterior"),
    )
    estado_nuevo = models.CharField(
        max_length=50,  # Adjusted to match Process.estado max_length if different
        choices=ProcessStatusChoices.choices,
        verbose_name=_("Estado Nuevo"),
    )
    fecha_cambio = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Fecha del Cambio")
    )
    usuario_modifico = models.ForeignKey(
        User,  # Assuming User model is directly imported
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="process_status_changes_made",
        verbose_name=_("Usuario que Modificó"),
    )

    def __str__(self):
        user_display = (
            self.usuario_modifico.username if self.usuario_modifico else _("Sistema")
        )
        # Ensure proceso and its fields are accessible for the string representation
        proceso_display = str(
            self.proceso_id
        )  # Default to ID if full object not loaded
        if hasattr(self, "proceso") and self.proceso:
            proceso_display = (
                f"{self.proceso.get_process_type_display()} ({self.proceso.id})"
            )

        estado_anterior_display = (
            self.get_estado_anterior_display() if self.estado_anterior else _("N/A")
        )
        estado_nuevo_display = self.get_estado_nuevo_display()

        return _(
            "Proceso %(proceso_display)s: %(estado_anterior_display)s -> %(estado_nuevo_display)s por %(user_display)s el %(fecha_cambio)s"
        ) % {
            "proceso_display": proceso_display,
            "estado_anterior_display": estado_anterior_display,
            "estado_nuevo_display": estado_nuevo_display,
            "user_display": user_display,
            "fecha_cambio": self.fecha_cambio.strftime("%Y-%m-%d %H:%M"),
        }

    class Meta:
        verbose_name = _("Log de Estado de Proceso")
        verbose_name_plural = _("Logs de Estado de Procesos")
        ordering = ["-fecha_cambio"]
