import logging
from datetime import date, timedelta

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

from .models import Equipment, ProcessTypeChoices, Report, RoleChoices, User

logger = logging.getLogger(__name__)


# Forms
class UserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ["title", "description", "pdf_file", "process", "estado_reporte"]


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
        # Lógica específica para usuarios de tipo Cliente
        # Determinar qué tipo de proceso y reporte mostrar
        # Usa 'calculo_blindajes' como valor por defecto
        proceso_activo = request.GET.get("proceso_activo", "calculo_blindajes")
        reporte_activo = request.GET.get("reporte_activo", "calculo_blindajes")

        # Filtrar reportes por tipo de proceso
        if reporte_activo == "calculo_blindajes":
            reportes = Report.objects.filter(
                user=request.user,
                process__process_type__process_type=ProcessTypeChoices.CALCULO_BLINDAJES,
            ).order_by("-created_at")[:5]
        elif reporte_activo == "control_calidad":
            reportes = Report.objects.filter(
                user=request.user,
                process__process_type__process_type=ProcessTypeChoices.CONTROL_CALIDAD,
            ).order_by("-created_at")[:5]
        elif reporte_activo == "asesoria":
            reportes = Report.objects.filter(
                user=request.user,
                process__process_type__process_type=ProcessTypeChoices.ASESORIA,
            ).order_by("-created_at")[:5]
        elif reporte_activo == "otro":
            reportes = Report.objects.filter(
                user=request.user,
                process__process_type__process_type=ProcessTypeChoices.OTRO,
            ).order_by("-created_at")[:5]

        # Filtrar equipos por tipo de proceso
        if proceso_activo == "calculo_blindajes":
            equipos = Equipment.objects.filter(
                user=request.user,
                process__process_type__process_type=ProcessTypeChoices.CALCULO_BLINDAJES,
            ).order_by("-process__fecha_inicio")[:5]
        elif proceso_activo == "control_calidad":
            equipos = Report.objects.filter(
                user=request.user,
                process__process_type__process_type=ProcessTypeChoices.CONTROL_CALIDAD,
            ).order_by("-process__fecha_inicio")[:5]
        elif proceso_activo == "asesoria":
            equipos = Report.objects.filter(
                user=request.user,
                process__process_type__process_type=ProcessTypeChoices.ASESORIA,
            ).order_by("-process__fecha_inicio")[:5]
        elif proceso_activo == "otro":
            equipos = Report.objects.filter(
                user=request.user,
                process__process_type__process_type=ProcessTypeChoices.OTRO,
            ).order_by("-process__fecha_inicio")[:5]

        # Filtrar equipos con licencia por vencer o vencida para el usuario cliente
        hoy = date.today()
        seis_meses_despues = hoy + timedelta(weeks=6 * 4)  # Aproximación de 6 meses

        equipos_licencia_por_vencer = Equipment.objects.filter(
            user=request.user,
            fecha_vigencia_licencia__isnull=False,
            fecha_vigencia_licencia__lte=seis_meses_despues,
        ).order_by("fecha_vigencia_licencia")

        context = {
            "titulo": "Página Principal - Cliente",
            "mensaje": f"Bienvenido, {request.user.first_name or ''} {request.user.last_name or ''}",
            "reportes": reportes,
            "equipos": equipos,
            "equipos_licencia_por_vencer": equipos_licencia_por_vencer,
            "proceso_activo": proceso_activo,  # Pasa el tipo de proceso activo al contexto
            "reporte_activo": reporte_activo,  # Pasa el tipo de reporte activo al contexto
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
        form.instance.user = self.request.user
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
