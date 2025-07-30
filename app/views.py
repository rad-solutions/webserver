import logging
import os
from datetime import date, datetime, timedelta

from dateutil.relativedelta import relativedelta
from django import forms
from django.contrib.auth import logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.views import LoginView, redirect_to_login
from django.core.exceptions import ValidationError
from django.db.models import Count, F, Max, Q
from django.db.models.functions import TruncMonth
from django.forms import inlineformset_factory
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)
from django_select2.forms import ModelSelect2Widget

from .models import (
    Anotacion,
    ChecklistItemStatusChoices,
    ClientBranch,
    ClientProfile,
    Equipment,
    HistorialTuboRayosX,
    Process,
    ProcessChecklistItem,
    ProcessStatusChoices,
    ProcessTypeChoices,
    Report,
    Role,
    RoleChoices,
    User,
)

logger = logging.getLogger(__name__)


# Forms
class UserWithProfileForm(UserCreationForm):
    role = forms.ModelChoiceField(
        queryset=Role.objects.none(),  # Se setea dinámicamente en la vista
        label="Rol",
        required=True,
    )
    # Redefinir campos en español
    username = forms.CharField(
        label="Nombre de Usuario",
        max_length=150,
        help_text="Requerido. 150 caracteres o menos. Letras, dígitos y @/./+/-/_ solamente.",
    )
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text="La contraseña debe contener al menos 8 caracteres, no puede ser únicamente numérica, no debe ser similar a los otros datos y no puede ser demasiado común.",
    )
    password2 = forms.CharField(
        label="Confirmación de Contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text="Introduce la misma contraseña que antes, para su verificación.",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        labels = {
            "username": "Nombre de Usuario",
            "first_name": "Nombre",
            "last_name": "Apellido",
            "email": "Correo Electrónico",
            "role": "Rol",
            "password1": "Contraseña",
            "password2": "Confirmar Contraseña",
        }
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "role",
            "password1",
            "password2",
        ]

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data


class UserEditWithProfileForm(UserCreationForm):
    role = forms.ModelChoiceField(
        queryset=Role.objects.none(),
        label="Rol",
        required=True,
    )
    # Redefinir campos en español
    username = forms.CharField(
        label="Nombre de Usuario",
        max_length=150,
        help_text="Requerido. 150 caracteres o menos. Letras, dígitos y @/./+/-/_ solamente.",
    )
    password2 = forms.CharField(
        label="Confirmación de Contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text="Introduce la misma contraseña que antes, para su verificación.",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "role",
            "password1",
            "password2",
        ]
        labels = {
            "username": "Nombre de Usuario",
            "first_name": "Nombre",
            "last_name": "Apellido",
            "email": "Correo Electrónico",
            "role": "Rol",
            "password1": "Contraseña",
            "password2": "Confirmar Contraseña",
        }

    def clean_username(self):
        username = self.cleaned_data["username"]
        qs = User.objects.filter(username=username)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(
                "Ya existe un usuario con ese nombre de usuario."
            )
        return username

    def clean(self):
        cleaned_data = super().clean()
        # Validar username único excepto para el propio usuario
        username = cleaned_data.get("username")
        if username:
            qs = User.objects.filter(username=username)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error(
                    "username", "Ya existe un usuario con ese nombre de usuario."
                )
        return cleaned_data


class ClientProfileForm(forms.ModelForm):
    class Meta:
        model = ClientProfile
        fields = ["razon_social", "nit", "representante_legal"]
        labels = {
            "razon_social": "Razón Social",
            "nit": "NIT",
            "representante_legal": "Representante Legal",
        }


class ClientBranchForm(forms.ModelForm):
    class Meta:
        model = ClientBranch
        fields = [
            "nombre",
            "direccion_instalacion",
            "departamento",
            "municipio",
            "persona_contacto",
        ]
        labels = {
            "nombre": "Nombre de la Sede",
            "direccion_instalacion": "Dirección de la Sede",
            "departamento": "Departamento",
            "municipio": "Municipio",
            "persona_contacto": "Persona de Contacto",
        }


class ReportForm(forms.ModelForm):
    # --- INICIO: WIDGET SELECT2 ---
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(roles__name=RoleChoices.CLIENTE),
        label="Cliente Asociado",
        widget=ModelSelect2Widget(
            model=User,
            search_fields=[
                "username__icontains",
                "first_name__icontains",
                "last_name__icontains",
                "client_profile__razon_social__icontains",  # ¡Busca también por razón social!
            ],
            attrs={
                "data-placeholder": "Escriba para buscar un cliente...",
                "lang": "es",
            },
        ),
    )
    # --- FIN: WIDGET SELECT2 ---

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        user_id_for_filtering = None
        if (
            self.instance
            and self.instance.pk
            and hasattr(self.instance, "user_id")
            and self.instance.user_id
        ):
            user_id_for_filtering = self.instance.user_id
        # Check self.data for 'user' when form is bound (e.g., POST request)
        elif "user" in self.data:
            try:
                user_id_for_filtering = int(self.data.get("user"))
            except (ValueError, TypeError):
                pass  # user_id_for_filtering remains None

        if "process" in self.fields:
            if user_id_for_filtering:
                self.fields["process"].queryset = Process.objects.filter(
                    user_id=user_id_for_filtering
                ).order_by("process_type")
            else:
                # If no user_id, and it's a new form, queryset should be empty.
                # If it's bound but user_id couldn't be determined, also empty to prevent validation errors with wrong choices.
                if not (
                    self.instance and self.instance.pk
                ):  # Only for new forms or if user_id is missing
                    self.fields["process"].queryset = Process.objects.none()
                # If editing an existing instance without a user_id (should not happen if user is required for process),
                # then self.fields['process'].queryset would retain its default (all processes) or what was set by super()

        if "equipment" in self.fields:
            if user_id_for_filtering:
                self.fields["equipment"].queryset = Equipment.objects.filter(
                    user_id=user_id_for_filtering
                ).order_by("nombre")
            else:
                if not (self.instance and self.instance.pk):
                    self.fields["equipment"].queryset = Equipment.objects.none()

    class Meta:
        model = Report
        fields = [
            "title",
            "description",
            "pdf_file",
            "user",
            "process",
            "equipment",
            "estado_reporte",
            "fecha_vencimiento",
        ]
        labels = {
            "title": "Título del Reporte",
            "description": "Descripción",
            "pdf_file": "Archivo PDF",
            "user": "Cliente Asociado",
            "process": "Proceso Asociado",
            "equipment": "Equipo Asociado",
            "estado_reporte": "Estado del Reporte",
            "fecha_vencimiento": "Fecha de Vencimiento",
        }
        widgets = {
            "fecha_vencimiento": forms.DateInput(attrs={"type": "date"}),
        }

    def clean_pdf_file(self):
        file = self.cleaned_data.get("pdf_file", False)
        if file:
            # Verificar si el archivo tiene un nombre (necesario para obtener la extensión)
            if not hasattr(file, "name"):
                raise ValidationError("No se pudo determinar el nombre del archivo.")

            ext = os.path.splitext(file.name)[1]  # Obtiene la extensión del archivo
            valid_extensions = [".pdf"]
            if not ext.lower() in valid_extensions:
                raise ValidationError(
                    "Archivo no válido. Solo se permiten archivos PDF."
                )
        # Si el campo no es obligatorio y no se sube archivo, no hay nada que validar aquí.
        # Si es obligatorio, la validación de 'required' se maneja antes.
        return file


