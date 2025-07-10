import os
from datetime import date, timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from ..models import (
    Equipment,
    EstadoReporteChoices,
    Process,
    ProcessStatusChoices,
    ProcessTypeChoices,
    Report,
    Role,
    RoleChoices,
    User,
)


class ClientDashboardTest(TestCase):
    def setUp(self):
        # Crear roles si no existen
        self.role_cliente, _ = Role.objects.get_or_create(name=RoleChoices.CLIENTE)

        # Crear un usuario cliente
        self.user = User.objects.create_user(
            username="clientuser",
            email="client@example.com",
            password="testpassword",
            first_name="Client",
            last_name="User",
        )
        self.user.roles.add(self.role_cliente)
        self.other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="testpassword",
            first_name="Other",
            last_name="User",
        )
        self.other_user.roles.add(self.role_cliente)

        # Crear tipos de proceso (usando los valores de ProcessTypeChoices)
        self.process_type_blindajes = ProcessTypeChoices.CALCULO_BLINDAJES
        self.process_type_calidad = ProcessTypeChoices.CONTROL_CALIDAD
        self.process_type_asesoria = ProcessTypeChoices.ASESORIA

        # Crear estado de proceso
        self.process_status = ProcessStatusChoices.EN_PROGRESO

        # Crear procesos para el usuario
        self.process_blindajes = Process.objects.create(
            user=self.user,
            process_type=self.process_type_blindajes,
            estado=self.process_status,
        )
        self.process_calidad = Process.objects.create(
            user=self.user,
            process_type=self.process_type_calidad,
            estado=self.process_status,
        )
        self.process_asesoria = Process.objects.create(
            user=self.user,
            process_type=self.process_type_asesoria,
            estado=self.process_status,
        )
        self.proceso_blindajes_activo = Process.objects.create(
            user=self.user,
            process_type=self.process_type_blindajes,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )
        self.proceso_calidad_en_revision = Process.objects.create(
            user=self.user,
            process_type=self.process_type_calidad,
            estado=ProcessStatusChoices.EN_REVISION,
        )
        self.proceso_asesoria_finalizado = Process.objects.create(
            user=self.user,
            process_type=self.process_type_asesoria,
            estado=ProcessStatusChoices.FINALIZADO,
        )
        self.proceso_asesoria_activo = Process.objects.create(
            user=self.user,
            process_type=self.process_type_asesoria,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )

        # Crear un archivo PDF temporal para los reportes
        self.temp_pdf_file_content = b"dummy pdf content"
        self.temp_pdf_file_name = "test_report.pdf"

        # Crear reportes asociados a los procesos
        self.report_blindajes = Report.objects.create(
            user=self.user,
            process=self.process_blindajes,
            title="Reporte Blindajes",
            description="Descripción del reporte de blindajes",
            estado_reporte=EstadoReporteChoices.EN_GENERACION,
            pdf_file=SimpleUploadedFile(
                self.temp_pdf_file_name, self.temp_pdf_file_content
            ),
        )
        self.report_calidad = Report.objects.create(
            user=self.user,
            process=self.process_calidad,
            title="Reporte Calidad",
            description="Descripción del reporte de calidad",
            estado_reporte=EstadoReporteChoices.EN_GENERACION,
            pdf_file=SimpleUploadedFile(
                self.temp_pdf_file_name, self.temp_pdf_file_content
            ),
        )
        self.report_asesoria = Report.objects.create(
            user=self.user,
            process=self.process_asesoria,
            title="Reporte Asesoria",
            description="Descripción del reporte de asesoría",
            estado_reporte=EstadoReporteChoices.EN_GENERACION,
            pdf_file=SimpleUploadedFile(
                self.temp_pdf_file_name, self.temp_pdf_file_content
            ),
        )

        # Crear equipos asociados a los procesos del usuario
        self.equipment_blindajes = Equipment.objects.create(
            nombre="Equipo Blindajes 1",
            marca="MarcaA",
            modelo="ModeloA1",
            serial="SN001",
            user=self.user,
            process=self.process_blindajes,
            fecha_vigencia_licencia=date.today() + timedelta(days=217),
        )
        self.equipment_calidad = Equipment.objects.create(
            nombre="Equipo Calidad 1",
            marca="MarcaB",
            modelo="ModeloB1",
            serial="SN002",
            user=self.user,
            process=self.process_calidad,
            fecha_vigencia_licencia=date.today() + timedelta(days=365),
        )
        self.equipment_asesoria = Equipment.objects.create(
            nombre="Equipo Asesoría 1",
            marca="MarcaC",
            modelo="ModeloC1",
            serial="SN1003",
            user=self.user,
            process=self.process_asesoria,
            fecha_vigencia_licencia=date.today() + timedelta(days=365),
        )
        # Equipo sin proceso para probar la sección de licencias por vencer
        self.equipment_licencia_proxima = Equipment.objects.create(
            nombre="Equipo Licencia Próxima",
            marca="MarcaC",
            modelo="ModeloC1",
            serial="SN003",
            user=self.user,
            fecha_vigencia_licencia=date.today()
            + timedelta(days=30),  # Licencia vence en 30 días
        )
        self.equipment_licencia_lejana = Equipment.objects.create(
            nombre="Equipo Licencia Lejana",
            marca="MarcaD",
            modelo="ModeloD1",
            serial="SN004",
            user=self.user,
            fecha_vigencia_licencia=date.today()
            + timedelta(days=365),  # Licencia vence en 1 año
        )
        self.equipment_cc_proximo = Equipment.objects.create(
            nombre="Equipo CC Próximo",
            marca="MarcaE",
            modelo="ModeloE1",
            serial="SN-CC-001",
            user=self.user,
            fecha_vencimiento_control_calidad=date.today()
            + timedelta(days=45),  # CC vence en 45 días
        )
        self.equipment_cc_lejano = Equipment.objects.create(
            nombre="Equipo CC Lejano",
            marca="MarcaF",
            modelo="ModeloF1",
            serial="SN-CC-002",
            user=self.user,
            fecha_vencimiento_control_calidad=date.today()
            + timedelta(days=200),  # CC vence en 200 días
        )
        self.equipment_cc_sin_fecha = Equipment.objects.create(
            nombre="Equipo CC Sin Fecha Vencimiento",
            marca="MarcaG",
            modelo="ModeloG1",
            serial="SN-CC-003",
            user=self.user,
            fecha_vencimiento_control_calidad=None,  # Sin fecha de vencimiento
        )
        self.client.login(username="clientuser", password="testpassword")

    def tearDown(self):
        # Limpiar archivos PDF creados por los reportes
        for report in Report.objects.all():
            if report.pdf_file and hasattr(report.pdf_file, "path"):
                if os.path.exists(report.pdf_file.path):
                    try:
                        os.remove(report.pdf_file.path)
                    except OSError:
                        pass

    def test_dashboard_initial_state_for_client(self):
        """Verificar el estado inicial del dashboard: bienvenida, licencias y procesos activos."""
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard_cliente.html")

        self.assertIsNone(response.context["proceso_activo"])
        self.assertContains(response, "Bienvenido, Client User")

        # Verificar licencias por vencer
        equipos_vencer = response.context["equipos_licencia_por_vencer"]
        self.assertIn(self.equipment_licencia_proxima, equipos_vencer)
        self.assertNotIn(
            self.equipment_licencia_lejana, equipos_vencer
        )  # Licencia lejana
        self.assertContains(response, self.equipment_licencia_proxima.nombre)
        self.assertContains(response, "Licencias Próximas a Vencer")

        # Verificar controles de calidad por vencer
        equipos_vencer_cc = response.context.get("equipos_cc_por_vencer")
        self.assertIsNotNone(
            equipos_vencer_cc,
            "La clave 'equipos_cc_por_vencer' no está en el contexto.",
        )
        if equipos_vencer_cc is not None:  # Solo proceder si la clave existe
            self.assertIn(self.equipment_cc_proximo, equipos_vencer_cc)
            self.assertNotIn(self.equipment_cc_lejano, equipos_vencer_cc)  # CC lejano
            self.assertNotIn(
                self.equipment_cc_sin_fecha, equipos_vencer_cc
            )  # CC sin fecha
            self.assertContains(response, self.equipment_cc_proximo.nombre)
            self.assertContains(response, "Controles de Calidad Próximos a Vencer")

        # Verificar procesos activos del cliente
        procesos_activos_ctx = response.context["procesos_activos_cliente"]
        self.assertIn(self.proceso_blindajes_activo, procesos_activos_ctx)
        self.assertIn(self.proceso_calidad_en_revision, procesos_activos_ctx)
        self.assertIn(self.proceso_asesoria_activo, procesos_activos_ctx)
        self.assertNotIn(
            self.proceso_asesoria_finalizado, procesos_activos_ctx
        )  # Finalizado no debe estar
        self.assertContains(response, "Mis Procesos Activos")
        self.assertContains(
            response, self.proceso_blindajes_activo.get_process_type_display()
        )
        self.assertContains(
            response, self.proceso_calidad_en_revision.get_estado_display()
        )

    def test_dashboard_calculo_blindajes_selected(self):
        """Dashboard con 'Cálculo de Blindajes' activo: muestra equipos con botón a sus reportes."""
        url = reverse("home") + f"?proceso_activo={self.process_type_blindajes.value}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["proceso_activo"], self.process_type_blindajes.value
        )

        # Verificar sección de equipos
        self.assertIn(self.equipment_blindajes, response.context["equipos_asociados"])
        self.assertContains(response, self.equipment_blindajes.nombre)
        # Verificar botón de informes para el equipo
        expected_report_link = (
            reverse("report_list")
            + f"?equipment_id={self.equipment_blindajes.id}&process_type={self.process_type_blindajes.value}"
        )
        self.assertContains(response, f'href="{expected_report_link}"')
        self.assertContains(response, "Ver Informes")

        # Verificar que la tabla de reportes general NO está
        self.assertNotContains(response, "Reportes Asociados</h5>")
        self.assertIsNone(response.context.get("reportes_para_tabla"))

    def test_dashboard_control_calidad_selected(self):
        """Dashboard con 'Control de Calidad' activo: muestra equipos con botón a sus reportes."""
        url = reverse("home") + f"?proceso_activo={self.process_type_calidad.value}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["proceso_activo"], self.process_type_calidad.value
        )

        self.assertIn(self.equipment_calidad, response.context["equipos_asociados"])
        self.assertContains(response, self.equipment_calidad.nombre)
        expected_report_link = (
            reverse("report_list")
            + f"?equipment_id={self.equipment_calidad.id}&process_type={self.process_type_calidad.value}"
        )
        self.assertContains(response, f'href="{expected_report_link}"')

        self.assertNotContains(response, "Reportes Asociados</h5>")
        self.assertIsNone(response.context.get("reportes_para_tabla"))

    def test_dashboard_asesoria_selected(self):
        """Dashboard con 'Asesoría' activo: muestra botón a documentos asociados."""
        url = reverse("home") + f"?proceso_activo={self.process_type_asesoria.value}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["proceso_activo"], self.process_type_asesoria.value
        )

        # Aquí verificamos el botón de documentos.
        self.assertIn(
            self.equipment_asesoria, response.context["equipos_asociados"]
        )  # Si se muestran equipos
        self.assertContains(response, self.equipment_asesoria.nombre)

        # Verificar botón de "Documentos Asociados"
        expected_docs_link = (
            reverse("report_list") + f"?process_type={self.process_type_asesoria.value}"
        )
        self.assertContains(response, f'href="{expected_docs_link}"')
        self.assertContains(response, "Ver Documentos Asociados")

        # Verificar que la tabla de reportes general NO está
        self.assertNotContains(
            response, "Reportes Asociados</h5>"  # El título de la tabla de reportes
        )
        self.assertIsNone(response.context.get("reportes_para_tabla"))

    def test_dashboard_non_client_user(self):
        """Verificar que un usuario no cliente es redirigido a main.html."""
        self.client.logout()  # Desloguear cliente
        User.objects.create_user(
            username="staffuser", password="password", is_staff=True
        )
        self.client.login(username="staffuser", password="password")
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "main.html")
        self.assertNotIn("equipos_licencia_por_vencer", response.context)
        self.assertNotIn("procesos_activos_cliente", response.context)

    def test_dashboard_cc_vencido_aparece(self):
        """Verificar que un equipo cuyo CC ya venció aparece en la lista."""
        Equipment.objects.filter(id=self.equipment_cc_proximo.id).update(
            fecha_vencimiento_control_calidad=date.today()
            - timedelta(days=10)  # Venció hace 10 días
        )

        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

        equipos_vencer_cc = response.context.get("equipos_cc_por_vencer")
        self.assertIsNotNone(equipos_vencer_cc)
        if equipos_vencer_cc is not None:
            self.assertIn(self.equipment_cc_proximo, equipos_vencer_cc)
            self.assertContains(response, self.equipment_cc_proximo.nombre)

    def test_dashboard_cc_exactamente_en_6_meses_no_aparece(self):
        """Verificar que un equipo cuyo CC vence exactamente en 6 meses (o un poco más) no aparece."""
        # 6 meses * 4 semanas/mes * 7 días/semana = 168 días. Usaremos un poco más para estar seguros.
        Equipment.objects.filter(id=self.equipment_cc_proximo.id).update(
            fecha_vencimiento_control_calidad=date.today()
            + timedelta(days=180)  # Aproximadamente 6 meses
        )

        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

        equipos_vencer_cc = response.context.get("equipos_cc_por_vencer")
        self.assertIsNotNone(equipos_vencer_cc)
        if equipos_vencer_cc is not None:
            self.assertNotIn(self.equipment_cc_proximo, equipos_vencer_cc)

    def test_dashboard_no_cc_por_vencer(self):
        """Verificar que se muestra el mensaje correcto si no hay CC próximos a vencer."""
        # Eliminar o modificar los equipos para que no haya CC próximos a vencer
        Equipment.objects.filter(id=self.equipment_cc_proximo.id).update(
            fecha_vencimiento_control_calidad=date.today() + timedelta(days=300)
        )

        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard_cliente.html")

        equipos_vencer_cc = response.context.get("equipos_cc_por_vencer")
        self.assertIsNotNone(equipos_vencer_cc)
        if equipos_vencer_cc is not None:
            self.assertEqual(len(equipos_vencer_cc), 0)

        # Verificar el mensaje específico para cuando no hay CC por vencer
        # Este mensaje depende de tu plantilla, ajústalo si es necesario.
        self.assertContains(
            response,
            "¡Felicidades, no hay equipos con controles de calidad próximos a vencer!",
        )
        self.assertNotContains(
            response, self.equipment_cc_proximo.nombre
        )  # Asegurarse que no se lista

    def test_sidebar_shows_only_user_process_types(self):
        """Verifica que el sidebar solo muestre enlaces para los tipos de proceso que el usuario tiene."""
        # Por defecto, el usuario tiene procesos de Blindajes, Calidad y Asesoría.
        # Vamos a crear un tipo de proceso que el usuario NO tiene.
        Process.objects.create(
            user=self.other_user,  # Proceso de OTRO usuario
            process_type=ProcessTypeChoices.ESTUDIO_AMBIENTAL,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )

        self.client.login(username="clientuser", password="testpassword")
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

        # Verificar que los enlaces a los tipos de proceso que SÍ tiene están presentes
        self.assertContains(
            response, f'href="/?proceso_activo={self.process_type_blindajes.value}"'
        )
        self.assertContains(
            response, f'href="/?proceso_activo={self.process_type_calidad.value}"'
        )
        self.assertContains(
            response, f'href="/?proceso_activo={self.process_type_asesoria.value}"'
        )

        # Verificar que el enlace al tipo de proceso que NO tiene NO está presente
        self.assertNotContains(
            response,
            f'href="/?proceso_activo={ProcessTypeChoices.ESTUDIO_AMBIENTAL.value}"',
        )
