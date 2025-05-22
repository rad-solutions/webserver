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


class Process(models.Model):

    process_type = models.CharField(
        max_length=20,
        choices=ProcessTypeChoices.choices,
        default=ProcessTypeChoices.OTRO,
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="processes")
    estado = models.CharField(
        max_length=15,
        choices=ProcessStatusChoices.choices,
        default=ProcessStatusChoices.EN_PROGRESO,
    )
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_final = models.DateTimeField(null=True, blank=True)

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

    def get_last_quality_control_report(self):
        """Return the last quality control report for this equipment.

        This method relies on the equipment's 'process' field. It fetches
        the latest report associated with this 'process', but only if the
        'process' itself is of type 'Control de Calidad' (ProcessTypeChoices.CONTROL_CALIDAD).

        Returns None if the equipment has no 'process' assigned, if the assigned
        'process' is not a 'Control de Calidad' type, or if no reports are
        found for that specific process.
        """
        if (
            self.process
            and self.process.process_type == ProcessTypeChoices.CONTROL_CALIDAD
        ):
            # Fetches reports linked to the specific 'process' instance currently associated with this equipment.
            return (
                Report.objects.filter(process=self.process)
                .order_by("-created_at")
                .first()
            )
        return None

    def get_quality_control_history(self):
        """Return a queryset of all quality control reports for this equipment.

        Ordered chronologically by creation date.

        This method relies on the equipment's 'process' field. It fetches
        all reports associated with this 'process', but only if the 'process'
        itself is of type 'Control de Calidad' (ProcessTypeChoices.CONTROL_CALIDAD).

        Returns an empty queryset if the equipment has no 'process' assigned,
        or if the assigned 'process' is not a 'Control de Calidad' type,
        or if no reports are found for that specific process.
        """
        if (
            self.process
            and self.process.process_type == ProcessTypeChoices.CONTROL_CALIDAD
        ):
            # Fetches reports linked to the specific 'process' instance currently associated with this equipment.
            return Report.objects.filter(process=self.process).order_by("created_at")
        return Report.objects.none()

    def __str__(self):
        return f"{self.nombre} ({self.serial or 'No Serial'}) - Owner: {self.user.username if self.user else 'None'}"

    class Meta:
        permissions = [
            ("manage_equipment", "Can create and edit equipment"),
        ]


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
