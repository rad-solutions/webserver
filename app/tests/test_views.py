import os
import tempfile
from datetime import date, datetime, timedelta, timezone

from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from ..models import (
    Equipment,
    EstadoEquipoChoices,
    EstadoReporteChoices,
    Process,
    ProcessStatusChoices,
    ProcessTypeChoices,
    Report,
    Role,
    RoleChoices,
    User,
)


class ReportAPITest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword",
            first_name="Test",
            last_name="User",
        )
        # Asignar rol de cliente para probar el filtrado por usuario en ReportListView
        self.role_cliente, _ = Role.objects.get_or_create(name=RoleChoices.CLIENTE)
        self.user.roles.add(self.role_cliente)

        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="adminpassword",
            first_name="Admin",
            last_name="User",
            is_staff=True,
            is_superuser=True,
        )

        self.temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        self.temp_file.write(b"contenido de prueba del PDF")
        self.temp_file.close()

        self.process_type_asesoria = ProcessTypeChoices.ASESORIA
        self.process_type_calidad = ProcessTypeChoices.CONTROL_CALIDAD
        self.process_status_progreso = ProcessStatusChoices.EN_PROGRESO

        self.process = Process.objects.create(
            user=self.user,
            process_type=ProcessTypeChoices.ASESORIA,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )

        self.process_asesoria = Process.objects.create(
            user=self.user,
            process_type=self.process_type_asesoria,
            estado=self.process_status_progreso,
            fecha_inicio=datetime(2024, 1, 10, tzinfo=timezone.utc),
        )
        self.process_calidad = Process.objects.create(
            user=self.user,
            process_type=self.process_type_calidad,
            estado=self.process_status_progreso,
            fecha_inicio=datetime(2024, 2, 15, tzinfo=timezone.utc),
        )
        # Proceso para otro usuario (admin en este caso, para probar que no se listen sus reportes para el cliente)
        self.process_admin = Process.objects.create(
            user=self.admin_user,
            process_type=self.process_type_asesoria,
            estado=self.process_status_progreso,
            fecha_inicio=datetime(2024, 3, 1, tzinfo=timezone.utc),
        )

        self.equipment1_calidad = Equipment.objects.create(
            nombre="Equipo Calidad Alpha",
            user=self.user,
            process=self.process_calidad,
            serial="EQCALPHA",
        )
        self.equipment2_asesoria = Equipment.objects.create(
            nombre="Equipo Asesoria Beta",
            user=self.user,
            process=self.process_asesoria,
            serial="EQASBETA",
        )
        self.equipment3_otro_proceso = Equipment.objects.create(
            nombre="Equipo Otro Gamma", user=self.user, serial="EQOTGAMMA"
        )

        self.temp_file_content = b"contenido de prueba del PDF"
        self.temp_file_name = "test.pdf"

        # Crear reportes con diferentes fechas de creación y tipos de proceso
        self.report1_asesoria_jan = Report.objects.create(
            user=self.user,
            process=self.process_asesoria,
            title="Reporte Asesoria Enero",
            pdf_file=SimpleUploadedFile(self.temp_file_name, self.temp_file_content),
            estado_reporte=EstadoReporteChoices.EN_GENERACION,
        )
        # Forzar created_at para pruebas de filtro de fecha precisas
        self.report1_asesoria_jan.created_at = datetime(
            2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc
        )
        self.report1_asesoria_jan.save()

        self.report2_calidad_feb = Report.objects.create(
            user=self.user,
            process=self.process_calidad,
            title="Reporte Calidad Febrero",
            pdf_file=SimpleUploadedFile(self.temp_file_name, self.temp_file_content),
            estado_reporte=EstadoReporteChoices.REVISADO,
        )
        self.report2_calidad_feb.created_at = datetime(
            2024, 2, 20, 11, 0, 0, tzinfo=timezone.utc
        )
        self.report2_calidad_feb.save()

        self.report3_asesoria_mar = Report.objects.create(
            user=self.user,
            process=self.process_asesoria,
            title="Reporte Asesoria Marzo",
            pdf_file=SimpleUploadedFile(self.temp_file_name, self.temp_file_content),
            estado_reporte=EstadoReporteChoices.APROBADO,
        )
        self.report3_asesoria_mar.created_at = datetime(
            2024, 3, 25, 12, 0, 0, tzinfo=timezone.utc
        )
        self.report3_asesoria_mar.save()

        # Reporte para el admin_user, no debería aparecer para el cliente
        self.report_admin_user = Report.objects.create(
            user=self.admin_user,
            process=self.process_admin,
            title="Reporte del Admin",
            pdf_file=SimpleUploadedFile(self.temp_file_name, self.temp_file_content),
            estado_reporte=EstadoReporteChoices.APROBADO,
        )
        self.report_admin_user.created_at = datetime(
            2024, 3, 10, 10, 0, 0, tzinfo=timezone.utc
        )
        self.report_admin_user.save()

        self.client.login(username="testuser", password="testpassword")

        # Add all necessary permissions for ReportAPITest user
        view_report_perm = Permission.objects.get(codename="view_report")
        add_report_perm = Permission.objects.get(
            codename="add_report"
        )  # Though upload_report is used in ReportCreateView
        upload_report_perm = Permission.objects.get(codename="upload_report")
        change_report_perm = Permission.objects.get(codename="change_report")
        delete_report_perm = Permission.objects.get(codename="delete_report")

        self.user.user_permissions.add(
            view_report_perm,
            add_report_perm,  # Adding for completeness, view uses upload_report
            upload_report_perm,
            change_report_perm,
            delete_report_perm,
        )

    def tearDown(self):
        self.temp_file.close()
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

        for report in Report.objects.all():
            if report.pdf_file and hasattr(report.pdf_file, "path"):
                if os.path.exists(report.pdf_file.path):
                    try:
                        os.remove(report.pdf_file.path)
                    except OSError:
                        pass

    def test_report_list_view(self):
        self.client.login(username="testuser", password="testpassword")
        with open(self.temp_file.name, "rb") as temp_file:
            Report.objects.create(
                user=self.user,
                process=self.process,
                title="Reporte en lista",
                pdf_file=SimpleUploadedFile("list.pdf", temp_file.read()),
                estado_reporte=EstadoReporteChoices.EN_GENERACION,
            )
            temp_file.seek(0)

        url = reverse("report_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/report_list.html")
        self.assertIn("reports", response.context)

    def test_report_detail_view(self):
        self.client.login(username="testuser", password="testpassword")
        with open(self.temp_file.name, "rb") as temp_file:
            report = Report.objects.create(
                user=self.user,
                process=self.process,
                title="Detalle Reporte",
                pdf_file=SimpleUploadedFile("detail.pdf", temp_file.read()),
                estado_reporte=EstadoReporteChoices.EN_GENERACION,
            )
            temp_file.seek(0)
        url = reverse("report_detail", args=[report.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/report_detail.html")
        self.assertEqual(response.context["report"], report)

    def test_report_create_view_get(self):
        self.client.login(username="testuser", password="testpassword")
        url = reverse("report_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/report_form.html")
        self.assertIn("form", response.context)

    def test_report_create_view_post_valid(self):
        self.client.login(username="testuser", password="testpassword")
        url = reverse("report_create")
        initial_count = Report.objects.count()
        with open(self.temp_file.name, "rb") as pdf:
            data = {
                "title": "Nuevo informe de prueba",
                "description": "Descripción del nuevo informe",
                "pdf_file": pdf,
                "process": self.process.id,
                "user": self.user.id,
                "estado_reporte": EstadoReporteChoices.EN_GENERACION,
                "fecha_vencimiento": date.today() + timedelta(days=30),
            }
            response = self.client.post(url, data, format="multipart")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Report.objects.count(), initial_count + 1)
        self.assertRedirects(response, reverse("report_list"))
        new_report = Report.objects.latest("created_at")
        self.assertEqual(new_report.title, "Nuevo informe de prueba")
        self.assertEqual(new_report.user, self.user)

    def test_report_create_view_post_invalid_no_title(self):
        self.client.login(username="testuser", password="testpassword")
        url = reverse("report_create")
        initial_count = Report.objects.count()
        with open(self.temp_file.name, "rb") as pdf:
            data = {
                "description": "Este informe no tiene título",
                "pdf_file": pdf,
                "process": self.process.id,
                "user": self.user.id,
                "estado_reporte": EstadoReporteChoices.EN_GENERACION,
            }
            response = self.client.post(url, data, format="multipart")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Report.objects.count(), initial_count)
        self.assertIn("form", response.context)
        self.assertTrue(response.context["form"].errors)
        form_in_context = response.context.get("form")
        self.assertIsNotNone(
            form_in_context,
            "El formulario no se encontró en el contexto de la respuesta.",
        )
        self.assertFormError(form_in_context, "title", "This field is required.")

    def test_report_create_view_post_invalid_no_pdf(self):
        self.client.login(username="testuser", password="testpassword")
        url = reverse("report_create")
        initial_count = Report.objects.count()
        data = {
            "title": "Informe sin archivo",
            "description": "Este informe no tiene archivo PDF",
            "process": self.process.id,
            "user": self.user.id,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Report.objects.count(), initial_count)
        form_in_context = response.context.get("form")
        self.assertIsNotNone(
            form_in_context,
            "El formulario no se encontró en el contexto de la respuesta.",
        )
        self.assertFormError(form_in_context, "pdf_file", "This field is required.")

    def test_report_update_view_get(self):
        self.client.login(username="testuser", password="testpassword")
        with open(self.temp_file.name, "rb") as temp_file:
            report = Report.objects.create(
                user=self.user,
                process=self.process,
                title="Para Actualizar GET",
                pdf_file=SimpleUploadedFile("update_get.pdf", temp_file.read()),
            )
            temp_file.seek(0)
        url = reverse("report_update", args=[report.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/report_form.html")
        self.assertEqual(response.context["form"].instance, report)

    def test_report_update_view_post_valid(self):
        self.client.login(username="testuser", password="testpassword")
        with open(self.temp_file.name, "rb") as temp_file:
            report = Report.objects.create(
                user=self.user,
                process=self.process,
                title="Informe para actualizar",
                description="Descripción original",
                pdf_file=SimpleUploadedFile("update_me.pdf", temp_file.read()),
                estado_reporte=EstadoReporteChoices.EN_GENERACION,
            )
            temp_file.seek(0)

        url = reverse("report_update", args=[report.id])
        updated_title = "Título actualizado"
        updated_description = "Descripción actualizada"
        updated_estado = EstadoReporteChoices.REVISADO

        # Para actualizar un FileField, necesitas pasar un nuevo archivo.
        # Si no se pasa, el archivo existente se mantiene.
        # Si quieres probar la actualización del archivo, crea otro archivo temporal.
        with open(self.temp_file.name, "rb") as pdf_update:
            data = {
                "title": updated_title,
                "description": updated_description,
                "process": self.process.id,
                "user": self.user.id,
                "estado_reporte": updated_estado,
                "pdf_file": pdf_update,
            }
            response = self.client.post(url, data, format="multipart")

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("report_list"))

        report.refresh_from_db()
        self.assertEqual(report.title, updated_title)
        self.assertEqual(report.description, updated_description)
        self.assertEqual(report.estado_reporte, updated_estado)

    def test_report_delete_view_get(self):
        self.client.login(username="testuser", password="testpassword")
        with open(self.temp_file.name, "rb") as temp_file:
            report = Report.objects.create(
                user=self.user,
                process=self.process,
                title="Para Eliminar GET",
                pdf_file=SimpleUploadedFile("delete_get.pdf", temp_file.read()),
            )
            temp_file.seek(0)
        url = reverse("report_delete", args=[report.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/report_confirm_delete.html")
        self.assertEqual(response.context["report"], report)

    def test_report_delete_view_post(self):
        self.client.login(username="testuser", password="testpassword")
        with open(self.temp_file.name, "rb") as temp_file:
            report = Report.objects.create(
                user=self.user,
                process=self.process,
                title="Informe para eliminar",
                description="Este informe será eliminado",
                pdf_file=SimpleUploadedFile("delete_me.pdf", temp_file.read()),
            )
            temp_file.seek(0)
        initial_count = Report.objects.count()

        url = reverse("report_delete", args=[report.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("report_list"))
        self.assertEqual(Report.objects.count(), initial_count - 1)
        with self.assertRaises(Report.DoesNotExist):
            Report.objects.get(id=report.id)

    def test_report_list_view_no_filters_client_user(self):
        """Test ReportListView sin filtros para un usuario cliente."""
        self.client.login(username="testuser", password="testpassword")
        url = reverse("report_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/report_list.html")
        reports_in_context = response.context["reports"]
        self.assertEqual(len(reports_in_context), 3)  # Solo los del self.user
        self.assertIn(self.report1_asesoria_jan, reports_in_context)
        self.assertIn(self.report2_calidad_feb, reports_in_context)
        self.assertIn(self.report3_asesoria_mar, reports_in_context)
        self.assertNotIn(
            self.report_admin_user, reports_in_context
        )  # No debe mostrar el del admin
        self.assertEqual(response.context["selected_process_type"], "todos")
        self.assertEqual(response.context["start_date"], "")
        self.assertEqual(response.context["end_date"], "")

    def test_report_list_view_no_filters_admin_user(self):
        """Test ReportListView sin filtros para un usuario admin (debería ver todos)."""
        self.client.login(username="adminuser", password="adminpassword")
        url = reverse("report_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        reports_in_context = response.context["reports"]
        self.assertEqual(len(reports_in_context), 4)  # Todos los reportes
        self.assertIn(self.report1_asesoria_jan, reports_in_context)
        self.assertIn(self.report_admin_user, reports_in_context)

    def test_report_list_view_filter_by_process_type(self):
        """Test ReportListView filtrando por tipo de proceso."""
        self.client.login(username="testuser", password="testpassword")
        url = reverse("report_list") + f"?process_type={self.process_type_asesoria}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        reports_in_context = response.context["reports"]
        self.assertEqual(len(reports_in_context), 2)
        self.assertIn(self.report1_asesoria_jan, reports_in_context)
        self.assertIn(self.report3_asesoria_mar, reports_in_context)
        self.assertNotIn(self.report2_calidad_feb, reports_in_context)
        self.assertEqual(
            response.context["selected_process_type"], self.process_type_asesoria
        )

    def test_report_list_view_filter_by_start_date(self):
        """Test ReportListView filtrando por fecha de inicio."""
        self.client.login(username="testuser", password="testpassword")
        # Filtra reportes creados desde el 1 de Febrero de 2024
        start_date_filter = "2024-02-01"
        url = reverse("report_list") + f"?start_date={start_date_filter}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        reports_in_context = response.context["reports"]
        self.assertEqual(
            len(reports_in_context), 2
        )  # report2_calidad_feb y report3_asesoria_mar
        self.assertIn(self.report2_calidad_feb, reports_in_context)
        self.assertIn(self.report3_asesoria_mar, reports_in_context)
        self.assertNotIn(self.report1_asesoria_jan, reports_in_context)
        self.assertEqual(response.context["start_date"], start_date_filter)

    def test_report_list_view_filter_by_end_date(self):
        """Test ReportListView filtrando por fecha de fin."""
        self.client.login(username="testuser", password="testpassword")
        # Filtra reportes creados hasta el 28 de Febrero de 2024
        end_date_filter = "2024-02-28"
        url = reverse("report_list") + f"?end_date={end_date_filter}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        reports_in_context = response.context["reports"]
        self.assertEqual(
            len(reports_in_context), 2
        )  # report1_asesoria_jan y report2_calidad_feb
        self.assertIn(self.report1_asesoria_jan, reports_in_context)
        self.assertIn(self.report2_calidad_feb, reports_in_context)
        self.assertNotIn(self.report3_asesoria_mar, reports_in_context)
        self.assertEqual(response.context["end_date"], end_date_filter)

    def test_report_list_view_filter_by_date_range(self):
        """Test ReportListView filtrando por rango de fechas."""
        self.client.login(username="testuser", password="testpassword")
        start_date_filter = "2024-02-01"
        end_date_filter = "2024-02-29"  # Incluye todo Febrero
        url = (
            reverse("report_list")
            + f"?start_date={start_date_filter}&end_date={end_date_filter}"
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        reports_in_context = response.context["reports"]
        self.assertEqual(len(reports_in_context), 1)  # Solo report2_calidad_feb
        self.assertIn(self.report2_calidad_feb, reports_in_context)
        self.assertNotIn(self.report1_asesoria_jan, reports_in_context)
        self.assertNotIn(self.report3_asesoria_mar, reports_in_context)
        self.assertEqual(response.context["start_date"], start_date_filter)
        self.assertEqual(response.context["end_date"], end_date_filter)

    def test_report_list_view_filter_by_process_type_and_date_range(self):
        """Test ReportListView filtrando por tipo de proceso y rango de fechas."""
        self.client.login(username="testuser", password="testpassword")
        process_type_filter = self.process_type_asesoria
        start_date_filter = "2024-01-01"
        end_date_filter = "2024-01-31"  # Solo Enero
        url = (
            reverse("report_list")
            + f"?process_type={process_type_filter}&start_date={start_date_filter}&end_date={end_date_filter}"
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        reports_in_context = response.context["reports"]
        self.assertEqual(len(reports_in_context), 1)  # Solo report1_asesoria_jan
        self.assertIn(self.report1_asesoria_jan, reports_in_context)
        self.assertNotIn(self.report2_calidad_feb, reports_in_context)
        self.assertNotIn(self.report3_asesoria_mar, reports_in_context)
        self.assertEqual(response.context["selected_process_type"], process_type_filter)
        self.assertEqual(response.context["start_date"], start_date_filter)
        self.assertEqual(response.context["end_date"], end_date_filter)

    def test_report_list_view_filter_no_results(self):
        """Test ReportListView con filtros que no devuelven resultados."""
        self.client.login(username="testuser", password="testpassword")
        start_date_filter = "2025-01-01"  # Fecha futura sin reportes
        url = reverse("report_list") + f"?start_date={start_date_filter}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        reports_in_context = response.context["reports"]
        self.assertEqual(len(reports_in_context), 0)
        self.assertEqual(response.context["start_date"], start_date_filter)

    def test_report_list_view_filter_by_equipment_id(self):
        """Test ReportListView filtrando por ID de equipo."""
        self.client.login(username="testuser", password="testpassword")
        # Filtrar por equipment1_calidad (asociado a process_calidad, que tiene report2_calidad_feb)
        url = reverse("report_list") + f"?equipment_id={self.equipment1_calidad.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        reports_in_context = response.context["reports"]
        self.assertEqual(len(reports_in_context), 1)
        self.assertIn(self.report2_calidad_feb, reports_in_context)
        self.assertNotIn(self.report1_asesoria_jan, reports_in_context)
        self.assertNotIn(self.report3_asesoria_mar, reports_in_context)
        self.assertEqual(
            str(response.context["selected_equipment_id"]),
            str(self.equipment1_calidad.id),
        )
        self.assertEqual(
            response.context["filtered_equipment"], self.equipment1_calidad
        )

    def test_report_list_view_filter_by_equipment_id_and_process_type(self):
        """Test ReportListView filtrando por ID de equipo y tipo de proceso."""
        self.client.login(username="testuser", password="testpassword")
        # Filtrar por equipment1_calidad Y process_type=control_calidad
        url = (
            reverse("report_list")
            + f"?equipment_id={self.equipment1_calidad.id}&process_type={self.process_type_calidad}"
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        reports_in_context = response.context["reports"]
        self.assertEqual(len(reports_in_context), 1)
        self.assertIn(self.report2_calidad_feb, reports_in_context)
        self.assertEqual(
            str(response.context["selected_equipment_id"]),
            str(self.equipment1_calidad.id),
        )
        self.assertEqual(
            response.context["selected_process_type"], self.process_type_calidad
        )

    def test_report_list_view_filter_by_equipment_id_wrong_process_type(self):
        """Test ReportListView con ID de equipo y un tipo de proceso que no coincide."""
        self.client.login(username="testuser", password="testpassword")
        # Filtrar por equipment1_calidad (cuyo proceso es 'control_calidad') pero pedir 'asesoria'
        url = (
            reverse("report_list")
            + f"?equipment_id={self.equipment1_calidad.id}&process_type={self.process_type_asesoria}"
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        reports_in_context = response.context["reports"]
        self.assertEqual(len(reports_in_context), 0)  # No debería haber resultados
        self.assertEqual(
            str(response.context["selected_equipment_id"]),
            str(self.equipment1_calidad.id),
        )
        self.assertEqual(
            response.context["selected_process_type"], self.process_type_asesoria
        )

    def test_report_list_view_filter_by_non_existent_equipment_id(self):
        """Test ReportListView con un ID de equipo que no existe."""
        self.client.login(username="testuser", password="testpassword")
        non_existent_equipment_id = 99999
        url = reverse("report_list") + f"?equipment_id={non_existent_equipment_id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        reports_in_context = response.context["reports"]
        self.assertEqual(len(reports_in_context), 0)
        self.assertEqual(
            str(response.context["selected_equipment_id"]),
            str(non_existent_equipment_id),
        )
        self.assertNotIn(
            "filtered_equipment", response.context
        )  # No debería encontrar el equipo


class AuthenticationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword",
            first_name="Test",
            last_name="User",
        )

    def test_login_successful(self):
        url = reverse("login")
        data = {
            "username": "testuser",
            "password": "testpassword",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Successful login redirects
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_invalid_username(self):
        url = reverse("login")
        data = {
            "username": "nonexistentuser",
            "password": "testpassword",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)  # Re-renders login form
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_login_invalid_password(self):
        url = reverse("login")
        data = {
            "username": "testuser",
            "password": "wrongpassword",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)  # Re-renders login form
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logout(self):
        self.client.login(username="testuser", password="testpassword")
        self.assertTrue(self.client.session.get("_auth_user_id") is not None)

        url = reverse("logout")
        response = self.client.get(url)  # Logout is usually a GET request
        self.assertEqual(response.status_code, 302)  # Redirects after logout
        self.assertIsNone(self.client.session.get("_auth_user_id"))


class ProtectedResourceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword",
            first_name="Test",
            last_name="User",
        )

        self.other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="otherpassword",
            first_name="Other",
            last_name="User",
        )

        self.process_for_urls = Process.objects.create(
            user=self.user,
            process_type=ProcessTypeChoices.OTRO,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )
        self.equipment_for_urls = Equipment.objects.create(
            nombre="Equipo Test URL", user=self.user, process=self.process_for_urls
        )
        # Crear un archivo temporal para el reporte
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        self.temp_file.write(b"dummy content")
        self.temp_file.seek(0)
        self.report_for_urls = Report.objects.create(
            user=self.user,
            process=self.process_for_urls,
            title="Reporte Test URL",
            pdf_file=SimpleUploadedFile("url_test.pdf", self.temp_file.read()),
        )

    def tearDown(self):
        self.temp_file.close()
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
        if self.report_for_urls.pdf_file and hasattr(
            self.report_for_urls.pdf_file, "path"
        ):
            if os.path.exists(self.report_for_urls.pdf_file.path):
                try:
                    os.remove(self.report_for_urls.pdf_file.path)
                except OSError:
                    pass

    def test_unauthenticated_access(self):
        """Test que los usuarios no autenticados son redirigidos al inicio de sesión"""
        urls_to_test = {
            "report_list": reverse("report_list"),
            "report_create": reverse("report_create"),
            "report_detail": reverse("report_detail", args=[self.report_for_urls.id]),
            "report_update": reverse("report_update", args=[self.report_for_urls.id]),
            "report_delete": reverse("report_delete", args=[self.report_for_urls.id]),
            "equipos_list": reverse("equipos_list"),
            "equipos_create": reverse("equipos_create"),
            "equipos_detail": reverse(
                "equipos_detail", args=[self.equipment_for_urls.id]
            ),
            "equipos_update": reverse(
                "equipos_update", args=[self.equipment_for_urls.id]
            ),
            "equipos_delete": reverse(
                "equipos_delete", args=[self.equipment_for_urls.id]
            ),
            "process_list": reverse("process_list"),
            "process_create": reverse("process_create"),
            "process_detail": reverse(
                "process_detail", args=[self.process_for_urls.id]
            ),
            "process_update": reverse(
                "process_update", args=[self.process_for_urls.id]
            ),
            "process_delete": reverse(
                "process_delete", args=[self.process_for_urls.id]
            ),
            "user_list": reverse("user_list"),
            "user_create": reverse("user_create"),
            # Añadir user_detail, user_update, user_delete si es necesario
        }

        for name, url in urls_to_test.items():
            with self.subTest(url_name=name):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 403, f"Failed for GET {url}")
                # self.assertTrue(
                #     response.url.startswith("/login/"), f"Failed for GET {url}"
                # )

                # Para vistas create, update, delete, también probar POST si es relevante
                # (aunque DeleteView y UpdateView suelen requerir GET primero para la confirmación/formulario)
                if "create" in name or "update" in name or "delete" in name:
                    response_post = self.client.post(url, {})
                    self.assertEqual(
                        response_post.status_code, 403, f"Failed for POST {url}"
                    )
                    # self.assertTrue(
                    #     response_post.url.startswith("/login/"),
                    #     f"Failed for POST {url}",
                    # )


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
            response, "Reportes Asociados</h5>"
        )  # El título de la tabla de reportes
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


class ProcessAPITest(TestCase):
    def setUp(self):
        self.user_cliente, _ = Role.objects.get_or_create(name=RoleChoices.CLIENTE)
        self.user = User.objects.create_user(username="procuser", password="password")
        self.user.roles.add(self.user_cliente)

        self.admin_user = User.objects.create_user(
            username="admin_proc", password="password", is_staff=True
        )
        self.other_user = User.objects.create_user(
            username="otherprocuser", password="password"
        )
        # Procesos con fechas variadas
        self.proc1 = Process.objects.create(
            user=self.user,
            process_type=ProcessTypeChoices.ASESORIA,
            estado=ProcessStatusChoices.EN_PROGRESO,
            # fecha_inicio se setea automáticamente por auto_now_add
        )
        # Forzar fechas para testing preciso
        self.proc1.fecha_inicio = datetime(2023, 3, 10, tzinfo=timezone.utc)
        self.proc1.fecha_final = datetime(2023, 9, 15, tzinfo=timezone.utc)
        self.proc1.save()

        self.proc2 = Process.objects.create(
            user=self.user,
            process_type=ProcessTypeChoices.CONTROL_CALIDAD,
            estado=ProcessStatusChoices.FINALIZADO,
        )
        self.proc2.fecha_inicio = datetime(2023, 8, 5, tzinfo=timezone.utc)
        self.proc2.fecha_final = datetime(2024, 1, 20, tzinfo=timezone.utc)
        self.proc2.save()

        self.proc3_admin = Process.objects.create(  # Proceso de otro usuario
            user=self.admin_user,
            process_type=ProcessTypeChoices.CALCULO_BLINDAJES,
            estado=ProcessStatusChoices.EN_REVISION,
        )
        self.proc3_admin.fecha_inicio = datetime(2024, 2, 1, tzinfo=timezone.utc)
        self.proc3_admin.save()

        self.proc4_no_final = Process.objects.create(  # Sin fecha final
            user=self.user,
            process_type=ProcessTypeChoices.OTRO,
            estado=ProcessStatusChoices.RADICADO,
        )
        self.proc4_no_final.fecha_inicio = datetime(2024, 3, 1, tzinfo=timezone.utc)
        self.proc4_no_final.save()

        # Equipos asociados a estos procesos (ya que la vista lista equipos)
        self.eq_p1 = Equipment.objects.create(
            nombre="Equipo P1", user=self.user, process=self.proc1
        )
        self.eq_p2 = Equipment.objects.create(
            nombre="Equipo P2", user=self.user, process=self.proc2
        )
        self.eq_p3_admin = Equipment.objects.create(
            nombre="Equipo P3 Admin", user=self.admin_user, process=self.proc3_admin
        )
        self.eq_p4 = Equipment.objects.create(
            nombre="Equipo P4", user=self.user, process=self.proc4_no_final
        )

        self.client.login(username="procuser", password="password")
        self.url = reverse("process_list")

    def test_process_list_view(self):
        Process.objects.create(
            user=self.user,
            process_type=ProcessTypeChoices.ASESORIA,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )
        url = reverse("process_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "process/process_list.html")
        self.assertIn("equipos", response.context)

    def test_process_detail_view(self):
        process = Process.objects.create(
            user=self.user,
            process_type=ProcessTypeChoices.CONTROL_CALIDAD,
            estado=ProcessStatusChoices.RADICADO,
        )
        url = reverse("process_detail", args=[process.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "process/process_detail.html")
        self.assertEqual(response.context["process"], process)

    def test_process_create_view_get(self):
        url = reverse("process_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "process/process_form.html")

    def test_process_create_view_post_valid(self):
        url = reverse("process_create")
        initial_count = Process.objects.count()
        data = {
            "user": self.user.id,
            "process_type": ProcessTypeChoices.CALCULO_BLINDAJES,
            "estado": ProcessStatusChoices.EN_PROGRESO,
            "fecha_final": (date.today() + timedelta(days=10)).strftime(
                "%Y-%m-%dT%H:%M"
            ),
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Process.objects.count(), initial_count + 1)
        new_process = Process.objects.latest("fecha_inicio")
        self.assertEqual(new_process.user, self.user)
        self.assertEqual(new_process.process_type, ProcessTypeChoices.CALCULO_BLINDAJES)

    def test_process_create_view_post_invalid(self):
        url = reverse("process_create")
        initial_count = Process.objects.count()
        data = {"user": self.user.id, "estado": "estado_invalido"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Process.objects.count(), initial_count)
        self.assertTrue(response.context["form"].errors)

    def test_process_update_view_get(self):
        process = Process.objects.create(
            user=self.user,
            process_type=ProcessTypeChoices.ASESORIA,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )
        url = reverse("process_update", args=[process.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "process/process_form.html")
        self.assertEqual(response.context["form"].instance, process)

    def test_process_update_view_post_valid(self):
        process = Process.objects.create(
            user=self.user,
            process_type=ProcessTypeChoices.ASESORIA,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )
        url = reverse("process_update", args=[process.id])
        data = {
            "user": self.user.id,
            "process_type": ProcessTypeChoices.CONTROL_CALIDAD,
            "estado": ProcessStatusChoices.FINALIZADO,
            "fecha_final": date.today().strftime("%Y-%m-%dT%H:%M"),
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        process.refresh_from_db()
        self.assertEqual(process.process_type, ProcessTypeChoices.CONTROL_CALIDAD)
        self.assertEqual(process.estado, ProcessStatusChoices.FINALIZADO)

    def test_process_delete_view_get(self):
        process = Process.objects.create(
            user=self.user,
            process_type=ProcessTypeChoices.OTRO,
            estado=ProcessStatusChoices.RADICADO,
        )
        url = reverse("process_delete", args=[process.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "process/process_confirm_delete.html")

    def test_process_delete_view_post(self):
        process = Process.objects.create(
            user=self.user,
            process_type=ProcessTypeChoices.OTRO,
            estado=ProcessStatusChoices.RADICADO,
        )
        initial_count = Process.objects.count()
        url = reverse("process_delete", args=[process.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Process.objects.count(), initial_count - 1)

    def test_process_list_filter_by_fecha_inicio_range(self):
        """Testea el filtro por rango de fecha de inicio del proceso."""
        # Filtro para procesos iniciados en Agosto 2023
        response = self.client.get(
            self.url,
            {"inicio_start_date": "2023-08-01", "inicio_end_date": "2023-08-31"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "process/process_list.html")
        equipos_en_contexto = response.context["equipos"]  # La vista devuelve 'equipos'
        self.assertEqual(len(equipos_en_contexto), 1)
        self.assertIn(
            self.eq_p2, equipos_en_contexto
        )  # Proceso eq_p2 inició 2023-08-05
        self.assertNotIn(
            self.eq_p1, equipos_en_contexto
        )  # Proceso eq_p1 inició 2023-03-10
        self.assertEqual(response.context["inicio_start_date"], "2023-08-01")
        self.assertEqual(response.context["inicio_end_date"], "2023-08-31")

    def test_process_list_filter_by_fecha_final_desde(self):
        """Testea el filtro por fecha de finalización del proceso (desde)."""
        # Filtro para procesos finalizados desde Enero 2024
        response = self.client.get(self.url, {"fin_start_date": "2024-01-01"})
        self.assertEqual(response.status_code, 200)
        equipos_en_contexto = response.context["equipos"]
        self.assertEqual(len(equipos_en_contexto), 1)
        self.assertIn(
            self.eq_p2, equipos_en_contexto
        )  # Proceso eq_p2 finalizó 2024-01-20
        self.assertNotIn(
            self.eq_p1, equipos_en_contexto
        )  # Proceso eq_p1 finalizó 2023-09-15
        self.assertNotIn(
            self.eq_p4, equipos_en_contexto
        )  # Proceso eq_p4 no ha finalizado
        self.assertEqual(response.context["fin_start_date"], "2024-01-01")

    def test_process_list_filter_by_fecha_final_exact_date(self):
        """Testea el filtro por fecha de finalización del proceso (exacta)."""
        response = self.client.get(
            self.url, {"fin_start_date": "2023-09-15", "fin_end_date": "2023-09-15"}
        )
        self.assertEqual(response.status_code, 200)
        equipos_en_contexto = response.context["equipos"]
        self.assertEqual(len(equipos_en_contexto), 1)
        self.assertIn(self.eq_p1, equipos_en_contexto)
        self.assertEqual(response.context["fin_start_date"], "2023-09-15")
        self.assertEqual(response.context["fin_end_date"], "2023-09-15")

    def test_process_list_filter_combined_type_and_fecha_inicio(self):
        """Testea combinación de filtro de tipo de proceso y fecha de inicio."""
        response = self.client.get(
            self.url,
            {
                "process_type": ProcessTypeChoices.ASESORIA,
                "inicio_start_date": "2023-03-01",
                "inicio_end_date": "2023-03-31",
            },
        )
        self.assertEqual(response.status_code, 200)
        equipos_en_contexto = response.context["equipos"]
        self.assertEqual(len(equipos_en_contexto), 1)
        self.assertIn(
            self.eq_p1, equipos_en_contexto
        )  # Proceso Asesoría, inició 2023-03-10
        self.assertNotIn(self.eq_p2, equipos_en_contexto)
        self.assertEqual(
            response.context["selected_process_type"], ProcessTypeChoices.ASESORIA
        )
        self.assertEqual(response.context["inicio_start_date"], "2023-03-01")

    def test_process_list_filter_no_results_for_final_date(self):
        """Testea filtros de fecha final que no devuelven resultados."""
        response = self.client.get(self.url, {"fin_start_date": "2099-01-01"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["equipos"]), 0)
        self.assertEqual(response.context["fin_start_date"], "2099-01-01")

    def test_process_list_admin_sees_all_relevant_equipments(self):
        """Testea que un admin vea equipos cuyos procesos cumplen el filtro (si la lógica lo permite)."""
        self.client.logout()
        self.client.login(username="admin_proc", password="password")
        # Filtro para procesos iniciados en Febrero 2024 (debería encontrar proc3_admin)
        response = self.client.get(
            self.url,
            {"inicio_start_date": "2024-02-01", "inicio_end_date": "2024-02-29"},
        )
        self.assertEqual(response.status_code, 200)
        equipos_en_contexto = response.context["equipos"]
        # La vista actual filtra por usuario si es cliente, sino muestra todos los equipos
        # y luego aplica los filtros de fecha del proceso.
        self.assertEqual(len(equipos_en_contexto), 1)
        self.assertIn(self.eq_p3_admin, equipos_en_contexto)


class EquipmentAPITest(TestCase):
    def setUp(self):
        self.user_client = User.objects.create_user(
            username="equipclient",
            password="password",
            first_name="Equip",
            last_name="Client",
        )
        self.admin_user = User.objects.create_user(
            username="equipadmin", password="password", is_staff=True
        )
        self.process = Process.objects.create(
            user=self.user_client,
            process_type=ProcessTypeChoices.ASESORIA,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )
        self.process_calidad = Process.objects.create(
            user=self.user_client, process_type=ProcessTypeChoices.CONTROL_CALIDAD
        )
        self.process_blindajes = Process.objects.create(
            user=self.user_client, process_type=ProcessTypeChoices.CALCULO_BLINDAJES
        )
        # Equipos con fechas variadas
        self.eq1 = Equipment.objects.create(
            nombre="Equipo Alfa",
            user=self.user_client,
            process=self.process_calidad,
            fecha_adquisicion=date(2023, 1, 15),
            fecha_vigencia_licencia=date(2025, 6, 30),
            fecha_ultimo_control_calidad=date(2024, 1, 10),
            fecha_vencimiento_control_calidad=date(2025, 1, 10),
        )
        self.eq2 = Equipment.objects.create(
            nombre="Equipo Beta",
            user=self.user_client,
            process=self.process_blindajes,
            fecha_adquisicion=date(2023, 7, 20),
            fecha_vigencia_licencia=date(2026, 1, 15),
            fecha_ultimo_control_calidad=date(2024, 7, 5),
            fecha_vencimiento_control_calidad=date(2025, 7, 5),
        )
        self.eq3 = Equipment.objects.create(
            nombre="Equipo Gamma (Admin)",
            user=self.admin_user,  # Para probar filtro de usuario
            fecha_adquisicion=date(2024, 1, 1),
            fecha_vigencia_licencia=date(2025, 12, 1),
            fecha_ultimo_control_calidad=date(2024, 6, 1),
            fecha_vencimiento_control_calidad=date(2025, 6, 1),
        )
        self.eq4_no_dates = Equipment.objects.create(
            nombre="Equipo Delta Sin Fechas",
            user=self.user_client,
            process=self.process_calidad,
        )
        self.client.login(username="equipadmin", password="password")
        self.url = reverse("equipos_list")

    def test_equipment_list_view(self):
        Equipment.objects.create(
            nombre="Equipo en Lista", user=self.user_client, process=self.process
        )
        url = reverse("equipos_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "equipos/equipos_list.html")
        self.assertIn("equipos", response.context)

    def test_equipment_detail_view(self):
        equipment = Equipment.objects.create(
            nombre="Detalle Equipo", user=self.user_client, process=self.process
        )
        url = reverse("equipos_detail", args=[equipment.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "equipos/equipos_detail.html")
        self.assertEqual(response.context["equipo"], equipment)

    def test_equipment_create_view_get(self):
        url = reverse("equipos_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "equipos/equipos_form.html")

    def test_equipment_create_view_post_valid(self):
        url = reverse("equipos_create")
        initial_count = Equipment.objects.count()
        data = {
            "nombre": "Nuevo Equipo Gamma",
            "marca": "MarcaTest",
            "modelo": "ModeloTest",
            "serial": "SNTEST123",
            "user": self.user_client.id,
            "process": self.process.id,
            "estado_actual": EstadoEquipoChoices.EN_USO,
            "sede": "Sede Test",
            "fecha_adquisicion": date.today().strftime("%Y-%m-%d"),
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302, response.content.decode())
        self.assertEqual(Equipment.objects.count(), initial_count + 1)
        new_equipment = Equipment.objects.latest("id")
        self.assertEqual(new_equipment.nombre, "Nuevo Equipo Gamma")
        self.assertEqual(new_equipment.user, self.user_client)

    def test_equipment_create_view_post_invalid(self):
        url = reverse("equipos_create")
        initial_count = Equipment.objects.count()
        data = {"marca": "SoloMarca"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Equipment.objects.count(), initial_count)
        self.assertTrue(response.context["form"].errors)

    def test_equipment_update_view_get(self):
        equipment = Equipment.objects.create(
            nombre="Equipo para GET Update", user=self.user_client, process=self.process
        )
        url = reverse("equipos_update", args=[equipment.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "equipos/equipos_form.html")
        self.assertEqual(response.context["form"].instance, equipment)

    def test_equipment_update_view_post_valid(self):
        equipment = Equipment.objects.create(
            nombre="Equipo Original",
            serial="SNORIG",
            user=self.user_client,
            process=self.process,
        )
        url = reverse("equipos_update", args=[equipment.id])
        data = {
            "nombre": "Equipo Actualizado",
            "marca": equipment.marca or "NuevaMarca",
            "modelo": equipment.modelo or "NuevoModelo",
            "serial": "SNUPDT",
            "user": self.user_client.id,
            "process": self.process.id,
            "estado_actual": EstadoEquipoChoices.DADO_DE_BAJA,
            "sede": equipment.sede or "NuevaSede",
            "fecha_adquisicion": (equipment.fecha_adquisicion or date.today()).strftime(
                "%Y-%m-%d"
            ),
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        equipment.refresh_from_db()
        self.assertEqual(equipment.nombre, "Equipo Actualizado")
        self.assertEqual(equipment.serial, "SNUPDT")
        self.assertEqual(equipment.estado_actual, EstadoEquipoChoices.DADO_DE_BAJA)

    def test_equipment_delete_view_get(self):
        equipment = Equipment.objects.create(
            nombre="Equipo para GET Delete", user=self.user_client, process=self.process
        )
        url = reverse("equipos_delete", args=[equipment.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "equipos/equipos_confirm_delete.html")

    def test_equipment_delete_view_post(self):
        equipment = Equipment.objects.create(
            nombre="Equipo para POST Delete",
            user=self.user_client,
            process=self.process,
        )
        initial_count = Equipment.objects.count()
        url = reverse("equipos_delete", args=[equipment.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Equipment.objects.count(), initial_count - 1)

    def test_equipos_list_filter_by_fecha_adquisicion_range(self):
        """Testea el filtro por rango de fecha de adquisición."""
        response = self.client.get(
            self.url, {"inicio_adq_date": "2023-07-01", "end_adq_date": "2023-12-31"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "equipos/equipos_list.html")
        equipos_en_contexto = response.context["equipos"]
        self.assertEqual(len(equipos_en_contexto), 1)
        self.assertIn(self.eq2, equipos_en_contexto)
        self.assertNotIn(self.eq1, equipos_en_contexto)
        self.assertEqual(response.context["inicio_adq_date"], "2023-07-01")
        self.assertEqual(response.context["end_adq_date"], "2023-12-31")

    def test_equipos_list_filter_by_fecha_vigencia_licencia_desde(self):
        """Testea el filtro por fecha de vigencia de licencia (desde)."""
        response = self.client.get(self.url, {"inicio_vig_lic_date": "2026-01-01"})
        self.assertEqual(response.status_code, 200)
        equipos_en_contexto = response.context["equipos"]
        self.assertEqual(len(equipos_en_contexto), 1)
        self.assertIn(self.eq2, equipos_en_contexto)  # Licencia 2026-01-15
        self.assertNotIn(self.eq1, equipos_en_contexto)  # Licencia 2025-06-30
        self.assertEqual(response.context["inicio_vig_lic_date"], "2026-01-01")

    def test_equipos_list_filter_by_fecha_ultimo_control_calidad_hasta(self):
        """Testea el filtro por fecha de último control de calidad (hasta)."""
        response = self.client.get(self.url, {"end_last_cc_date": "2024-06-30"})
        self.assertEqual(response.status_code, 200)
        equipos_en_contexto = response.context["equipos"]
        self.assertEqual(len(equipos_en_contexto), 2)
        self.assertIn(self.eq1, equipos_en_contexto)  # Ultimo CC 2024-01-10
        self.assertIn(self.eq3, equipos_en_contexto)  # Ultimo CC 2024-06-01
        self.assertNotIn(self.eq2, equipos_en_contexto)  # Ultimo CC 2024-07-05
        self.assertEqual(response.context["end_last_cc_date"], "2024-06-30")

    def test_equipos_list_filter_by_fecha_vencimiento_control_calidad_range(self):
        """Testea el filtro por rango de fecha de vencimiento de control de calidad."""
        response = self.client.get(
            self.url,
            {"inicio_venc_cc_date": "2025-01-01", "end_venc_cc_date": "2025-06-30"},
        )
        self.assertEqual(response.status_code, 200)
        equipos_en_contexto = response.context["equipos"]
        self.assertEqual(len(equipos_en_contexto), 2)
        self.assertIn(self.eq1, equipos_en_contexto)  # Vence CC 2025-01-10
        self.assertIn(self.eq3, equipos_en_contexto)  # Vence CC 2025-06-01
        self.assertNotIn(self.eq2, equipos_en_contexto)  # Vence CC 2025-07-05
        self.assertEqual(response.context["inicio_venc_cc_date"], "2025-01-01")
        self.assertEqual(response.context["end_venc_cc_date"], "2025-06-30")

    def test_equipos_list_filter_combined_process_type_and_adq_date(self):
        """Testea combinación de filtro de tipo de proceso y fecha de adquisición."""
        response = self.client.get(
            self.url,
            {
                "process_type": ProcessTypeChoices.CONTROL_CALIDAD,
                "inicio_adq_date": "2023-01-01",
                "end_adq_date": "2023-12-31",
            },
        )
        self.assertEqual(response.status_code, 200)
        equipos_en_contexto = response.context["equipos"]
        self.assertEqual(len(equipos_en_contexto), 1)
        self.assertIn(self.eq1, equipos_en_contexto)  # Proceso Calidad, Adq 2023-01-15
        self.assertNotIn(self.eq2, equipos_en_contexto)  # Proceso Blindajes
        self.assertEqual(
            response.context["selected_process_type"],
            ProcessTypeChoices.CONTROL_CALIDAD,
        )
        self.assertEqual(response.context["inicio_adq_date"], "2023-01-01")

    def test_equipos_list_filter_no_results(self):
        """Testea filtros que no devuelven resultados."""
        response = self.client.get(self.url, {"inicio_adq_date": "2099-01-01"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["equipos"]), 0)
        self.assertEqual(response.context["inicio_adq_date"], "2099-01-01")

    def test_equipos_list_admin_sees_all_without_date_filters(self):
        """Testea que un admin vea todos los equipos si no hay filtros de fecha (solo para verificar el setup)."""
        self.client.logout()
        self.client.login(username="equipadmin", password="password")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        # Esperamos 4 equipos: eq1, eq2, eq3 (admin), eq4_no_dates
        # La vista actual filtra por usuario si es cliente, sino muestra todos.
        self.assertEqual(len(response.context["equipos"]), 4)
        self.assertIn(self.eq3, response.context["equipos"])