class ReportStatusAndNoteForm(forms.ModelForm):
    anotacion = forms.CharField(
        label="Anotación al proceso (opcional)",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    class Meta:
        model = Report
        fields = ["estado_reporte"]
        labels = {
            "estado_reporte": "Estado del Reporte",
        }


class ProcessForm(forms.ModelForm):
    # --- INICIO: WIDGET SELECT2 ---
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(roles__name=RoleChoices.CLIENTE),
        label="Cliente Asociado",
        widget=ModelSelect2Widget(
            model=User,
            search_fields=[
                "username__icontains",
                "first_name__icontains",
                "last_name__icontains",
                "client_profile__razon_social__icontains",  # ¡Busca también por razón social!
            ],
            attrs={
                "data-placeholder": "Escriba para buscar un cliente...",
                "lang": "es",
            },
        ),
    )
    # --- FIN: WIDGET SELECT2 ---

    class Meta:
        model = Process
        fields = ["process_type", "practice_category", "estado", "user", "fecha_final"]
        labels = {
            "process_type": "Tipo de Proceso",
            "practice_category": "Categoría de la Práctica",
            "estado": "Estado del Proceso",
            "user": "Cliente",
            "fecha_final": "Fecha de Finalización",
        }
        widgets = {
            "fecha_final": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # El campo siempre se renderiza, pero solo es requerido si es asesoría
        self.fields["practice_category"].required = False

    def clean(self):
        cleaned_data = super().clean()
        process_type = cleaned_data.get("process_type")
        practice_category = cleaned_data.get("practice_category")
        if process_type == ProcessTypeChoices.ASESORIA and not practice_category:
            self.add_error(
                "practice_category",
                "Este campo es obligatorio para procesos de Asesoría.",
            )
        return cleaned_data


class ProcessProgressForm(forms.ModelForm):
    class Meta:
        model = Process
        fields = ["estado"]
        labels = {
            "estado": "Estado del Proceso",
        }
        widgets = {"estado": forms.Select(choices=ProcessStatusChoices.choices)}


class ProcessChecklistItemForm(forms.ModelForm):
    class Meta:
        model = ProcessChecklistItem
        fields = ["status", "started_at", "completed_at", "due_date"]
        labels = {
            "status": "Estado del Ítem",
            "started_at": "Fecha de Inicio",
            "completed_at": "Fecha de Finalización",
            "due_date": "Fecha Límite",
        }
        widgets = {
            "started_at": forms.DateInput(attrs={"type": "date"}),
            "completed_at": forms.DateInput(attrs={"type": "date"}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }


ProcessChecklistItemFormSet = inlineformset_factory(
    Process,
    ProcessChecklistItem,
    form=ProcessChecklistItemForm,
    extra=0,
    can_delete=False,
)


class ProcessAssignmentForm(forms.ModelForm):
    class Meta:
        model = Process
        fields = ["assigned_to"]
        labels = {
            "assigned_to": "Asignar a Usuario Interno",
        }
        widgets = {
            "assigned_to": forms.CheckboxSelectMultiple(
                attrs={"class": "form-check-input"}
            ),
        }

    def clean_assigned_to(self):
        """Valida que no se asignen más de 3 usuarios."""
        assigned_users = self.cleaned_data.get("assigned_to")
        if assigned_users and len(assigned_users) > 3:
            raise forms.ValidationError(
                "No se pueden asignar más de 3 usuarios a un proceso."
            )
        return assigned_users

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo mostrar usuarios con rol de cliente
        self.fields["assigned_to"].queryset = User.objects.exclude(
            roles__name=RoleChoices.CLIENTE
        ).order_by("username")


class AnotacionForm(forms.ModelForm):
    class Meta:
        model = Anotacion
        fields = ["contenido"]
        labels = {
            "contenido": "Contenido de la Anotación",
        }
        widgets = {
            "fecha_final": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
        }


class EquipmentForm(forms.ModelForm):
    # --- INICIO: WIDGET SELECT2 ---
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(roles__name=RoleChoices.CLIENTE),
        label="Cliente Propietario",
        widget=ModelSelect2Widget(
            model=User,
            search_fields=[
                "username__icontains",
                "first_name__icontains",
                "last_name__icontains",
                "client_profile__razon_social__icontains",  # ¡Busca también por razón social!
            ],
            attrs={
                "data-placeholder": "Escriba para buscar un cliente...",
                "lang": "es",
            },
        ),
    )
    # --- FIN: WIDGET SELECT2 ---

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        user_id_for_filtering = None
        if (
            self.instance
            and self.instance.pk
            and hasattr(self.instance, "user_id")
            and self.instance.user_id
        ):
            user_id_for_filtering = self.instance.user_id
        elif "user" in self.data:  # Check self.data for 'user' when form is bound
            try:
                user_id_for_filtering = int(self.data.get("user"))
            except (ValueError, TypeError):
                pass

        if "process" in self.fields:
            if user_id_for_filtering:
                self.fields["process"].queryset = Process.objects.filter(
                    user_id=user_id_for_filtering
                ).order_by("process_type")
            else:
                # For new forms or if user_id is missing, set to none.
                # This ensures that if 'user' is selected via JS, the process list is initially empty
                # and then populated. If 'user' is pre-selected (e.g. editing), this logic is fine.
                # If 'user' is submitted in POST, user_id_for_filtering should be set.
                if (
                    not (self.instance and self.instance.pk)
                    or not user_id_for_filtering
                ):
                    self.fields["process"].queryset = Process.objects.none()
                # If self.instance.pk exists but no user_id_for_filtering, it implies an issue or
                # that the process field should show all. For dependent filtering, it's safer to default to none.

    class Meta:
        model = Equipment
        fields = [
            "equipment_type",
            "marca",
            "modelo",
            "serial",
            "practica_asociada",
            "fecha_adquisicion",
            "fecha_vigencia_licencia",
            "fecha_ultimo_control_calidad",
            "fecha_vencimiento_control_calidad",
            "tiene_proceso_de_asesoria",
            "user",
            "process",
            "estado_actual",
            "sede",
        ]
        labels = {
            "equipment_type": "Tipo de Equipo",
            "marca": "Marca",
            "modelo": "Modelo",
            "serial": "Serial",
            "practica_asociada": "Práctica Asociada",
            "fecha_adquisicion": "Fecha de Adquisición",
            "fecha_vigencia_licencia": "Vigencia de la Licencia",
            "fecha_ultimo_control_calidad": "Último Control de Calidad",
            "fecha_vencimiento_control_calidad": "Vencimiento del Control de Calidad",
            "tiene_proceso_de_asesoria": "Tiene Proceso de Asesoría Activo",
            "user": "Cliente Propietario",
            "process": "Proceso Principal Asociado",
            "estado_actual": "Estado Actual",
            "sede": "Sede",
        }
        widgets = {
            "fecha_adquisicion": forms.DateInput(attrs={"type": "date"}),
            "fecha_vigencia_licencia": forms.DateInput(attrs={"type": "date"}),
            "fecha_ultimo_control_calidad": forms.DateInput(attrs={"type": "date"}),
            "fecha_vencimiento_control_calidad": forms.DateInput(
                attrs={"type": "date"}
            ),
        }


class HistorialTuboRayosXForm(forms.ModelForm):
    class Meta:
        model = HistorialTuboRayosX
        fields = ["marca", "modelo", "serial"]
        labels = {
            "marca": "Marca del Tubo de Rayos X",
            "modelo": "Modelo del Tubo de Rayos X",
            "serial": "Serial del Tubo de Rayos X",
        }


def load_user_processes(request):
    user_id = request.GET.get("user_id")
    processes_data = []
    if user_id:
        processes = Process.objects.filter(user_id=user_id).order_by("process_type")
        processes_data = [{"id": p.id, "name": str(p)} for p in processes]
    return JsonResponse(processes_data, safe=False)


def load_user_equipment(request):
    user_id = request.GET.get("user_id")
    equipment_data = []
    if user_id:
        equipments = Equipment.objects.filter(user_id=user_id).order_by("nombre")
        equipment_data = [{"id": e.id, "name": str(e)} for e in equipments]
    return JsonResponse(equipment_data, safe=False)


def load_client_branches(request):
    """Vista AJAX para cargar las sedes de un cliente específico.

    Usado en los filtros de las listas de reportes y equipos y formulario de creación de equipo.
    """
    user_id = request.GET.get("user_id")
    branches_data = []
    if user_id:
        try:
            # Buscamos las sedes a través del perfil del cliente
            branches = ClientBranch.objects.filter(company__user_id=user_id).order_by(
                "nombre"
            )
            branches_data = [{"id": b.id, "name": b.nombre} for b in branches]
        except (ValueError, TypeError):
            pass  # Si el user_id no es válido, devuelve una lista vacía
    return JsonResponse(branches_data, safe=False)


# Login view
class CustomLoginView(LoginView):
    template_name = "login.html"

    def get_success_url(self):
        return reverse("home")


# Logout view
def logout_view(request):
    logout(request)
    return redirect("login")


class DashboardGerenteView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "dashboard_gerente.html"
    permission_required = "app.view_report"  # O un permiso más específico para gerentes
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoy = timezone.now().date()

        # Define el umbral para "próximo a vencer"
        dias_proximos_a_vencer = 30
        fecha_limite_proximos = hoy + timedelta(days=dias_proximos_a_vencer)

        # Obtener todos los procesos no finalizados, optimizando consultas
        procesos_activos = (
            Process.objects.exclude(estado=ProcessStatusChoices.FINALIZADO)
            .select_related("user__client_profile")
            .prefetch_related("assigned_to")
        )

        procesos_vencidos = []
        procesos_proximos = []
        procesos_en_progreso = []

        for p in procesos_activos:
            if p.fecha_final:
                fecha_final_date = p.fecha_final.date()
                if fecha_final_date < hoy:
                    p.dias_vencido = (hoy - fecha_final_date).days
                    procesos_vencidos.append(p)
                elif hoy <= fecha_final_date <= fecha_limite_proximos:
                    procesos_proximos.append(p)
                else:
                    procesos_en_progreso.append(p)
            else:
                # Si no tiene fecha final, va a "en progreso"
                procesos_en_progreso.append(p)

        context["procesos_vencidos"] = procesos_vencidos
        context["procesos_proximos"] = procesos_proximos
        context["procesos_en_progreso"] = procesos_en_progreso

        # Datos para la gráfica de torta
        context["chart_data"] = {
            "labels": ["Vencidos", "Próximos a Vencer", "En Progreso"],
            "data": [
                len(procesos_vencidos),
                len(procesos_proximos),
                len(procesos_en_progreso),
            ],
        }

        # --- INICIO: Lógica para las nuevas gráficas de barras ---

        # 1. Determinar el rango de fechas desde los parámetros GET
        interval = self.request.GET.get("interval", "current_month")
        start_date_str = self.request.GET.get("start_date")
        end_date_str = self.request.GET.get("end_date")
        start_date, end_date = None, None

        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                interval = "custom"
            except ValueError:
                start_date, end_date = None, None

        if not (start_date and end_date):
            if interval == "last_3_months":
                start_date = hoy - relativedelta(months=3)
                end_date = hoy
            elif interval == "current_year":
                start_date = hoy.replace(month=1, day=1)
                end_date = hoy
            else:
                interval = "current_month"
                start_date = hoy.replace(day=1)
                end_date = hoy

        context["selected_interval"] = interval
        context["start_date_form"] = (
            start_date.strftime("%Y-%m-%d") if start_date else ""
        )
        context["end_date_form"] = end_date.strftime("%Y-%m-%d") if end_date else ""

        # 2. Query base para procesos finalizados en el rango
        completed_processes = Process.objects.filter(
            estado=ProcessStatusChoices.FINALIZADO,
            fecha_final__date__gte=start_date,
            fecha_final__date__lte=end_date,
        ).prefetch_related("assigned_to")

        # 3. Datos para la Gráfica 1: Procesos por Tipo
        process_types_to_chart = [
            ProcessTypeChoices.CALCULO_BLINDAJES,
            ProcessTypeChoices.CONTROL_CALIDAD,
            ProcessTypeChoices.ASESORIA,
            ProcessTypeChoices.ESTUDIO_AMBIENTAL,
        ]
        type_counts = (
            completed_processes.filter(process_type__in=process_types_to_chart)
            .values("process_type")
            .annotate(count=Count("id"))
        )
        type_counts_dict = {item["process_type"]: item["count"] for item in type_counts}
        context["process_type_chart_data"] = {
            "labels": [ProcessTypeChoices(pt).label for pt in process_types_to_chart],
            "data": [
                type_counts_dict.get(pt.value, 0) for pt in process_types_to_chart
            ],
        }

        # 4. Datos para la Gráfica 2: Procesos completados por Usuario
        user_completion_counts = {}
        internal_users = User.objects.exclude(roles__name=RoleChoices.CLIENTE)
        for user in internal_users:
            user_completion_counts[user.get_full_name() or user.username] = 0

        for process in completed_processes:
            for user in process.assigned_to.all():
                if not user.roles.filter(name=RoleChoices.CLIENTE).exists():
                    user_key = user.get_full_name() or user.username
                    if user_key in user_completion_counts:
                        user_completion_counts[user_key] += 1

        filtered_user_counts = {
            user: count for user, count in user_completion_counts.items() if count > 0
        }
        context["user_completion_chart_data"] = {
            "labels": list(filtered_user_counts.keys()),
            "data": list(filtered_user_counts.values()),
        }
        # --- FIN: Lógica para las nuevas gráficas de barras ---

        return context


class DashboardInternoView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "dashboard_interno.html"
    permission_required = (
        "app.change_report"  # Un permiso básico que tengan los usuarios internos
    )
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario_actual = self.request.user
        hoy = timezone.now().date()

        # Define el umbral para "próximo a vencer" (ej. 30 días)
        dias_proximos_a_vencer = 30
        fecha_limite_proximos = hoy + timedelta(days=dias_proximos_a_vencer)

        # Obtener procesos asignados al usuario actual que no estén finalizados
        procesos_asignados = (
            Process.objects.filter(assigned_to__in=[usuario_actual])
            .exclude(estado=ProcessStatusChoices.FINALIZADO)
            .select_related("user__client_profile")
        )  # Optimiza la consulta para obtener el perfil del cliente

        procesos_vencidos = []
        procesos_proximos = []
        procesos_en_progreso = []

        for p in procesos_asignados:
            if p.fecha_final:
                fecha_final_date = p.fecha_final.date()
                if fecha_final_date < hoy:
                    p.dias_vencido = (hoy - fecha_final_date).days
                    procesos_vencidos.append(p)
                elif hoy <= fecha_final_date <= fecha_limite_proximos:
                    procesos_proximos.append(p)
                else:
                    procesos_en_progreso.append(p)
            else:
                # Si no tiene fecha final, se considera "en progreso"
                procesos_en_progreso.append(p)

        context["procesos_vencidos"] = procesos_vencidos
        context["procesos_proximos"] = procesos_proximos
        context["procesos_en_progreso"] = procesos_en_progreso

        # Datos para la gráfica de torta
        context["chart_data"] = {
            "labels": [
                "Mis Procesos Vencidos",
                "Mis Procesos Próximos a Vencer",
                "Mis Otros Procesos",
            ],
            "data": [
                len(procesos_vencidos),
                len(procesos_proximos),
                len(procesos_en_progreso),
            ],
        }

        context["titulo"] = (
            f"Dashboard de {usuario_actual.first_name or usuario_actual.username}"
        )
        return context


def main(request):
    if not request.user.is_authenticated:
        # Si el usuario no está autenticado, mostrar una página de bienvenida sencilla
        context = {
            "titulo": "Bienvenido al sistema de gestión de reportes de RadSolutions",
            "mensaje": "Inicia sesión para acceder al sistema",
        }
        return render(request, "welcome.html", context)

    if request.user.roles.filter(name=RoleChoices.GERENTE).exists():
        # Si es gerente, redirigir a su dashboard
        return redirect("dashboard_gerente")

    if (
        request.user.roles.filter(name=RoleChoices.DIRECTOR_TECNICO).exists()
        or request.user.roles.filter(name=RoleChoices.PERSONAL_TECNICO_APOYO).exists()
        or request.user.roles.filter(name=RoleChoices.PERSONAL_ADMINISTRATIVO).exists()
    ):
        # Si es interno, redirigir a su dashboard
        return redirect("dashboard_interno")

    # Si el usuario está autenticado, mostrar la página principal con acceso a todas las funcionalidades
    if request.user.roles.filter(name=RoleChoices.CLIENTE).exists():
        proceso_activo = request.GET.get("proceso_activo")
        reportes_para_tabla = None
        equipos_asociados = None

        hoy = date.today()
        seis_meses_despues = hoy + timedelta(weeks=6 * 4)
        equipos_licencia_por_vencer = Equipment.objects.filter(
            user=request.user,
            fecha_vigencia_licencia__isnull=False,
            fecha_vigencia_licencia__lte=seis_meses_despues,
        ).order_by("fecha_vigencia_licencia")

        equipos_cc_por_vencer = Equipment.objects.filter(
            user=request.user,
            fecha_vencimiento_control_calidad__isnull=False,
            fecha_vencimiento_control_calidad__lte=seis_meses_despues,
        ).order_by("fecha_vencimiento_control_calidad")

        procesos_activos_cliente = (
            Process.objects.filter(user=request.user)
            .exclude(estado=ProcessStatusChoices.FINALIZADO)
            .order_by("-fecha_inicio")
        )

        # 1. Obtener la fecha de inicio más reciente de un proceso relevante (activo y del tipo filtrado)
        #    asociado a cada equipo a través de los REPORTES DEL USUARIO.

        # Construir el filtro para los procesos dentro de los reportes
        filtro_proceso_en_reporte = ~Q(process__estado=ProcessStatusChoices.FINALIZADO)
        if proceso_activo and proceso_activo != "todos":
            filtro_proceso_en_reporte &= Q(process__process_type=proceso_activo)

        # Obtener {equipment_id: max_fecha_relevante_via_reporte}
        map_equipo_a_fecha_max_proceso_reporte = {
            item["equipment_id"]: item["max_fecha_relevante"]
            for item in Report.objects.filter(
                user=request.user,  # Reportes del usuario actual
                equipment__isnull=False,  # Reporte asociado a un equipo
                process__isnull=False,  # Reporte asociado a un proceso
            )
            .filter(filtro_proceso_en_reporte)
            .values("equipment_id")  # Agrupar por equipo
            .annotate(
                max_fecha_relevante=Max(
                    "process__fecha_inicio"
                )  # Fecha más reciente del proceso del reporte
            )
            .order_by()  # Limpiar cualquier ordenación por defecto
            if item["equipment_id"] is not None
        }

        # 2. Iterar sobre todos los equipos del usuario para determinar si califican y cuál es su fecha de ordenación.
        equipos_candidatos_con_fecha_ordenacion = []
        # Usar select_related para optimizar el acceso a equipo.process y equipo.user
        todos_los_equipos_del_usuario = Equipment.objects.filter(
            user=request.user
        ).select_related("process", "user")

        for equipo in todos_los_equipos_del_usuario:
            fechas_relevantes_para_este_equipo = []

            # a. Considerar el proceso directamente asociado al equipo
            if equipo.process:
                proceso_directo_cumple_tipo = (
                    proceso_activo
                    and proceso_activo != "todos"
                    and equipo.process.process_type == proceso_activo
                ) or (
                    not proceso_activo or proceso_activo == "todos"
                )  # No hay filtro de tipo o es "todos"
                if (
                    equipo.process.estado != ProcessStatusChoices.FINALIZADO
                    and proceso_directo_cumple_tipo
                ):
                    fechas_relevantes_para_este_equipo.append(
                        equipo.process.fecha_inicio
                    )

            # b. Considerar procesos vía reportes (usando el mapa precalculado)
            if equipo.id in map_equipo_a_fecha_max_proceso_reporte:
                fechas_relevantes_para_este_equipo.append(
                    map_equipo_a_fecha_max_proceso_reporte[equipo.id]
                )

            # Si el equipo tiene al menos una fecha relevante (es decir, un proceso activo asociado que cumple el filtro)
            if fechas_relevantes_para_este_equipo:
                # La fecha de ordenación para este equipo será la más reciente de todas sus fechas relevantes
                fecha_ordenacion_para_equipo = max(fechas_relevantes_para_este_equipo)
                equipos_candidatos_con_fecha_ordenacion.append(
                    (equipo, fecha_ordenacion_para_equipo)
                )

        # 3. Ordenar los equipos candidatos por su fecha de ordenación (más reciente primero)
        equipos_candidatos_con_fecha_ordenacion.sort(key=lambda x: x[1], reverse=True)

        # 4. Tomar los primeros 5 equipos
        equipos_asociados = [
            ec_con_fecha[0]
            for ec_con_fecha in equipos_candidatos_con_fecha_ordenacion[:5]
        ]

        # Obtener una lista de los tipos de proceso que el usuario realmente tiene
        user_process_types = list(
            Process.objects.filter(user=request.user)
            .values_list("process_type", flat=True)
            .distinct()
        )

        context = {
            "titulo": "RadSolutions",
            "mensaje_bienvenida": f"Bienvenido, {request.user.first_name or ''} {request.user.last_name or ''}",
            "reportes_para_tabla": reportes_para_tabla,
            "equipos_asociados": equipos_asociados,
            "equipos_licencia_por_vencer": equipos_licencia_por_vencer,
            "equipos_cc_por_vencer": equipos_cc_por_vencer,
            "procesos_activos_cliente": procesos_activos_cliente,
            "proceso_activo": proceso_activo,
            "process_types_choices": ProcessTypeChoices.choices,
            "ProcessTypeChoices": ProcessTypeChoices,
            "user_process_types": user_process_types,
        }
        return render(request, "dashboard_cliente.html", context)
    else:
        # Lógica para otros tipos de usuarios autenticados
        context = {
            "titulo": "Página Principal",
            "mensaje": "Bienvenido a RadSolutions Reports",
        }
        return render(request, "main.html", context)


# User Views
class UserListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = User
    template_name = "users/user_list.html"
    context_object_name = (
        "users"  # es el nombre que usamos en el template para referirse a la vista
    )
    login_url = "/login/"
    permission_required = "app.view_user"
    raise_exception = True
    paginate_by = 20

    def get_context_data(self, **kwargs):
        """Añade la lógica para mostrar los roles de cada usuario."""
        # Primero, obtenemos el contexto base de la clase padre
        context = super().get_context_data(**kwargs)

        # Obtenemos la lista de usuarios del contexto
        users_list = context["users"]

        # Iteramos sobre cada usuario para añadirle la cadena de roles
        for user in users_list:
            # Obtenemos los nombres "display" de todos los roles y los unimos con una coma
            # Ej: "Gerente, Personal Técnico"
            roles_display = ", ".join(
                [role.get_name_display() for role in user.roles.all()]
            )
            # Adjuntamos la cadena como un nuevo atributo al objeto user
            user.roles_display_string = (
                roles_display if roles_display else "Sin rol asignado"
            )

        return context

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect_to_login(
                self.request.get_full_path(),
                self.get_login_url(),
                self.get_redirect_field_name(),
            )
        # User is authenticated, but lacks permission.
        # Delegate to PermissionRequiredMixin's original behavior.
        return PermissionRequiredMixin.handle_no_permission(self)


class UserDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = User
    template_name = "users/user_detail.html"
    context_object_name = "user"
    login_url = "/login/"
    permission_required = "app.view_user"
    raise_exception = True

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect_to_login(
                self.request.get_full_path(),
                self.get_login_url(),
                self.get_redirect_field_name(),
            )
        # User is authenticated, but lacks permission.
        # Delegate to PermissionRequiredMixin's original behavior.
        return PermissionRequiredMixin.handle_no_permission(self)


class UserCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = User
    form_class = UserWithProfileForm
    template_name = "users/user_form.html"
    login_url = "/login/"
    success_url = reverse_lazy("user_list")
    raise_exception = True

    def get_permission_required(self):
        # Permitir acceso si tiene alguno de los dos permisos
        return ("app.add_user", "app.add_external_user")

    def has_permission(self):
        perms = self.get_permission_required()
        return any(self.request.user.has_perm(perm) for perm in perms)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Limitar roles según permisos
        if self.request.user.has_perm(
            "app.add_user"
        ) and not self.request.user.has_perm("app.add_external_user"):
            # Solo usuarios internos (todos menos cliente)
            form.fields["role"].queryset = Role.objects.exclude(
                name=RoleChoices.CLIENTE
            )
        elif self.request.user.has_perm(
            "app.add_external_user"
        ) and not self.request.user.has_perm("app.add_user"):
            # Solo cliente
            form.fields["role"].queryset = Role.objects.filter(name=RoleChoices.CLIENTE)
        elif self.request.user.has_perm("app.add_user") and self.request.user.has_perm(
            "app.add_external_user"
        ):
            # Puede elegir cualquier rol
            form.fields["role"].queryset = Role.objects.all()
        else:
            form.fields["role"].queryset = Role.objects.none()
        return form

    def form_valid(self, form):
        user = form.save()
        role = form.cleaned_data["role"]
        user.roles.set([role])
        self.object = user

        # --- CORRECCIÓN: Lógica de redirección ---
        if role.name == RoleChoices.CLIENTE:
            # Si es cliente, redirigir al formulario de creación de perfil
            return redirect("client_profile_create", user_pk=self.object.pk)
        else:
            # Si es interno, el flujo termina aquí
            return redirect(self.get_success_url())

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect_to_login(
                self.request.get_full_path(),
                self.get_login_url(),
                self.get_redirect_field_name(),
            )
        # User is authenticated, but lacks permission.
        # Delegate to PermissionRequiredMixin's original behavior.
        return PermissionRequiredMixin.handle_no_permission(self)


class UserUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = User
    form_class = UserEditWithProfileForm
    template_name = "users/user_form.html"
    success_url = reverse_lazy("user_list")
    login_url = "/login/"
    raise_exception = True

    def get_permission_required(self):
        # Permitir acceso si tiene alguno de los permisos de edición/creación
        return ("app.change_user", "app.add_user", "app.add_external_user")

    def has_permission(self):
        perms = self.get_permission_required()
        return any(self.request.user.has_perm(perm) for perm in perms)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Limitar roles según permisos (igual que en UserCreateView)
        if self.request.user.has_perm(
            "app.add_user"
        ) and not self.request.user.has_perm("app.add_external_user"):
            form.fields["role"].queryset = Role.objects.exclude(
                name=RoleChoices.CLIENTE
            )
        elif self.request.user.has_perm(
            "app.add_external_user"
        ) and not self.request.user.has_perm("app.add_user"):
            form.fields["role"].queryset = Role.objects.filter(name=RoleChoices.CLIENTE)
        elif self.request.user.has_perm("app.add_user") and self.request.user.has_perm(
            "app.add_external_user"
        ):
            form.fields["role"].queryset = Role.objects.all()
        else:
            form.fields["role"].queryset = Role.objects.none()
        return form

    def form_valid(self, form):
        user = form.save(commit=False)
        # Siempre actualizar la contraseña
        password = form.cleaned_data.get("password1")
        if password:
            user.set_password(password)
        user.save()
        role = form.cleaned_data["role"]
        user.roles.set([role])

        # Si el rol cambia a NO ser cliente, eliminamos el perfil.
        if role.name != RoleChoices.CLIENTE:
            ClientProfile.objects.filter(user=user).delete()
        return redirect(self.get_success_url())

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect_to_login(
                self.request.get_full_path(),
                self.get_login_url(),
                self.get_redirect_field_name(),
            )
        # User is authenticated, but lacks permission.
        # Delegate to PermissionRequiredMixin's original behavior.
        return PermissionRequiredMixin.handle_no_permission(self)


class ClientProfileCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = ClientProfile
    form_class = ClientProfileForm
    template_name = "users/client_profile_form.html"
    permission_required = "app.add_user"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Registrar Perfil del Cliente"
        return context

    def form_valid(self, form):
        user = get_object_or_404(User, pk=self.kwargs["user_pk"])
        form.instance.user = user
        self.object = form.save()
        return redirect(self.get_success_url())

    def get_success_url(self):
        # Redirigir a crear la primera sede, pasando el ID del perfil recién creado
        return reverse_lazy(
            "client_branch_create", kwargs={"profile_pk": self.object.pk}
        )


class ClientBranchCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = ClientBranch
    form_class = ClientBranchForm
    template_name = "users/client_branch_form.html"
    permission_required = "app.add_user"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Registrar Sede del Cliente"
        return context

    def form_valid(self, form):
        profile = get_object_or_404(ClientProfile, pk=self.kwargs["profile_pk"])
        form.instance.company = profile
        self.object = form.save()
        return redirect(self.get_success_url())

    def get_success_url(self):
        # Al final del flujo, redirigir a los detalles del usuario
        profile = get_object_or_404(ClientProfile, pk=self.kwargs["profile_pk"])
        return reverse_lazy("user_detail", kwargs={"pk": profile.user.pk})


class ClientProfileUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = ClientProfile
    form_class = ClientProfileForm
    template_name = "users/client_profile_form.html"
    permission_required = "app.add_user"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Editar Perfil del Cliente"
        return context

    def get_success_url(self):
        return reverse_lazy("user_detail", kwargs={"pk": self.object.user.pk})


class ClientBranchUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = ClientBranch
    form_class = ClientBranchForm
    template_name = "users/client_branch_form.html"
    permission_required = "app.add_user"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Editar Sede del Cliente"
        return context

    def get_success_url(self):
        return reverse_lazy("user_detail", kwargs={"pk": self.object.company.user.pk})


class UserDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = User
    template_name = "users/user_confirm_delete.html"
    success_url = reverse_lazy("user_list")
    login_url = "/login/"
    permission_required = "app.delete_user"
    raise_exception = True

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect_to_login(
                self.request.get_full_path(),
                self.get_login_url(),
                self.get_redirect_field_name(),
            )
        # User is authenticated, but lacks permission.
        # Delegate to PermissionRequiredMixin's original behavior.
        return PermissionRequiredMixin.handle_no_permission(self)


class UserLookupView(LoginRequiredMixin, View):
    """Vista para el widget Select2 que busca usuarios con rol de Cliente.

    Vista de búsqueda para el widget Select2, asegurando que solo se
    muestren usuarios con el rol de Cliente y devolviendo el JSON correcto.
    """

    def get(self, request, *args, **kwargs):
        term = request.GET.get("term", "")

        # Obtener el queryset base de clientes
        queryset = User.objects.filter(roles__name=RoleChoices.CLIENTE)

        # Filtrar si hay un término de búsqueda
        if term:
            queryset = queryset.filter(
                Q(username__icontains=term)
                | Q(first_name__icontains=term)
                | Q(last_name__icontains=term)
                | Q(client_profile__razon_social__icontains=term)
            )

        # Limitar resultados y optimizar.
        # Usamos F() para ordenar por un campo que puede ser nulo, poniendo los nulos al final.
        queryset = queryset.select_related("client_profile").order_by(
            F("client_profile__razon_social").asc(nulls_last=True),
            "username",  # Añadimos un segundo orden para consistencia
        )[:20]

        # Formatear los resultados para Select2, manejando de forma segura los perfiles nulos.
        results = []
        for user in queryset:
            # Determinar el texto a mostrar de forma segura
            display_text = ""
            if hasattr(user, "client_profile") and user.client_profile:
                display_text = user.client_profile.razon_social

            # Si no hay razón social, usar nombre completo o username como fallback
            if not display_text:
                display_text = user.get_full_name() or user.username

            results.append({"id": user.id, "text": display_text})

        return JsonResponse({"results": results})


# Report Views
class ReportListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Report
    template_name = "reports/report_list.html"
    context_object_name = "reports"
    login_url = "/login/"
    permission_required = "app.view_report"
    paginate_by = 20
    raise_exception = True

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect_to_login(
                self.request.get_full_path(),
                self.get_login_url(),
                self.get_redirect_field_name(),
            )
        # User is authenticated, but lacks permission.
        # Delegate to PermissionRequiredMixin's original behavior.
        return PermissionRequiredMixin.handle_no_permission(self)

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtrar por usuario si es CLIENTE
        if self.request.user.roles.filter(name=RoleChoices.CLIENTE).exists():
            queryset = queryset.filter(user=self.request.user)
        # Para otros roles (admin, etc.), por defecto se muestran todos los reportes
        # o podrías añadir lógica de filtrado adicional si es necesario.

        # Obtener parámetros de filtro
        process_type_filter = self.request.GET.get("process_type", "todos")
        start_date_str = self.request.GET.get("start_date")
        end_date_str = self.request.GET.get("end_date")
        equipment_id_filter = self.request.GET.get("equipment_id")
        marca_filter = self.request.GET.get("marca")
        modelo_filter = self.request.GET.get("modelo")
        serial_filter = self.request.GET.get("serial")
        sede_filter = self.request.GET.get("sede")
        client_user_filter = self.request.GET.get("client_user")

        # Variable para saber si el filtro de equipo se aplicó y tuvo éxito
        equipment_filter_cc_applied_successfully = False

        if equipment_id_filter and process_type_filter == "control_calidad":
            try:
                equipment_id = int(equipment_id_filter)
                equipo = Equipment.objects.get(id=equipment_id)
                queryset = equipo.get_quality_control_history()
                equipment_filter_cc_applied_successfully = True
            except (ValueError, TypeError, Equipment.DoesNotExist):
                # Si equipment_id no es un entero válido, no aplicar este filtro
                pass
        elif equipment_id_filter:
            try:
                queryset = queryset.filter(equipment__id=equipment_id_filter)
            except (ValueError, TypeError, Equipment.DoesNotExist):
                # Si equipment_id no es un entero válido, no aplicar este filtro
                pass

        # Filtrar por tipo de proceso
        if (
            not equipment_filter_cc_applied_successfully
            and process_type_filter != "todos"
        ):
            queryset = queryset.filter(process__process_type=process_type_filter)

        # Filtrar por fecha de inicio
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                queryset = queryset.filter(created_at__date__gte=start_date)
            except ValueError:
                pass  # Ignorar fecha inválida

        # Filtrar por fecha de fin
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                queryset = queryset.filter(created_at__date__lte=end_date)
            except ValueError:
                pass  # Ignorar fecha inválida

        # Filtrar por marca, modelo y serial del equipo
        if marca_filter:
            queryset = queryset.filter(equipment__marca__icontains=marca_filter)
        if modelo_filter:
            queryset = queryset.filter(equipment__modelo__icontains=modelo_filter)
        if serial_filter:
            queryset = queryset.filter(equipment__serial__icontains=serial_filter)

        # --- NUEVO: Filtrar por sede ---
        if sede_filter:
            try:
                queryset = queryset.filter(equipment__sede_id=int(sede_filter))
            except (ValueError, TypeError):
                pass  # Ignorar si no es un número
        elif client_user_filter:
            # Si NO se selecciona sede, pero SÍ un cliente, filtrar por todos los equipos de ese cliente.
            try:
                queryset = queryset.filter(equipment__user_id=int(client_user_filter))
            except (ValueError, TypeError):
                pass  # Ignorar si no es un número

        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Para el filtro de tipo de proceso
        choices_list = [("todos", "Todos")] + list(ProcessTypeChoices.choices)
        context["process_types"] = choices_list
        context["selected_process_type"] = self.request.GET.get("process_type", "todos")
        # Para los filtros de fecha
        context["start_date"] = self.request.GET.get("start_date", "")
        context["end_date"] = self.request.GET.get("end_date", "")
        context["selected_equipment_id"] = self.request.GET.get("equipment_id")
        if self.request.user.roles.filter(name=RoleChoices.CLIENTE).exists():
            context["all_equipment"] = Equipment.objects.filter(user=self.request.user)
        else:
            context["all_equipment"] = Equipment.objects.all()
        context["marca_filter"] = self.request.GET.get("marca", "")
        context["modelo_filter"] = self.request.GET.get("modelo", "")
        context["serial_filter"] = self.request.GET.get("serial", "")

        # --- NUEVO: Contexto para el filtro de Sede/Cliente ---
        context["selected_sede_id"] = self.request.GET.get("sede")
        client_user_id = self.request.GET.get("client_user")
        context["selected_client_id"] = client_user_id

        if client_user_id:
            try:
                context["selected_client_object"] = User.objects.select_related(
                    "client_profile"
                ).get(pk=client_user_id)
            except (User.DoesNotExist, ValueError):
                context["selected_client_object"] = None

        if self.request.user.roles.filter(name=RoleChoices.CLIENTE).exists():
            # El cliente solo ve sus propias sedes
            context["client_branches"] = ClientBranch.objects.filter(
                company__user=self.request.user
            )

        if context["selected_equipment_id"]:
            try:
                context["filtered_equipment"] = Equipment.objects.get(
                    id=context["selected_equipment_id"]
                )
            except Equipment.DoesNotExist:
                pass

        return context


class ReportDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Report
    template_name = "reports/report_detail.html"
    context_object_name = "report"
    login_url = "/login/"
    permission_required = "app.view_report"
    raise_exception = True

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect_to_login(
                self.request.get_full_path(),
                self.get_login_url(),
                self.get_redirect_field_name(),
            )
        # User is authenticated, but lacks permission.
        # Delegate to PermissionRequiredMixin's original behavior.
        return PermissionRequiredMixin.handle_no_permission(self)


class ReportCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "app.upload_report"
    raise_exception = True
    model = Report
    form_class = ReportForm
    template_name = "reports/report_form.html"
    success_url = reverse_lazy("report_list")
    login_url = "/login/"

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect_to_login(
                self.request.get_full_path(),
                self.get_login_url(),
                self.get_redirect_field_name(),
            )
        # User is authenticated, but lacks permission.
        # Delegate to PermissionRequiredMixin's original behavior.
        return PermissionRequiredMixin.handle_no_permission(self)

    def form_valid(self, form):
        # Guardar la instancia sin hacer commit a la BD para poder modificarla
        self.object = form.save(commit=False)

        # Llamar al método save() del modelo, pasando el usuario que modifica
        self.object.save(user_who_modified=self.request.user)

        logger.info(f"Archivo guardado exitosamente: {self.object.pdf_file.name}")
        logger.info(f"URL del archivo: {self.object.pdf_file.url}")

        return redirect(self.get_success_url())


class ReportUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Report
    form_class = ReportForm
    template_name = "reports/report_form.html"
    success_url = reverse_lazy("report_list")
    login_url = "/login/"
    permission_required = "app.change_report"
    raise_exception = True

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect_to_login(
                self.request.get_full_path(),
                self.get_login_url(),
                self.get_redirect_field_name(),
            )
        # User is authenticated, but lacks permission.
        # Delegate to PermissionRequiredMixin's original behavior.
        return PermissionRequiredMixin.handle_no_permission(self)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        # Llamar al método save() del modelo, pasando el usuario que modifica
        self.object.save(user_who_modified=self.request.user)
        return redirect(self.get_success_url())


class ReportDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Report
    template_name = "reports/report_confirm_delete.html"
    success_url = reverse_lazy("report_list")
    login_url = "/login/"
    permission_required = "app.delete_report"
    raise_exception = True

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect_to_login(
                self.request.get_full_path(),
                self.get_login_url(),
                self.get_redirect_field_name(),
            )
        # User is authenticated, but lacks permission.
        # Delegate to PermissionRequiredMixin's original behavior.
        return PermissionRequiredMixin.handle_no_permission(self)


class ReportStatusAndNoteUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    model = Report
    form_class = ReportStatusAndNoteForm
    template_name = "reports/report_status_and_note_form.html"
    permission_required = "app.change_report"
    raise_exception = True

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect_to_login(
                self.request.get_full_path(),
                self.get_login_url(),
                self.get_redirect_field_name(),
            )
        # User is authenticated, but lacks permission.
        # Delegate to PermissionRequiredMixin's original behavior.
        return PermissionRequiredMixin.handle_no_permission(self)

    def get_success_url(self):
        return reverse_lazy("report_detail", args=[self.object.id])

    def form_valid(self, form):
        response = super().form_valid(form)
        anotacion_text = form.cleaned_data.get("anotacion", "").strip()
        # Solo crear anotación si hay texto y el reporte tiene proceso asociado
        if anotacion_text and self.object.process:
            Anotacion.objects.create(
                proceso=self.object.process,
                usuario=self.request.user,
                contenido=anotacion_text,
            )
        return response


# Equipos Views
class EquiposListView(LoginRequiredMixin, ListView):
    model = Equipment
    template_name = "equipos/equipos_list.html"
    context_object_name = "equipos"
    login_url = "/login/"
    paginate_by = 20

    def get_queryset(self):
        # Obtener el tipo de proceso desde los parámetros GET
        process_type_filter = self.request.GET.get("process_type", "todos")
        text_search_term = self.request.GET.get(
            "text_search_term", ""
        ).strip()  # Nuevo filtro de texto
        inicio_adq_date_str = self.request.GET.get("inicio_adq_date")
        inicio_vig_lic_date_str = self.request.GET.get("inicio_vig_lic_date")
        inicio_last_cc_date_str = self.request.GET.get("inicio_last_cc_date")
        inicio_venc_cc_date_str = self.request.GET.get("inicio_venc_cc_date")
        end_adq_date_str = self.request.GET.get("end_adq_date")
        end_vig_lic_date_str = self.request.GET.get("end_vig_lic_date")
        end_last_cc_date_str = self.request.GET.get("end_last_cc_date")
        end_venc_cc_date_str = self.request.GET.get("end_venc_cc_date")
        sede_filter = self.request.GET.get("sede")
        client_user_filter = self.request.GET.get("client_user")

        if self.request.user.roles.filter(name=RoleChoices.CLIENTE).exists():
            queryset = Equipment.objects.filter(user=self.request.user)
        else:
            queryset = Equipment.objects.all()

        if process_type_filter != "todos":  # Si se especifica un tipo y no es "todos"
            queryset = queryset.filter(process__process_type=process_type_filter)
        # Si process_type_filter es "todos", no se aplica filtro adicional de tipo de proceso.

        if text_search_term:
            queryset = queryset.filter(
                Q(modelo__icontains=text_search_term)
                | Q(serial__icontains=text_search_term)
            )

        # Filtrar por fecha de adquisición
        if inicio_adq_date_str:
            try:
                inicio_adq_date = datetime.strptime(
                    inicio_adq_date_str, "%Y-%m-%d"
                ).date()
                queryset = queryset.filter(fecha_adquisicion__gte=inicio_adq_date)
            except ValueError:
                pass  # Ignorar fecha inválida

        if end_adq_date_str:
            try:
                end_adq_date = datetime.strptime(end_adq_date_str, "%Y-%m-%d").date()
                queryset = queryset.filter(fecha_adquisicion__lte=end_adq_date)
            except ValueError:
                pass  # Ignorar fecha inválida

        # Filtrar por fecha de vigencia de licencia
        if inicio_vig_lic_date_str:
            try:
                inicio_vig_lic_date = datetime.strptime(
                    inicio_vig_lic_date_str, "%Y-%m-%d"
                ).date()
                queryset = queryset.filter(
                    fecha_vigencia_licencia__gte=inicio_vig_lic_date
                )
            except ValueError:
                pass  # Ignorar fecha inválida

        if end_vig_lic_date_str:
            try:
                end_vig_lic_date = datetime.strptime(
                    end_vig_lic_date_str, "%Y-%m-%d"
                ).date()
                queryset = queryset.filter(
                    fecha_vigencia_licencia__lte=end_vig_lic_date
                )
            except ValueError:
                pass  # Ignorar fecha inválida

        # Filtrar por fecha de último control de calidad
        if inicio_last_cc_date_str:
            try:
                inicio_last_cc_date = datetime.strptime(
                    inicio_last_cc_date_str, "%Y-%m-%d"
                ).date()
                queryset = queryset.filter(
                    fecha_ultimo_control_calidad__gte=inicio_last_cc_date
                )
            except ValueError:
                pass  # Ignorar fecha inválida

        if end_last_cc_date_str:
            try:
                end_last_cc_date = datetime.strptime(
                    end_last_cc_date_str, "%Y-%m-%d"
                ).date()
                queryset = queryset.filter(
                    fecha_ultimo_control_calidad__lte=end_last_cc_date
                )
            except ValueError:
                pass  # Ignorar fecha inválida

        # Filtrar por fecha de vencimiento de control de calidad
        if inicio_venc_cc_date_str:
            try:
                inicio_venc_cc_date = datetime.strptime(
                    inicio_venc_cc_date_str, "%Y-%m-%d"
                ).date()
                queryset = queryset.filter(
                    fecha_vencimiento_control_calidad__gte=inicio_venc_cc_date
                )
            except ValueError:
                pass  # Ignorar fecha inválida

        if end_venc_cc_date_str:
            try:
                end_venc_cc_date = datetime.strptime(
                    end_venc_cc_date_str, "%Y-%m-%d"
                ).date()
                queryset = queryset.filter(
                    fecha_vencimiento_control_calidad__lte=end_venc_cc_date
                )
            except ValueError:
                pass  # Ignorar fecha inválida

        # --- NUEVO: Filtrar por sede ---
        if sede_filter:
            try:
                queryset = queryset.filter(sede_id=int(sede_filter))
            except (ValueError, TypeError):
                pass  # Ignorar si no es un número
        elif client_user_filter:
            # Si NO se selecciona sede, pero SÍ un cliente, filtrar por todos los equipos de ese cliente.
            try:
                queryset = queryset.filter(user_id=int(client_user_filter))
            except (ValueError, TypeError):
                pass  # Ignorar si no es un número

        return queryset.order_by("-process__fecha_inicio")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pasar el tipo de proceso seleccionado al contexto
        context["selected_process_type"] = self.request.GET.get("process_type", "todos")
        # Pasar todos los tipos de proceso al contexto para el dropdown
        choices_list = [("todos", "Todos")] + list(ProcessTypeChoices.choices)
        context["process_types"] = choices_list
        # Pasar el término de búsqueda de texto al contexto
        context["text_search_term"] = self.request.GET.get(
            "text_search_term", ""
        ).strip()
        # Para los filtros de fecha
        context["inicio_adq_date"] = self.request.GET.get("inicio_adq_date", "")
        context["inicio_vig_lic_date"] = self.request.GET.get("inicio_vig_lic_date", "")
        context["inicio_last_cc_date"] = self.request.GET.get("inicio_last_cc_date", "")
        context["inicio_venc_cc_date"] = self.request.GET.get("inicio_venc_cc_date", "")
        context["end_adq_date"] = self.request.GET.get("end_adq_date", "")
        context["end_vig_lic_date"] = self.request.GET.get("end_vig_lic_date", "")
        context["end_last_cc_date"] = self.request.GET.get("end_last_cc_date", "")
        context["end_venc_cc_date"] = self.request.GET.get("end_venc_cc_date", "")

        # --- NUEVO: Contexto para el filtro de Sede/Cliente ---
        context["selected_sede_id"] = self.request.GET.get("sede")
        client_user_id = self.request.GET.get("client_user")
        context["selected_client_id"] = client_user_id

        if client_user_id:
            try:
                context["selected_client_object"] = User.objects.select_related(
                    "client_profile"
                ).get(pk=client_user_id)
            except (User.DoesNotExist, ValueError):
                context["selected_client_object"] = None

        if self.request.user.roles.filter(name=RoleChoices.CLIENTE).exists():
            # El cliente solo ve sus propias sedes
            context["client_branches"] = ClientBranch.objects.filter(
                company__user=self.request.user
            )

        today = timezone.now().date()

        # --- 1. Lógica para el resaltado de filas ---
        # Añadimos flags a cada objeto de equipo para usarlos fácilmente en la plantilla.
        equipos_list = context.get("equipos", [])
        for equipo in equipos_list:
            # Flag para CC que vence en menos de 30 días
            equipo.cc_vence_pronto = False
            if (
                equipo.fecha_vencimiento_control_calidad
                and (equipo.fecha_vencimiento_control_calidad - today).days < 30
            ):
                equipo.cc_vence_pronto = True

            # Flag para licencia que vence en menos de 90 días
            equipo.licencia_vence_pronto = False
            if (
                equipo.fecha_vigencia_licencia
                and (equipo.fecha_vigencia_licencia - today).days < 90
            ):
                equipo.licencia_vence_pronto = True

        # --- 2. Lógica para la gráfica del gerente ---
        context["show_chart"] = False
        if self.request.user.roles.filter(name=RoleChoices.GERENTE).exists():
            context["show_chart"] = True

            interval = self.request.GET.get("interval", "current_month")
            context["selected_interval"] = interval

            now = timezone.now()

            if interval == "last_3_months":
                start_date = now.date() - relativedelta(months=3)
                title = "Últimos 3 Meses"
            elif interval == "current_year":
                start_date = now.date().replace(month=1, day=1)
                title = f"Año {now.year}"
            else:  # default to current_month
                start_date = now.date().replace(day=1)
                title = "Mes Actual"

            # Contar controles de calidad por mes para el usuario actual
            qs = (
                Equipment.objects.filter(
                    fecha_ultimo_control_calidad__gte=start_date,
                    fecha_ultimo_control_calidad__lte=now.date(),
                )
                .annotate(month=TruncMonth("fecha_ultimo_control_calidad"))
                .values("month")
                .annotate(count=Count("id"))
                .order_by("month")
            )

            # Formatear datos para Chart.js, incluyendo meses con 0
            chart_data_dict = {}
            current_month = start_date.replace(day=1)
            while current_month <= now.date():
                chart_data_dict[current_month] = 0
                current_month += relativedelta(months=1)

            for item in qs:
                month_key = item["month"].replace(day=1)
                if month_key in chart_data_dict:
                    chart_data_dict[month_key] = item["count"]

            meses = {
                1: "Ene",
                2: "Feb",
                3: "Mar",
                4: "Abr",
                5: "May",
                6: "Jun",
                7: "Jul",
                8: "Ago",
                9: "Sep",
                10: "Oct",
                11: "Nov",
                12: "Dic",
            }
            labels = [
                f"{meses[d.month]} {d.year}" for d in sorted(chart_data_dict.keys())
            ]
            data = [chart_data_dict[d] for d in sorted(chart_data_dict.keys())]

            context["chart_data"] = {
                "labels": labels,
                "data": data,
                "title": f"Controles de Calidad Realizados ({title})",
            }

        return context


class EquiposDetailView(LoginRequiredMixin, DetailView):
    model = Equipment
    template_name = "equipos/equipos_detail.html"
    context_object_name = "equipo"
    login_url = "/login/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        equipo = self.get_object()

        procesos_activos_asociados = set()

        # 1. Proceso directamente asociado al equipo
        if equipo.process and equipo.process.estado != ProcessStatusChoices.FINALIZADO:
            procesos_activos_asociados.add(equipo.process)

        # 2. Procesos asociados a través de reportes vinculados al equipo
        reportes_del_equipo = Report.objects.filter(equipment=equipo)
        for reporte in reportes_del_equipo:
            if (
                reporte.process
                and reporte.process.estado != ProcessStatusChoices.FINALIZADO
            ):
                procesos_activos_asociados.add(reporte.process)

        context["procesos_activos_del_equipo"] = list(procesos_activos_asociados)
        context["numero_procesos_activos"] = len(procesos_activos_asociados)

        return context


class EquiposCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Equipment
    form_class = EquipmentForm
    template_name = "equipos/equipos_form.html"
    login_url = "/login/"
    permission_required = "app.manage_equipment"
    raise_exception = True

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect_to_login(
                self.request.get_full_path(),
                self.get_login_url(),
                self.get_redirect_field_name(),
            )
        # User is authenticated, but lacks permission.
        # Delegate to PermissionRequiredMixin's original behavior.
        return PermissionRequiredMixin.handle_no_permission(self)

    def get_success_url(self):
        # Redirigir al formulario de actualización del tubo de rayos X
        return reverse_lazy("tubo_update", kwargs={"pk": self.object.id})

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            # Verificar si el archivo se guardó correctamente
            logger.info(
                f"Equipo '{form.instance.nombre}' creado exitosamente por {self.request.user} con ID {form.instance.id}."
            )
            return response
        except Exception as e:
            logger.error(f"Error al guardar el equipo: {str(e)}")
            form.add_error(None, f"Error al guardar el equipo: {str(e)}")
            return self.form_invalid(form)


class EquipoTuboUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = HistorialTuboRayosX
    form_class = HistorialTuboRayosXForm
    template_name = "equipos/tubo_xray_form.html"
    login_url = "/login/"
    permission_required = "app.manage_equipment"
    raise_exception = True

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect_to_login(
                self.request.get_full_path(),
                self.get_login_url(),
                self.get_redirect_field_name(),
            )
        # User is authenticated, but lacks permission.
        # Delegate to PermissionRequiredMixin's original behavior.
        return PermissionRequiredMixin.handle_no_permission(self)

    def get_success_url(self):
        # Redirigir de vuelta a la página de detalle del equipo
        return reverse_lazy("equipos_detail", kwargs={"pk": self.kwargs.get("pk")})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        equipo_id = self.kwargs.get("pk")
        context["equipo"] = get_object_or_404(Equipment, id=equipo_id)
        return context

    def form_valid(self, form):
        equipo_id = self.kwargs.get("pk")
        equipo_obj = get_object_or_404(Equipment, id=equipo_id)

        form.instance.equipment = equipo_obj
        form.instance.fecha_cambio = timezone.now()
        return super().form_valid(form)


class EquiposDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Equipment
    template_name = "equipos/equipos_confirm_delete.html"
    success_url = reverse_lazy("equipos_list")
    login_url = "/login/"
    permission_required = "app.manage_equipment"
    raise_exception = True

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect_to_login(
                self.request.get_full_path(),
                self.get_login_url(),
                self.get_redirect_field_name(),
            )
        # User is authenticated, but lacks permission.
        # Delegate to PermissionRequiredMixin's original behavior.
        return PermissionRequiredMixin.handle_no_permission(self)


class EquiposUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Equipment
    form_class = EquipmentForm
    template_name = "equipos/equipos_form.html"
    success_url = reverse_lazy("equipos_list")
    login_url = "/login/"
    permission_required = "app.manage_equipment"
    raise_exception = True

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect_to_login(
                self.request.get_full_path(),
                self.get_login_url(),
                self.get_redirect_field_name(),
            )
        # User is authenticated, but lacks permission.
        # Delegate to PermissionRequiredMixin's original behavior.
        return PermissionRequiredMixin.handle_no_permission(self)


# Process Views
class ProcessListView(LoginRequiredMixin, ListView):
    model = Equipment
    template_name = "process/process_list.html"
    context_object_name = "equipos"
    login_url = "/login/"
    paginate_by = 20

    def get_queryset(self):
        # Obtener el tipo de proceso desde los parámetros GET
        process_type_filter = self.request.GET.get("process_type", "todos")
        process_status_filter = self.request.GET.get("estado", "todos")
        inicio_start_date_str = self.request.GET.get("inicio_start_date")
        inicio_end_date_str = self.request.GET.get("inicio_end_date")
        fin_start_date_str = self.request.GET.get("fin_start_date")
        fin_end_date_str = self.request.GET.get("fin_end_date")
        if self.request.user.roles.filter(name=RoleChoices.CLIENTE).exists():
            queryset = Equipment.objects.filter(user=self.request.user)
        else:
            queryset = Equipment.objects.all()

        if process_type_filter != "todos":  # Si se especifica un tipo y no es "todos"
            queryset = queryset.filter(process__process_type=process_type_filter)
        # Si process_type_filter es "todos", no se aplica filtro adicional de tipo de proceso.

        if (
            process_status_filter != "todos"
        ):  # Si se especifica un estado y no es "todos"
            queryset = queryset.filter(process__estado=process_status_filter)
        # Si process_status_filter es "todos", no se aplica filtro adicional de estado.

        # Filtrar por fecha de inicio
        if inicio_start_date_str:
            try:
                inicio_start_date = datetime.strptime(
                    inicio_start_date_str, "%Y-%m-%d"
                ).date()
                queryset = queryset.filter(
                    process__fecha_inicio__date__gte=inicio_start_date
                )
            except ValueError:
                pass  # Ignorar fecha inválida

        if inicio_end_date_str:
            try:
                inicio_end_date = datetime.strptime(
                    inicio_end_date_str, "%Y-%m-%d"
                ).date()
                queryset = queryset.filter(
                    process__fecha_inicio__date__lte=inicio_end_date
                )
            except ValueError:
                pass  # Ignorar fecha inválida

        # Filtrar por fecha de fin
        if fin_start_date_str:
            try:
                fin_start_date = datetime.strptime(
                    fin_start_date_str, "%Y-%m-%d"
                ).date()
                queryset = queryset.filter(
                    process__fecha_final__date__gte=fin_start_date
                )
            except ValueError:
                pass  # Ignorar fecha inválida

        if fin_end_date_str:
            try:
                fin_end_date = datetime.strptime(fin_end_date_str, "%Y-%m-%d").date()
                queryset = queryset.filter(process__fecha_final__date__lte=fin_end_date)
            except ValueError:
                pass  # Ignorar fecha inválida

        queryset = queryset.prefetch_related(
            "process__checklist_items",  # Proceso directo y su checklist
            "reports__process__checklist_items",  # Procesos vía reportes y sus checklists
        )

        return queryset.order_by("-process__fecha_inicio")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        equipos = context["equipos"]

        # --- LÓGICA PARA CALCULAR EL PROGRESO DEL PROCESO MÁS RECIENTE ---
        equipment_progress_map = {}
        for equipo in equipos:
            candidate_processes = set()

            # 1. Recolectar proceso asociado directamente
            if equipo.process:
                candidate_processes.add(equipo.process)

            # 2. Recolectar procesos asociados vía reportes (usa datos precargados)
            for report in equipo.reports.all():
                if report.process:
                    candidate_processes.add(report.process)

            most_recent_process = None
            if candidate_processes:
                # Filtrar procesos sin fecha de inicio para evitar errores
                valid_processes = [p for p in candidate_processes if p.fecha_inicio]
                if valid_processes:
                    # 3. Seleccionar el más reciente por fecha de inicio
                    most_recent_process = sorted(
                        valid_processes, key=lambda p: p.fecha_inicio, reverse=True
                    )[0]

            # Guardar el proceso y su progreso en un mapa
            if most_recent_process:
                equipment_progress_map[equipo.id] = {
                    "process": most_recent_process,
                    "progress": most_recent_process.get_progress_percentage(),
                }
            else:
                equipment_progress_map[equipo.id] = {"process": None, "progress": 0}

        context["equipment_progress_map"] = equipment_progress_map
        # Pasar el tipo de proceso seleccionado al contexto
        context["selected_process_type"] = self.request.GET.get("process_type", "todos")
        # Pasar todos los tipos de proceso al contexto para el dropdown
        choices_list = [("todos", "Todos")] + list(ProcessTypeChoices.choices)
        context["process_types"] = choices_list
        status_choices_list = [("todos", "Todos")] + list(ProcessStatusChoices.choices)
        context["process_statuses"] = status_choices_list
        context["selected_estado"] = self.request.GET.get("estado", "todos")
        # Para los filtros de fecha
        context["inicio_start_date"] = self.request.GET.get("inicio_start_date", "")
        context["inicio_end_date"] = self.request.GET.get("inicio_end_date", "")
        context["fin_start_date"] = self.request.GET.get("fin_start_date", "")
        context["fin_end_date"] = self.request.GET.get("fin_end_date", "")
        return context


class ProcessInternalListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Process List for Internal Users.

    Vista para que los usuarios internos vean una lista de TODOS los procesos,
    con filtros avanzados, incluyendo el de usuario asignado.
    """

    model = Process
    template_name = "process/process_internal_list.html"
    context_object_name = "procesos"
    permission_required = "app.add_anotacion"  # Permiso adecuado para usuarios internos
    paginate_by = 20  # Opcional: añade paginación para listas largas

    def get_queryset(self):
        # Empezamos con todos los procesos y optimizamos las consultas
        queryset = (
            super()
            .get_queryset()
            .select_related("user__client_profile")
            .prefetch_related("checklist_items", "assigned_to")
        )

        # --- Reutilizamos la lógica de filtros existentes ---
        process_type_filter = self.request.GET.get("process_type", "todos")
        process_status_filter = self.request.GET.get("estado", "todos")
        inicio_start_date_str = self.request.GET.get("inicio_start_date")
        inicio_end_date_str = self.request.GET.get("inicio_end_date")
        fin_start_date_str = self.request.GET.get("fin_start_date")
        fin_end_date_str = self.request.GET.get("fin_end_date")

        # --- NUEVO FILTRO: Por usuario asignado ---
        assigned_user_id = self.request.GET.get("assigned_user")

        if process_type_filter != "todos":
            queryset = queryset.filter(process_type=process_type_filter)

        if process_status_filter != "todos":
            queryset = queryset.filter(estado=process_status_filter)

        # --- NUEVA LÓGICA DE FILTRO ---
        if assigned_user_id:
            try:
                queryset = queryset.filter(assigned_to__id=int(assigned_user_id))
            except (ValueError, TypeError):
                pass  # Ignorar si el ID no es válido

        # Lógica de filtros de fecha (adaptada para el modelo Process)
        try:
            if inicio_start_date_str:
                queryset = queryset.filter(
                    fecha_inicio__date__gte=datetime.strptime(
                        inicio_start_date_str, "%Y-%m-%d"
                    ).date()
                )
            if inicio_end_date_str:
                queryset = queryset.filter(
                    fecha_inicio__date__lte=datetime.strptime(
                        inicio_end_date_str, "%Y-%m-%d"
                    ).date()
                )
            if fin_start_date_str:
                queryset = queryset.filter(
                    fecha_final__date__gte=datetime.strptime(
                        fin_start_date_str, "%Y-%m-%d"
                    ).date()
                )
            if fin_end_date_str:
                queryset = queryset.filter(
                    fecha_final__date__lte=datetime.strptime(
                        fin_end_date_str, "%Y-%m-%d"
                    ).date()
                )
        except ValueError:
            pass  # Ignorar fechas con formato incorrecto

        # --- NUEVA LÓGICA DE ORDENAMIENTO ---
        sort_by = self.request.GET.get("sort_by", "fecha_inicio")
        sort_dir = self.request.GET.get("sort_dir", "desc")

        sorting_map = {
            "fecha_inicio": "fecha_inicio",
            "fecha_final": "fecha_final",
            "tipo": "process_type",
            "cliente": "user__client_profile__razon_social",
        }

        order_field_name = sorting_map.get(sort_by, "fecha_inicio")

        # Crear la expresión de ordenamiento con F() para manejar NULLs consistentemente
        if sort_dir == "asc":
            # Para descendente, los NULL van al final
            order_expression = F(order_field_name).asc(nulls_last=True)
        else:
            # Para ascendente, los NULL también van al final
            order_expression = F(order_field_name).desc(nulls_last=True)

        # Aplicar ordenamiento primario y un ordenamiento secundario para desempates
        return queryset.order_by(order_expression, "-fecha_inicio")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()

        # --- INICIO: Lógica para calcular días de proceso y vencimiento ---
        for proceso in context["object_list"]:
            # Calcular días de proceso (desde inicio hasta hoy)
            if proceso.fecha_inicio:
                proceso.dias_de_proceso = (today - proceso.fecha_inicio.date()).days
            else:
                proceso.dias_de_proceso = None

            # Calcular días para vencimiento (desde hoy hasta fecha final)  y días vencido
            proceso.dias_hasta_vencimiento = None
            proceso.dias_vencido = None  # Inicializar el atributo
            if proceso.fecha_final:
                dias = (proceso.fecha_final.date() - today).days
                proceso.dias_hasta_vencimiento = dias
                if dias < 0:
                    proceso.dias_vencido = abs(dias)
        # --- FIN: Lógica para calcular días ---

        # Pasar datos para poblar los filtros en el template
        context["process_types"] = [("todos", "Todos")] + ProcessTypeChoices.choices
        context["process_statuses"] = [
            ("todos", "Todos")
        ] + ProcessStatusChoices.choices

        # --- NUEVO CONTEXTO: Lista de usuarios internos para el dropdown ---
        internal_roles = [
            RoleChoices.GERENTE,
            RoleChoices.DIRECTOR_TECNICO,
            RoleChoices.PERSONAL_TECNICO_APOYO,
            RoleChoices.PERSONAL_ADMINISTRATIVO,
        ]
        context["internal_users"] = User.objects.filter(
            roles__name__in=internal_roles
        ).order_by("username")

        # Pasar los valores seleccionados para mantener el estado del formulario
        context["selected_process_type"] = self.request.GET.get("process_type", "todos")
        context["selected_estado"] = self.request.GET.get("estado", "todos")
        context["selected_assigned_user"] = self.request.GET.get("assigned_user")
        context["inicio_start_date"] = self.request.GET.get("inicio_start_date", "")
        context["inicio_end_date"] = self.request.GET.get("inicio_end_date", "")
        context["fin_start_date"] = self.request.GET.get("fin_start_date", "")
        context["fin_end_date"] = self.request.GET.get("fin_end_date", "")

        # --- NUEVO CONTEXTO PARA ORDENAMIENTO ---
        context["sorting_options"] = {
            "fecha_inicio": "Fecha de Inicio",
            "fecha_final": "Fecha de Finalización",
            "tipo": "Tipo de Proceso",
            "cliente": "Razón Social (Cliente)",
        }
        context["selected_sort_by"] = self.request.GET.get("sort_by", "fecha_inicio")
        context["selected_sort_dir"] = self.request.GET.get("sort_dir", "desc")

        return context


class ProcessDetailView(LoginRequiredMixin, DetailView):
    model = Process
    template_name = "process/process_detail.html"
    context_object_name = "process"
    login_url = "/login/"


class ProcessCreateView(LoginRequiredMixin, CreateView):
    model = Process
    form_class = ProcessForm
    template_name = "process/process_form.html"
    success_url = reverse_lazy("process_internal_list")
    login_url = "/login/"

    def form_valid(self, form):
        try:
            self.object = form.save(commit=False)
            # Llamar al método save() del modelo, pasando el usuario que modifica
            self.object.save(user_who_modified=self.request.user)
            logger.info(
                f"Proceso '{self.object.process_type}' creado exitosamente por {self.request.user} con ID {self.object.id}."
            )
            return redirect(self.get_success_url())
        except Exception as e:
            logger.error(
                f"Error crítico al guardar el proceso para el usuario {self.request.user}: {str(e)}"
            )
            form.add_error(None, f"Error al guardar el reporte: {str(e)}")
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ProcessTypeChoices"] = ProcessTypeChoices
        return context


class ProcessDeleteView(LoginRequiredMixin, DeleteView):
    model = Process
    template_name = "process/process_confirm_delete.html"
    success_url = reverse_lazy("process_internal_list")
    login_url = "/login/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ProcessTypeChoices"] = ProcessTypeChoices
        return context


class ProcessUpdateView(LoginRequiredMixin, UpdateView):
    model = Process
    form_class = ProcessForm
    template_name = "process/process_form.html"
    login_url = "/login/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ProcessTypeChoices"] = ProcessTypeChoices
        return context

    def get_success_url(self):
        # Redirigir de vuelta a la página de detalle del proceso
        return reverse_lazy("process_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        self.object = form.save(commit=False)
        # Llamar al método save() del modelo, pasando el usuario que modifica
        self.object.save(user_who_modified=self.request.user)
        return redirect(self.get_success_url())


class ProcessUpdateAssignmentView(
    LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    model = Process
    form_class = ProcessAssignmentForm
    template_name = "process/process_update_assignment.html"
    login_url = "/login/"
    permission_required = "app.manage_equipment"

    def get_success_url(self):
        return reverse_lazy("process_detail", kwargs={"pk": self.object.pk})

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect_to_login(
                self.request.get_full_path(),
                self.get_login_url(),
                self.get_redirect_field_name(),
            )
        # User is authenticated, but lacks permission.
        # Delegate to PermissionRequiredMixin's original behavior.
        return PermissionRequiredMixin.handle_no_permission(self)


class ProcessProgressUpdateView(LoginRequiredMixin, UpdateView):
    model = Process
    form_class = ProcessProgressForm
    template_name = "process/process_progress_form.html"
    login_url = "/login/"

    def get_success_url(self):
        return reverse_lazy("process_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        process = self.object
        if self.request.method == "POST":
            context["checklist_formset"] = ProcessChecklistItemFormSet(
                self.request.POST, instance=process
            )
        else:
            context["checklist_formset"] = ProcessChecklistItemFormSet(instance=process)
        context["ProcessTypeChoices"] = ProcessTypeChoices
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        checklist_formset = ProcessChecklistItemFormSet(
            request.POST, instance=self.object
        )
        # Permitir formset vacío si no hay items
        if not self.object.checklist_items.exists():
            checklist_formset.empty_permitted = True

        if form.is_valid() and (
            not self.object.checklist_items.exists() or checklist_formset.is_valid()
        ):
            process_instance = form.save(commit=False)
            process_instance.save(user_who_modified=request.user)
            if self.object.checklist_items.exists():
                checklist_items = checklist_formset.save(commit=False)
                for item in checklist_items:
                    if item.status == ChecklistItemStatusChoices.APROBADO:
                        item.completed_by = request.user
                    item.save(user_who_modified=self.request.user)
                checklist_formset.save_m2m()
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(
                self.get_context_data(form=form, checklist_formset=checklist_formset)
            )


class AnotacionCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Anotacion
    form_class = AnotacionForm
    template_name = "process/anotacion_form.html"
    login_url = "/login/"
    permission_required = "app.add_anotacion"
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        process_id = self.kwargs.get("process_id")
        context["proceso"] = get_object_or_404(Process, id=process_id)
        return context

    def form_valid(self, form):
        process_id = self.kwargs.get("process_id")
        proceso_obj = get_object_or_404(Process, id=process_id)

        form.instance.proceso = proceso_obj
        form.instance.usuario = self.request.user  # Asignar el usuario logueado
        return super().form_valid(form)

    def get_success_url(self):
        # Redirigir de vuelta a la página de detalle del proceso
        return reverse_lazy(
            "process_detail", kwargs={"pk": self.kwargs.get("process_id")}
        )

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect_to_login(
                self.request.get_full_path(),
                self.get_login_url(),
                self.get_redirect_field_name(),
            )
        # User is authenticated, but lacks permission.
        # Delegate to PermissionRequiredMixin's original behavior.
        return PermissionRequiredMixin.handle_no_permission(self)
