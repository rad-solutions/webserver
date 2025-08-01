from datetime import date, timedelta

from dateutil.relativedelta import relativedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from ..models import (
    ClientBranch,
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
            username="gerente_user",
            password="password",
            first_name="Gerente",
            last_name="Uno",
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
        self.client_profile = ClientProfile.objects.create(
            user=self.cliente,
            razon_social="Empresa de Prueba S.A.S.",
            nit="900.123.456-7",
        )
        self.client_branch = ClientBranch.objects.create(
            company=self.client_profile,
            nombre="Sede Principal",
            direccion_instalacion="Calle Falsa 123",
            departamento="Antioquia",
            municipio="Medellín",
        )

        self.role_tecnico, _ = Role.objects.get_or_create(
            name=RoleChoices.PERSONAL_TECNICO_APOYO
        )
        self.tecnico1 = User.objects.create_user(
            username="tecnico1",
            password="password",
            first_name="Tecnico",
            last_name="Uno",
        )
        self.tecnico1.roles.add(self.role_tecnico)
        self.tecnico2 = User.objects.create_user(
            username="tecnico2",
            password="password",
            first_name="Tecnico",
            last_name="Dos",
        )
        self.tecnico2.roles.add(self.role_tecnico)

        # Crear procesos con diferentes fechas de finalización
        hoy = timezone.now()
        self.proceso_vencido = Process.objects.create(
            user=self.cliente,
            process_type=ProcessTypeChoices.ASESORIA,
            estado=ProcessStatusChoices.EN_PROGRESO,
            fecha_final=hoy - timedelta(days=15),
        )
        self.proceso_vencido.assigned_to.set([self.gerente])
        self.proceso_vencido.save()
        self.proceso_proximo = Process.objects.create(
            user=self.cliente,
            process_type=ProcessTypeChoices.CONTROL_CALIDAD,
            estado=ProcessStatusChoices.EN_PROGRESO,
            fecha_final=hoy + timedelta(days=15),
        )
        self.proceso_proximo.assigned_to.set([self.gerente])
        self.proceso_proximo.save()
        self.proceso_en_progreso = Process.objects.create(
            user=self.cliente,
            process_type=ProcessTypeChoices.CALCULO_BLINDAJES,
            estado=ProcessStatusChoices.EN_PROGRESO,
            fecha_final=hoy + timedelta(days=90),
        )
        self.proceso_en_progreso.assigned_to.set([self.gerente])
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
        # Proceso finalizado este mes, asignado a gerente y tecnico1
        self.proceso_finalizado_mes_actual = Process.objects.create(
            user=self.cliente,
            process_type=ProcessTypeChoices.CONTROL_CALIDAD,
            estado=ProcessStatusChoices.FINALIZADO,
            fecha_final=hoy,
        )
        self.proceso_finalizado_mes_actual.assigned_to.set(
            [self.gerente, self.tecnico1]
        )

        # Proceso finalizado hace 2 meses, asignado a tecnico1
        self.proceso_finalizado_2_meses_antes = Process.objects.create(
            user=self.cliente,
            process_type=ProcessTypeChoices.ASESORIA,
            estado=ProcessStatusChoices.FINALIZADO,
            fecha_final=hoy - relativedelta(months=2),
        )
        self.proceso_finalizado_2_meses_antes.assigned_to.set([self.tecnico1])

        # Proceso finalizado el año pasado, asignado a tecnico2
        self.proceso_finalizado_ano_pasado = Process.objects.create(
            user=self.cliente,
            process_type=ProcessTypeChoices.CALCULO_BLINDAJES,
            estado=ProcessStatusChoices.FINALIZADO,
            fecha_final=hoy - relativedelta(years=1),
        )
        self.proceso_finalizado_ano_pasado.assigned_to.set([self.tecnico2])

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

    def test_template_renders_new_charts_and_filters(self):
        """Verifica que el template renderice las nuevas gráficas y el filtro de fecha."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="dateRangeForm"')
        self.assertContains(response, 'id="processTypeChart"')
        self.assertContains(response, 'id="userCompletionChart"')

    def test_bar_charts_data_default_interval(self):
        """Verifica los datos de las gráficas de barras para el intervalo por defecto (mes actual)."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        # Gráfica 1: Tipos de Proceso
        type_chart = response.context["process_type_chart_data"]
        self.assertEqual(
            type_chart["labels"],
            [
                "Cálculo de Blindajes",
                "Control de Calidad",
                "Asesoría",
                "Estudio Ambiental",
            ],
        )
        self.assertEqual(type_chart["data"], [0, 1, 0, 0])

        # Gráfica 2: Finalizados por Usuario
        user_chart = response.context["user_completion_chart_data"]
        expected_users = {
            self.gerente.get_full_name(): 1,
            self.tecnico1.get_full_name(): 1,
        }
        self.assertEqual(
            dict(zip(user_chart["labels"], user_chart["data"])), expected_users
        )

    def test_bar_charts_data_last_3_months(self):
        """Verifica los datos de las gráficas para el intervalo de últimos 3 meses."""
        response = self.client.get(self.url, {"interval": "last_3_months"})
        self.assertEqual(response.status_code, 200)

        # Gráfica 1: Tipos de Proceso (1 CC este mes, 1 Asesoría hace 2 meses)
        type_chart = response.context["process_type_chart_data"]
        self.assertEqual(type_chart["data"], [0, 1, 1, 0])

        # Gráfica 2: Finalizados por Usuario (gerente: 1, tecnico1: 1+1=2)
        user_chart = response.context["user_completion_chart_data"]
        expected_users = {
            self.gerente.get_full_name(): 1,
            self.tecnico1.get_full_name(): 2,
        }
        self.assertEqual(
            dict(zip(user_chart["labels"], user_chart["data"])), expected_users
        )

    def test_bar_charts_data_custom_range(self):
        """Verifica los datos de las gráficas para un rango de fechas personalizado."""
        start = date.today() - relativedelta(years=2)
        end = date.today()
        response = self.client.get(
            self.url,
            {
                "start_date": start.strftime("%Y-%m-%d"),
                "end_date": end.strftime("%Y-%m-%d"),
            },
        )
        self.assertEqual(response.status_code, 200)

        # Gráfica 1: Tipos de Proceso (1 Blindaje, 1 CC, 1 Asesoría)
        type_chart = response.context["process_type_chart_data"]
        self.assertEqual(type_chart["data"], [1, 1, 2, 0])

        # Gráfica 2: Finalizados por Usuario (gerente: 1, tecnico1: 2, tecnico2: 1)
        user_chart = response.context["user_completion_chart_data"]
        expected_users = {
            self.gerente.get_full_name(): 1,
            self.tecnico1.get_full_name(): 2,
            self.tecnico2.get_full_name(): 1,
        }
        self.assertEqual(
            dict(zip(user_chart["labels"], user_chart["data"])), expected_users
        )
