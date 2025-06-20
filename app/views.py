import logging
import os
from datetime import date, datetime, timedelta

from django import forms
from django.contrib.auth import logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.views import LoginView, redirect_to_login
from django.core.exceptions import ValidationError
from django.db.models import Max, Q
from django.forms import inlineformset_factory
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .models import (
    Anotacion,
    ClientProfile,
    Equipment,
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
    # Campos de ClientProfile (solo para cliente)
    razon_social = forms.CharField(required=False)
    nit = forms.CharField(required=False)
    representante_legal = forms.CharField(required=False)
    direccion_instalacion = forms.CharField(required=False)
    departamento = forms.CharField(required=False)
    municipio = forms.CharField(required=False)
    persona_contacto = forms.CharField(required=False)

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

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get("role")
        if role and role.name == RoleChoices.CLIENTE:
            # Validar campos obligatorios de ClientProfile
            for field in [
                "razon_social",
                "nit",
                "direccion_instalacion",
                "departamento",
                "municipio",
            ]:
                if not cleaned_data.get(field):
                    self.add_error(field, "Este campo es obligatorio para clientes.")
        return cleaned_data


class UserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]


class ReportForm(forms.ModelForm):
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


class ProcessForm(forms.ModelForm):
    class Meta:
        model = Process
        fields = ["process_type", "practice_category", "estado", "user", "fecha_final"]
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
        widgets = {"estado": forms.Select(choices=ProcessStatusChoices.choices)}


class ProcessChecklistItemForm(forms.ModelForm):
    class Meta:
        model = ProcessChecklistItem
        fields = ["is_completed"]
        widgets = {
            "is_completed": forms.CheckboxInput(attrs={"class": "form-check-input"})
        }


ProcessChecklistItemFormSet = inlineformset_factory(
    Process,
    ProcessChecklistItem,
    form=ProcessChecklistItemForm,
    extra=0,
    can_delete=False,
)


class AnotacionForm(forms.ModelForm):
    class Meta:
        model = Anotacion
        fields = ["contenido"]
        widgets = {
            "fecha_final": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
        }


class EquipmentForm(forms.ModelForm):
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
            "nombre",
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
        widgets = {
            "fecha_adquisicion": forms.DateInput(attrs={"type": "date"}),
            "fecha_vigencia_licencia": forms.DateInput(attrs={"type": "date"}),
            "fecha_ultimo_control_calidad": forms.DateInput(attrs={"type": "date"}),
            "fecha_vencimiento_control_calidad": forms.DateInput(
                attrs={"type": "date"}
            ),
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


# Login view
class CustomLoginView(LoginView):
    template_name = "login.html"

    def get_success_url(self):
        return reverse("home")


# Logout view
def logout_view(request):
    logout(request)
    return redirect("login")


def main(request):
    if not request.user.is_authenticated:
        # Si el usuario no está autenticado, mostrar una página de bienvenida sencilla
        context = {
            "titulo": "Bienvenido a RadSolutions Reports",
            "mensaje": "Inicia sesión para acceder al sistema",
        }
        return render(request, "welcome.html", context)

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
    permission_required = "app.add_user"
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


class UserDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = User
    template_name = "users/user_detail.html"
    context_object_name = "user"
    login_url = "/login/"
    permission_required = "app.add_user"
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
        response = super().form_valid(form)
        role = form.cleaned_data["role"]
        self.object.roles.set([role])
        if role.name == RoleChoices.CLIENTE:
            ClientProfile.objects.create(
                user=self.object,
                razon_social=form.cleaned_data["razon_social"],
                nit=form.cleaned_data["nit"],
                representante_legal=form.cleaned_data.get("representante_legal"),
                direccion_instalacion=form.cleaned_data["direccion_instalacion"],
                departamento=form.cleaned_data["departamento"],
                municipio=form.cleaned_data["municipio"],
                persona_contacto=form.cleaned_data.get("persona_contacto"),
            )
        return response

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
    form_class = UserForm
    template_name = "users/user_form.html"
    success_url = reverse_lazy("user_list")
    login_url = "/login/"
    permission_required = "app.change_user"
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


# Report Views
class ReportListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Report
    template_name = "reports/report_list.html"
    context_object_name = "reports"
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
        context["all_equipment"] = Equipment.objects.filter(user=self.request.user)

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
        try:
            response = super().form_valid(form)
            # Verificar si el archivo se guardó correctamente
            if hasattr(form.instance, "pdf_file") and form.instance.pdf_file:
                logger.info(
                    f"Archivo guardado exitosamente: {form.instance.pdf_file.name}"
                )
                logger.info(f"URL del archivo: {form.instance.pdf_file.url}")
            return response
        except Exception as e:
            logger.error(f"Error al guardar el reporte: {str(e)}")
            form.add_error(None, f"Error al guardar el reporte: {str(e)}")
            return self.form_invalid(form)


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


# Equipos Views
class EquiposListView(LoginRequiredMixin, ListView):
    model = Equipment
    template_name = "equipos/equipos_list.html"
    context_object_name = "equipos"
    login_url = "/login/"

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

        return queryset.order_by("-process__fecha_inicio")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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


class ProcessDetailView(LoginRequiredMixin, DetailView):
    model = Process
    template_name = "process/process_detail.html"
    context_object_name = "process"
    login_url = "/login/"


class ProcessCreateView(LoginRequiredMixin, CreateView):
    model = Process
    form_class = ProcessForm
    template_name = "process/process_form.html"
    success_url = reverse_lazy("process_list")
    login_url = "/login/"

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            logger.info(
                f"Proceso '{form.instance.process_type}' creado exitosamente por {self.request.user} con ID {form.instance.id}."
            )
            return response
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
    success_url = reverse_lazy("process_list")
    login_url = "/login/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ProcessTypeChoices"] = ProcessTypeChoices
        return context


class ProcessUpdateView(LoginRequiredMixin, UpdateView):
    model = Process
    form_class = ProcessForm
    template_name = "process/process_form.html"
    success_url = reverse_lazy("process_list")
    login_url = "/login/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ProcessTypeChoices"] = ProcessTypeChoices
        return context


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

        # Agrega esto para depurar
        if not checklist_formset.is_valid():
            logger.info("Checklist formset errors:", checklist_formset.errors)

        if form.is_valid() and (
            not self.object.checklist_items.exists() or checklist_formset.is_valid()
        ):
            form.save()
            if self.object.checklist_items.exists():
                checklist_formset.save()
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
