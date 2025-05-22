import logging
from datetime import date, datetime, timedelta

from django import forms
from django.contrib.auth import logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .models import Equipment, Process, ProcessTypeChoices, Report, RoleChoices, User

logger = logging.getLogger(__name__)


# Forms
class UserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = [
            "title",
            "description",
            "pdf_file",
            "user",
            "process",
            "estado_reporte",
            "fecha_vencimiento",
        ]
        widgets = {
            "fecha_vencimiento": forms.DateInput(attrs={"type": "date"}),
        }


class ProcessForm(forms.ModelForm):
    class Meta:
        model = Process
        fields = ["process_type", "estado", "user", "fecha_final"]
        widgets = {
            "fecha_final": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
        }


class EquipmentForm(forms.ModelForm):
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
        reportes = None
        equipos = None

        hoy = date.today()
        seis_meses_despues = hoy + timedelta(weeks=6 * 4)
        equipos_licencia_por_vencer = Equipment.objects.filter(
            user=request.user,
            fecha_vigencia_licencia__isnull=False,
            fecha_vigencia_licencia__lte=seis_meses_despues,
        ).order_by("fecha_vigencia_licencia")

        if proceso_activo:
            # Filtrar reportes por tipo de proceso
            reportes = Report.objects.filter(
                user=request.user,
                process__process_type=proceso_activo,
            ).order_by("-created_at")[:5]

            # Filtrar equipos por tipo de proceso
            equipos = Equipment.objects.filter(
                user=request.user,
                process__process_type=proceso_activo,
            ).order_by("-process__fecha_inicio")[:5]

        context = {
            "titulo": "RadSolutions",
            "mensaje_bienvenida": f"Bienvenido, {request.user.first_name or ''} {request.user.last_name or ''}",
            "reportes": reportes,
            "equipos": equipos,
            "equipos_licencia_por_vencer": equipos_licencia_por_vencer,
            "proceso_activo": proceso_activo,
            "process_types_choices": ProcessTypeChoices.choices,
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
class UserListView(LoginRequiredMixin, ListView):
    model = User
    template_name = "users/user_list.html"
    context_object_name = (
        "users"  # es el nombre que usamos en el template para referirse a la vista
    )
    login_url = "/login/"


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = "users/user_detail.html"
    context_object_name = "user"
    login_url = "/login/"


class UserCreateView(LoginRequiredMixin, CreateView):
    model = User
    form_class = UserForm
    template_name = "users/user_form.html"
    success_url = reverse_lazy("user_list")  # cuando se crea lo redirije aquí.
    login_url = "/login/"


class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserForm
    template_name = "users/user_form.html"
    success_url = reverse_lazy("user_list")
    login_url = "/login/"


class UserDeleteView(LoginRequiredMixin, DeleteView):
    model = User
    template_name = "users/user_confirm_delete.html"
    success_url = reverse_lazy("user_list")
    login_url = "/login/"


# Report Views
class ReportListView(LoginRequiredMixin, ListView):
    model = Report
    template_name = "reports/report_list.html"
    context_object_name = "reports"
    login_url = "/login/"

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

        # Filtrar por tipo de proceso
        if process_type_filter != "todos":
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

        return context


class ReportDetailView(LoginRequiredMixin, DetailView):
    model = Report
    template_name = "reports/report_detail.html"
    context_object_name = "report"
    login_url = "/login/"


class ReportCreateView(LoginRequiredMixin, CreateView):
    model = Report
    form_class = ReportForm
    template_name = "reports/report_form.html"
    success_url = reverse_lazy("report_list")
    login_url = "/login/"

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


class ReportUpdateView(LoginRequiredMixin, UpdateView):
    model = Report
    form_class = ReportForm
    template_name = "reports/report_form.html"
    success_url = reverse_lazy("report_list")
    login_url = "/login/"


class ReportDeleteView(LoginRequiredMixin, DeleteView):
    model = Report
    template_name = "reports/report_confirm_delete.html"
    success_url = reverse_lazy("report_list")
    login_url = "/login/"


# Equipos Views
class EquiposListView(LoginRequiredMixin, ListView):
    model = Equipment
    template_name = "equipos/equipos_list.html"
    context_object_name = "equipos"
    login_url = "/login/"

    def get_queryset(self):
        # Obtener el tipo de proceso desde los parámetros GET
        process_type_filter = self.request.GET.get("process_type", "todos")
        if self.request.user.roles.filter(name=RoleChoices.CLIENTE).exists():
            queryset = Equipment.objects.filter(user=self.request.user)
        else:
            queryset = Equipment.objects.all()

        if process_type_filter != "todos":  # Si se especifica un tipo y no es "todos"
            queryset = queryset.filter(process__process_type=process_type_filter)
        # Si process_type_filter es "todos", no se aplica filtro adicional de tipo de proceso.

        return queryset.order_by("-process__fecha_inicio")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pasar el tipo de proceso seleccionado al contexto
        context["selected_process_type"] = self.request.GET.get("process_type", "todos")
        # Pasar todos los tipos de proceso al contexto para el dropdown
        choices_list = [("todos", "Todos")] + list(ProcessTypeChoices.choices)
        context["process_types"] = choices_list
        return context


class EquiposDetailView(LoginRequiredMixin, DetailView):
    model = Equipment
    template_name = "equipos/equipos_detail.html"
    context_object_name = "equipo"
    login_url = "/login/"


class EquiposCreateView(LoginRequiredMixin, CreateView):
    model = Equipment
    form_class = EquipmentForm
    template_name = "equipos/equipos_form.html"
    success_url = reverse_lazy("equipos_list")
    login_url = "/login/"

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


class EquiposDeleteView(LoginRequiredMixin, DeleteView):
    model = Equipment
    template_name = "equipos/equipos_confirm_delete.html"
    success_url = reverse_lazy("equipos_list")
    login_url = "/login/"


class EquiposUpdateView(LoginRequiredMixin, UpdateView):
    model = Equipment
    form_class = EquipmentForm
    template_name = "equipos/equipos_form.html"
    success_url = reverse_lazy("equipos_list")
    login_url = "/login/"


# Process Views
class ProcessListView(LoginRequiredMixin, ListView):
    model = Equipment
    template_name = "process/process_list.html"
    context_object_name = "equipos"
    login_url = "/login/"

    def get_queryset(self):
        # Obtener el tipo de proceso desde los parámetros GET
        process_type_filter = self.request.GET.get("process_type", "todos")
        if self.request.user.roles.filter(name=RoleChoices.CLIENTE).exists():
            queryset = Equipment.objects.filter(user=self.request.user)
        else:
            queryset = Equipment.objects.all()

        if process_type_filter != "todos":  # Si se especifica un tipo y no es "todos"
            queryset = queryset.filter(process__process_type=process_type_filter)
        # Si process_type_filter es "todos", no se aplica filtro adicional de tipo de proceso.

        return queryset.order_by("-process__fecha_inicio")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pasar el tipo de proceso seleccionado al contexto
        context["selected_process_type"] = self.request.GET.get("process_type", "todos")
        # Pasar todos los tipos de proceso al contexto para el dropdown
        choices_list = [("todos", "Todos")] + list(ProcessTypeChoices.choices)
        context["process_types"] = choices_list
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


class ProcessDeleteView(LoginRequiredMixin, DeleteView):
    model = Process
    template_name = "process/process_confirm_delete.html"
    success_url = reverse_lazy("process_list")
    login_url = "/login/"


class ProcessUpdateView(LoginRequiredMixin, UpdateView):
    model = Process
    form_class = ProcessForm
    template_name = "process/process_form.html"
    success_url = reverse_lazy("process_list")
    login_url = "/login/"
