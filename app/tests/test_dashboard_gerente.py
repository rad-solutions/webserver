from datetime import timedelta

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


class GerenteDashboardTest(TestCase):
    def setUp(self):
        # Crear roles
        self.role_gerente, _ = Role.objects.get_or_create(name=RoleChoices.GERENTE)
        self.role_cliente, _ = Role.objects.get_or_create(name=RoleChoices.CLIENTE)

        # Crear usuario Gerente y loguearlo
        self.gerente = User.objects.create_user(
            username="gerente_user", password="password"
        )
        self.gerente.roles.add(self.role_gerente)
        # Asignar permiso necesario para ver el dashboard
        # Ajusta este permiso si usas uno diferente en la vista
        # from django.contrib.auth.models import Permission
        # view_report_perm = Permission.objects.get(codename='view_report')
        # self.gerente.user_permissions.add(view_report_perm)

        # Crear usuario Cliente con su perfil
        self.cliente = User.objects.create_user(
            username="cliente_test", password="password"
        )
        self.cliente.roles.add(self.role_cliente)
        ClientProfile.objects.create(
            user=self.cliente,
            razon_social="Empresa de Prueba S.A.S.",
            nit="900.123.456-7",
            direccion_instalacion="Calle Falsa 123",
            departamento="Antioquia",
            municipio="Medellín",
        )

        # Crear procesos con diferentes fechas de finalización
        hoy = timezone.now()
        self.proceso_vencido = Process.objects.create(
            user=self.cliente,
            process_type=ProcessTypeChoices.ASESORIA,
            estado=ProcessStatusChoices.EN_PROGRESO,
            fecha_final=hoy - timedelta(days=15),
        )
        self.proceso_vencido.assigned_to.add(self.gerente)
        self.proceso_vencido.save()
        self.proceso_proximo = Process.objects.create(
            user=self.cliente,
            process_type=ProcessTypeChoices.CONTROL_CALIDAD,
            estado=ProcessStatusChoices.EN_PROGRESO,
            fecha_final=hoy + timedelta(days=15),
        )
        self.proceso_proximo.assigned_to.add(self.gerente)
        self.proceso_proximo.save()
        self.proceso_en_progreso = Process.objects.create(
            user=self.cliente,
            process_type=ProcessTypeChoices.CALCULO_BLINDAJES,
            estado=ProcessStatusChoices.EN_PROGRESO,
            fecha_final=hoy + timedelta(days=90),
        )
        self.proceso_en_progreso.assigned_to.add(self.gerente)
        self.proceso_en_progreso.save()
        self.proceso_sin_fecha = Process.objects.create(
            user=self.cliente,
            process_type=ProcessTypeChoices.OTRO,
            estado=ProcessStatusChoices.EN_PROGRESO,
            fecha_final=None,  # Debe contar como "En Progreso"
        )
        self.proceso_finalizado = Process.objects.create(
            user=self.cliente,
            process_type=ProcessTypeChoices.ASESORIA,
            estado=ProcessStatusChoices.FINALIZADO,  # No debe aparecer
            fecha_final=hoy - timedelta(days=100),
        )

        self.client.login(username="gerente_user", password="password")
        self.url = reverse("dashboard_gerente")

    def test_dashboard_access_permissions(self):
        """Verifica que solo el gerente pueda acceder al dashboard."""
        # Gerente tiene acceso
        response = self.client.get(reverse("home"))
        self.assertRedirects(response, reverse("dashboard_gerente"))

        # Cliente no tiene acceso (debería ser redirigido o dar 403)
        self.client.logout()
        self.client.login(username="cliente_test", password="password")
        response = self.client.get(reverse("home"))
        # La vista main redirige a home, y home redirige al dashboard del cliente
        self.assertEqual(response.status_code, 200)

        # Usuario no autenticado no tiene acceso
        self.client.logout()
        response = self.client.get(reverse("dashboard_gerente"))
        self.assertEqual(response.status_code, 403)

    def test_process_categorization_in_context(self):
        """Verifica que los procesos se categoricen correctamente en el contexto."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        # Verificar procesos vencidos
        procesos_vencidos = response.context["procesos_vencidos"]
        self.assertEqual(len(procesos_vencidos), 1)
        self.assertIn(self.proceso_vencido, procesos_vencidos)
        self.assertEqual(procesos_vencidos[0].dias_vencido, 15)

        # Verificar procesos próximos a vencer
        procesos_proximos = response.context["procesos_proximos"]
        self.assertEqual(len(procesos_proximos), 1)
        self.assertIn(self.proceso_proximo, procesos_proximos)

        # Verificar procesos en progreso (incluye el que no tiene fecha)
        procesos_en_progreso = response.context["procesos_en_progreso"]
        self.assertEqual(len(procesos_en_progreso), 2)
        self.assertIn(self.proceso_en_progreso, procesos_en_progreso)
        self.assertIn(self.proceso_sin_fecha, procesos_en_progreso)

        # El proceso finalizado no debe estar en ninguna lista
        self.assertNotIn(self.proceso_finalizado, procesos_vencidos)
        self.assertNotIn(self.proceso_finalizado, procesos_proximos)
        self.assertNotIn(self.proceso_finalizado, procesos_en_progreso)

    def test_chart_data_in_context(self):
        """Verifica que los datos para la gráfica sean correctos."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        chart_data = response.context["chart_data"]
        self.assertIsNotNone(chart_data)
        self.assertEqual(
            chart_data["labels"], ["Vencidos", "Próximos a Vencer", "En Progreso"]
        )
        self.assertEqual(chart_data["data"], [1, 1, 2])  # Corresponde a las listas

    def test_template_displays_process_details(self):
        """Verifica que el template renderice los detalles de los procesos."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        # Verificar contenido de la card de vencidos
        self.assertContains(response, "Procesos Vencidos (1)")
        self.assertContains(response, self.proceso_vencido.get_process_type_display())
        self.assertContains(response, "Empresa de Prueba S.A.S.")  # Razón Social
        self.assertContains(response, self.gerente.get_full_name())  # Asignado a
        self.assertContains(response, "15 días vencido")  # Badge de días vencido

        # Verificar contenido de la card de próximos a vencer
        self.assertContains(response, "Próximos a Vencer (1)")
        self.assertContains(response, self.proceso_proximo.get_process_type_display())

        # Verificar contenido de la card de en progreso
        self.assertContains(response, "Otros Procesos en Progreso (2)")
        self.assertContains(
            response, self.proceso_en_progreso.get_process_type_display()
        )
        self.assertContains(response, self.proceso_sin_fecha.get_process_type_display())

        # El proceso finalizado no debe mostrarse en el HTML
        self.assertNotContains(response, self.proceso_finalizado)
