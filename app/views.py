import logging

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

from .models import Report, User

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
