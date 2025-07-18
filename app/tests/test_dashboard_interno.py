from datetime import timedelta

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from ..models import (
    ClientProfile,
    Process,
    ProcessStatusChoices,
    ProcessTypeChoices,
    Role,
    RoleChoices,
    User,
)


class InternoDashboardTest(TestCase):
    def setUp(self):
        # --- Crear Roles ---
        self.role_gerente, _ = Role.objects.get_or_create(name=RoleChoices.GERENTE)
        self.role_cliente, _ = Role.objects.get_or_create(name=RoleChoices.CLIENTE)
        self.role_tecnico, _ = Role.objects.get_or_create(
            name=RoleChoices.DIRECTOR_TECNICO
        )

        # --- Crear Usuarios ---
        self.gerente = User.objects.create_user(
            username="gerente_test", password="password"
        )
        self.gerente.roles.add(self.role_gerente)

        self.cliente = User.objects.create_user(
            username="cliente_test", password="password"
        )
        self.cliente.roles.add(self.role_cliente)
        ClientProfile.objects.create(
            user=self.cliente, razon_social="Cliente de Prueba Inc."
        )

        self.usuario_interno = User.objects.create_user(
            username="tecnico1", password="password", first_name="Juan"
        )
        self.usuario_interno.roles.add(self.role_tecnico)

        # Asignar el permiso requerido por la vista
        change_report_perm = Permission.objects.get(codename="change_report")
        self.usuario_interno.user_permissions.add(change_report_perm)

        self.otro_usuario_interno = User.objects.create_user(
            username="tecnico2", password="password"
        )
        self.otro_usuario_interno.roles.add(self.role_tecnico)

        # --- Crear Procesos ---
        hoy = timezone.now()
        # Procesos asignados al usuario_interno
        self.proceso_vencido = Process.objects.create(
            user=self.cliente,
            assigned_to=self.usuario_interno,
            process_type=ProcessTypeChoices.ASESORIA,
            estado=ProcessStatusChoices.EN_PROGRESO,
            fecha_final=hoy - timedelta(days=10),
        )
        self.proceso_proximo = Process.objects.create(
            user=self.cliente,
            assigned_to=self.usuario_interno,
            process_type=ProcessTypeChoices.CONTROL_CALIDAD,
            estado=ProcessStatusChoices.EN_PROGRESO,
            fecha_final=hoy + timedelta(days=20),
        )
        self.proceso_en_progreso = Process.objects.create(
            user=self.cliente,
            assigned_to=self.usuario_interno,
            process_type=ProcessTypeChoices.CALCULO_BLINDAJES,
            estado=ProcessStatusChoices.EN_PROGRESO,
            fecha_final=hoy + timedelta(days=60),
        )
        self.proceso_finalizado = Process.objects.create(
            user=self.cliente,
            assigned_to=self.usuario_interno,
            process_type=ProcessTypeChoices.OTRO,
            estado=ProcessStatusChoices.FINALIZADO,
            fecha_final=hoy - timedelta(days=30),
        )
        # Proceso asignado a OTRO usuario (no debe aparecer)
        self.proceso_de_otro = Process.objects.create(
            user=self.cliente,
            assigned_to=self.otro_usuario_interno,
            process_type=ProcessTypeChoices.ASESORIA,
            estado=ProcessStatusChoices.EN_PROGRESO,
            fecha_final=hoy + timedelta(days=5),
        )

        self.url = reverse("dashboard_interno")

    # def test_dashboard_access_permissions(self):
    #     """Verifica que solo el usuario interno correcto pueda acceder."""
    #     # Usuario interno logueado tiene acceso
    #     self.client.login(username="tecnico1", password="password")
    #     response = self.client.get(self.url)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTemplateUsed(response, "dashboard_interno.html")

    #     # Gerente es redirigido a su propio dashboard
    #     self.client.login(username="gerente_test", password="password")
    #     response = self.client.get(reverse("home"))  # La lógica está en la vista main
    #     self.assertRedirects(response, reverse("dashboard_gerente"))

    #     # Cliente es redirigido a su dashboard
    #     self.client.login(username="cliente_test", password="password")
    #     response = self.client.get(reverse("home"))
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTemplateUsed(response, "dashboard_cliente.html")

    #     # Usuario no autenticado es redirigido al login
    #     self.client.logout()
    #     response = self.client.get(self.url)
    #     self.assertEqual(response.status_code, 403)

    # def test_process_categorization_is_correct_for_logged_in_user(self):
    #     """Verifica que solo se muestren y categoricen los procesos del usuario logueado."""
    #     self.client.login(username="tecnico1", password="password")
    #     response = self.client.get(self.url)
    #     self.assertEqual(response.status_code, 200)

    #     context = response.context
    #     self.assertIn(self.proceso_vencido, context["procesos_vencidos"])
    #     self.assertEqual(len(context["procesos_vencidos"]), 1)
    #     self.assertEqual(context["procesos_vencidos"][0].dias_vencido, 10)

    #     self.assertIn(self.proceso_proximo, context["procesos_proximos"])
    #     self.assertEqual(len(context["procesos_proximos"]), 1)

    #     self.assertIn(self.proceso_en_progreso, context["procesos_en_progreso"])
    #     self.assertEqual(len(context["procesos_en_progreso"]), 1)

    #     # Verificar que procesos de otros o finalizados NO estén en el contexto
    #     self.assertNotIn(self.proceso_finalizado, context["procesos_vencidos"])
    #     self.assertNotIn(self.proceso_finalizado, context["procesos_proximos"])
    #     self.assertNotIn(self.proceso_finalizado, context["procesos_en_progreso"])

    #     self.assertNotIn(self.proceso_de_otro, context["procesos_vencidos"])
    #     self.assertNotIn(self.proceso_de_otro, context["procesos_proximos"])
    #     self.assertNotIn(self.proceso_de_otro, context["procesos_en_progreso"])

    # def test_chart_data_in_context_is_correct(self):
    #     """Verifica que los datos para la gráfica sean correctos."""
    #     self.client.login(username="tecnico1", password="password")
    #     response = self.client.get(self.url)
    #     self.assertEqual(response.status_code, 200)

    #     chart_data = response.context["chart_data"]
    #     self.assertIsNotNone(chart_data)
    #     self.assertEqual(
    #         chart_data["labels"],
    #         [
    #             "Mis Procesos Vencidos",
    #             "Mis Procesos Próximos a Vencer",
    #             "Mis Otros Procesos",
    #         ],
    #     )
    #     self.assertEqual(chart_data["data"], [1, 1, 1])

    # def test_template_displays_correct_process_details(self):
    #     """Verifica que el template renderice los detalles correctos de los procesos."""
    #     self.client.login(username="tecnico1", password="password")
    #     response = self.client.get(self.url)
    #     self.assertEqual(response.status_code, 200)

    #     # Verificar título del dashboard
    #     self.assertContains(response, "Dashboard de Juan")

    #     # Verificar contenido de la card de vencidos
    #     self.assertContains(response, "Mis Procesos Vencidos (1)")
    #     self.assertContains(response, self.proceso_vencido.get_process_type_display())
    #     self.assertContains(response, "Cliente de Prueba Inc.")  # Razón Social
    #     self.assertContains(response, "10 días vencido")

    #     # Verificar contenido de la card de próximos a vencer
    #     self.assertContains(response, "Mis Procesos Próximos a Vencer (1)")
    #     self.assertContains(response, self.proceso_proximo.get_process_type_display())
