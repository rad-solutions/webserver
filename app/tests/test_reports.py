import os
import tempfile
from datetime import date, datetime, timedelta, timezone

from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from ..models import (
    Anotacion,
    ClientBranch,
    ClientProfile,
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

        self.role_dtp, _ = Role.objects.get_or_create(name=RoleChoices.DIRECTOR_TECNICO)
        self.admin_user.roles.add(self.role_dtp)

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
            fecha_inicio=datetime(2024, 1, 10, tzinfo=timezone(-timedelta(hours=5))),
        )
        self.process_calidad = Process.objects.create(
            user=self.user,
            process_type=self.process_type_calidad,
            estado=self.process_status_progreso,
            fecha_inicio=datetime(2024, 2, 15, tzinfo=timezone(-timedelta(hours=5))),
        )
        # Proceso para otro usuario (admin en este caso, para probar que no se listen sus reportes para el cliente)
        self.process_admin = Process.objects.create(
            user=self.admin_user,
            process_type=self.process_type_asesoria,
            estado=self.process_status_progreso,
            fecha_inicio=datetime(2024, 3, 1, tzinfo=timezone(-timedelta(hours=5))),
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
            2024, 1, 15, 10, 0, 0, tzinfo=timezone(-timedelta(hours=5))
        )
        self.report1_asesoria_jan.save()

        self.report2_calidad_feb = Report.objects.create(
            user=self.user,
            process=self.process_calidad,
            equipment=self.equipment1_calidad,
            title="Reporte Calidad Febrero",
            pdf_file=SimpleUploadedFile(self.temp_file_name, self.temp_file_content),
            estado_reporte=EstadoReporteChoices.REVISADO,
        )
        self.report2_calidad_feb.created_at = datetime(
            2024, 2, 20, 11, 0, 0, tzinfo=timezone(-timedelta(hours=5))
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
            2024, 3, 25, 12, 0, 0, tzinfo=timezone(-timedelta(hours=5))
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
            2024, 3, 10, 10, 0, 0, tzinfo=timezone(-timedelta(hours=5))
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
                "equipment": self.equipment2_asesoria.id,
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
        self.assertFormError(form_in_context, "title", "Este campo es obligatorio.")

    def test_report_create_view_post_invalid_no_pdf(self):
        self.client.login(username="testuser", password="testpassword")
        url = reverse("report_create")
        initial_count = Report.objects.count()
        data = {
            "title": "Informe sin archivo",
            "description": "Este informe no tiene archivo PDF",
            "process": self.process.id,
            "user": self.user.id,
            "estado_reporte": EstadoReporteChoices.EN_GENERACION,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Report.objects.count(), initial_count)
        form_in_context = response.context.get("form")
        self.assertIsNotNone(
            form_in_context,
            "El formulario no se encontró en el contexto de la respuesta.",
        )
        self.assertFormError(form_in_context, "pdf_file", "Este campo es obligatorio.")

    def test_report_create_view_post_invalid_file_type(self):
        """Test que verifica la validación del tipo de archivo.

        Debe fallar si se sube un archivo que no es PDF.
        """
        self.client.login(username="testuser", password="testpassword")
        url = reverse("report_create")
        initial_count = Report.objects.count()

        # Crear un archivo temporal .txt
        txt_content = b"Este no es un archivo PDF."
        txt_file = SimpleUploadedFile(
            "test_file.txt", txt_content, content_type="text/plain"
        )

        data = {
            "title": "Informe con archivo incorrecto",
            "description": "Intento de subir un .txt",
            "pdf_file": txt_file,  # Archivo no PDF
            "process": self.process.id,
            "user": self.user.id,
            "equipment": self.equipment2_asesoria.id,
            "estado_reporte": EstadoReporteChoices.EN_GENERACION,
            "fecha_vencimiento": date.today() + timedelta(days=30),
        }
        response = self.client.post(url, data, format="multipart")

        self.assertEqual(
            response.status_code, 200
        )  # Debería volver a mostrar el formulario
        self.assertEqual(
            Report.objects.count(), initial_count
        )  # No se debe crear el reporte
        form_in_context = response.context.get("form")
        self.assertIsNotNone(
            form_in_context,
            "El formulario no se encontró en el contexto de la respuesta.",
        )
        self.assertTrue(form_in_context.errors, "El formulario debería tener errores.")
        self.assertFormError(
            form_in_context,
            "pdf_file",
            "Archivo no válido. Solo se permiten archivos PDF.",
        )

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
        """Test ReportListView filtrando por ID de equipo.

        Debe mostrar solo el historial de control de calidad para ese equipo.
        """
        self.client.login(username="testuser", password="testpassword")
        # Asumiendo que report2_calidad_feb está asociado a equipment1_calidad
        # y es un reporte de control de calidad.
        url = reverse("report_list") + f"?equipment_id={self.equipment1_calidad.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        reports_in_context = response.context["reports"]

        # Verificar que solo se listen los reportes de CC del equipo especificado
        # y que el método get_quality_control_history() los devuelva.
        # Si solo hay uno (report2_calidad_feb):
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
        # El process_type seleccionado debería ser 'todos' o no estar presente si el filtro de equipo tuvo prioridad.
        # La vista actual lo deja como 'todos' si no se especifica en la URL.
        self.assertEqual(response.context["selected_process_type"], "todos")

    def test_report_list_view_filter_by_equipment_id_and_process_type(self):
        """Test ReportListView con ID de equipo y tipo de proceso.

        Si equipment_id es válido, el process_type de la URL es ignorado
        y se usa equipo.get_quality_control_history().
        """
        self.client.login(username="testuser", password="testpassword")
        # Filtrar por equipment1_calidad Y process_type=control_calidad (que coincide)
        url = (
            reverse("report_list")
            + f"?equipment_id={self.equipment1_calidad.id}&process_type={self.process_type_calidad}"
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        reports_in_context = response.context["reports"]

        # Debería devolver solo los reportes de CC de equipment1_calidad
        self.assertEqual(len(reports_in_context), 1)
        self.assertIn(self.report2_calidad_feb, reports_in_context)

        self.assertEqual(
            str(response.context["selected_equipment_id"]),
            str(self.equipment1_calidad.id),
        )
        # Aunque process_type se pasó en la URL, el contexto reflejará lo que se usó para el filtro.
        # Dado que equipment_id tuvo prioridad, selected_process_type en el contexto
        # será el que se pasó en la URL, pero el filtrado real fue por get_quality_control_history.
        self.assertEqual(
            response.context["selected_process_type"], self.process_type_calidad
        )

    def test_report_list_view_filter_by_equipment_id_wrong_process_type(self):
        """Test ReportListView con ID de equipo y un tipo de proceso que no coincide.

        Según la vista actual:
        1. Se filtra por equipment_id.
        2. Luego, si el primer bloque de CC no se aplicó, se filtra por process_type.
        """
        self.client.login(username="testuser", password="testpassword")
        # Filtrar por equipment1_calidad pero pedir 'asesoria'
        url = (
            reverse("report_list")
            + f"?equipment_id={self.equipment1_calidad.id}&process_type={self.process_type_asesoria}"
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        reports_in_context = response.context["reports"]

        # El reporte asociado a equipment1_calidad es report2_calidad_feb (tipo CC).
        # El filtro process_type='asesoria' se aplica después, por lo que no debería haber resultados.
        self.assertEqual(len(reports_in_context), 0)
        self.assertNotIn(self.report2_calidad_feb, reports_in_context)

        self.assertEqual(
            str(response.context["selected_equipment_id"]),
            str(self.equipment1_calidad.id),
        )
        self.assertEqual(
            response.context["selected_process_type"], self.process_type_asesoria
        )

    def test_report_list_view_filter_by_non_existent_equipment_id(self):
        """Test ReportListView con un ID de equipo que no existe.

        Según la vista actual:
        1. El filtro por equipment__id (inexistente) vaciará el queryset.
        2. El filtro posterior por process_type se aplicará a un queryset vacío.
        """
        self.client.login(username="testuser", password="testpassword")
        non_existent_equipment_id = 99999
        # Probar con un process_type general
        url = (
            reverse("report_list")
            + f"?equipment_id={non_existent_equipment_id}&process_type={self.process_type_asesoria}"
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        reports_in_context = response.context["reports"]

        # Como equipment_id no existe, el queryset.filter(equipment__id=...) lo vacía.
        self.assertEqual(len(reports_in_context), 0)
        self.assertNotIn(self.report1_asesoria_jan, reports_in_context)
        self.assertNotIn(self.report3_asesoria_mar, reports_in_context)
        self.assertNotIn(self.report2_calidad_feb, reports_in_context)

        self.assertEqual(
            str(response.context["selected_equipment_id"]),
            str(non_existent_equipment_id),
        )
        self.assertNotIn(
            "filtered_equipment", response.context
        )  # Porque el equipo no se encontró
        self.assertEqual(
            response.context["selected_process_type"], self.process_type_asesoria
        )

    def test_report_list_view_filter_by_equipment_id_and_dates(self):
        """Test filtrando por ID de equipo y rango de fechas."""
        self.client.login(username="testuser", password="testpassword")
        # Crear otro reporte de CC para equipment1_calidad con fecha diferente
        report_cc_anterior = Report.objects.create(
            user=self.user,
            process=self.process_calidad,  # Mismo proceso que equipment1_calidad
            equipment=self.equipment1_calidad,
            title="Reporte Calidad Enero para Equipo1",
            pdf_file=SimpleUploadedFile("cc_enero.pdf", self.temp_file_content),
        )
        report_cc_anterior.created_at = datetime(
            2024, 1, 20, tzinfo=timezone(-timedelta(hours=5))
        )
        report_cc_anterior.save()

        # self.report2_calidad_feb.created_at es 2024-02-20
        start_date_filter = "2024-02-01"
        end_date_filter = "2024-02-28"

        url = (
            reverse("report_list")
            + f"?equipment_id={self.equipment1_calidad.id}&start_date={start_date_filter}&end_date={end_date_filter}"
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        reports_in_context = response.context["reports"]

        # Debería obtener el historial de CC de equipment1_calidad y LUEGO filtrar por fecha.
        self.assertEqual(len(reports_in_context), 1)
        self.assertIn(self.report2_calidad_feb, reports_in_context)
        self.assertNotIn(report_cc_anterior, reports_in_context)

        self.assertEqual(
            str(response.context["selected_equipment_id"]),
            str(self.equipment1_calidad.id),
        )
        self.assertEqual(response.context["start_date"], start_date_filter)
        self.assertEqual(response.context["end_date"], end_date_filter)

    def test_report_create_view_shows_correct_labels(self):
        """Verifica que el formulario de creación de reportes muestra las etiquetas en español."""
        self.client.login(username="adminuser", password="adminpassword")
        url = reverse("report_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Verificar algunas de las nuevas etiquetas
        self.assertContains(response, "Título del Reporte")
        self.assertContains(response, "Archivo PDF")
        self.assertContains(response, "Fecha de Vencimiento")

    def test_report_create_with_long_filename(self):
        """Test that a report can be created with a PDF file that has a name longer than 100 characters."""
        self.client.login(username="testuser", password="testpassword")
        url = reverse("report_create")
        initial_count = Report.objects.count()

        # Create a filename that is longer than 100 characters
        long_filename = "a" * 150 + ".pdf"
        pdf_content = b"This is a test PDF content."
        pdf_file = SimpleUploadedFile(
            long_filename, pdf_content, content_type="application/pdf"
        )

        data = {
            "title": "Informe con nombre de archivo largo",
            "description": "Prueba de subida de archivo con nombre largo.",
            "pdf_file": pdf_file,
            "process": self.process.id,
            "user": self.user.id,
            "equipment": self.equipment2_asesoria.id,
            "estado_reporte": EstadoReporteChoices.EN_GENERACION,
            "fecha_vencimiento": date.today() + timedelta(days=30),
        }
        response = self.client.post(url, data, format="multipart")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Report.objects.count(), initial_count + 1)
        self.assertRedirects(response, reverse("report_list"))

        new_report = Report.objects.latest("created_at")
        self.assertEqual(new_report.title, "Informe con nombre de archivo largo")
        self.assertTrue(new_report.pdf_file.name.endswith(long_filename))


class ReportStatusAndNoteTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        change_report_perm = Permission.objects.get(codename="change_report")
        view_report_perm = Permission.objects.get(codename="view_report")
        self.user.user_permissions.add(change_report_perm, view_report_perm)
        self.process = Process.objects.create(
            user=self.user, process_type=ProcessTypeChoices.ASESORIA
        )
        self.temp_file_content = b"contenido de prueba del PDF"
        self.temp_file_name = "test.pdf"
        self.report = Report.objects.create(
            user=self.user,
            process=self.process,
            pdf_file=SimpleUploadedFile(self.temp_file_name, self.temp_file_content),
            title="Reporte de prueba",
            estado_reporte=EstadoReporteChoices.EN_GENERACION,
        )
        self.client.login(username="testuser", password="testpass")

        self.url = reverse("report_status_and_note", args=[self.report.id])

    def tearDown(self):
        for report in Report.objects.all():
            if report.pdf_file and hasattr(report.pdf_file, "path"):
                if os.path.exists(report.pdf_file.path):
                    try:
                        os.remove(report.pdf_file.path)
                    except OSError:
                        pass

    def test_change_status_and_add_note(self):
        data = {
            "estado_reporte": EstadoReporteChoices.APROBADO,
            "anotacion": "Nueva anotación para el proceso.",
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(response, reverse("report_detail", args=[self.report.id]))
        self.report.refresh_from_db()
        self.assertEqual(self.report.estado_reporte, EstadoReporteChoices.APROBADO)
        anotaciones = Anotacion.objects.filter(proceso=self.process)
        self.assertEqual(anotaciones.count(), 1)
        self.assertEqual(
            anotaciones.first().contenido, "Nueva anotación para el proceso."
        )

    def test_change_status_without_note(self):
        data = {
            "estado_reporte": EstadoReporteChoices.REVISADO,
            "anotacion": "",
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(response, reverse("report_detail", args=[self.report.id]))
        self.report.refresh_from_db()
        self.assertEqual(self.report.estado_reporte, EstadoReporteChoices.REVISADO)
        self.assertFalse(Anotacion.objects.filter(proceso=self.process).exists())

    def test_get_form(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Actualizar Estado del Reporte")
        self.assertContains(response, "Anotación al proceso")


class ReportListEquipmentFilterTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Crear usuario y rol
        cls.user = User.objects.create_user(username="test_equip_filter", password="p")
        role_cliente, _ = Role.objects.get_or_create(name=RoleChoices.CLIENTE)
        cls.user.roles.add(role_cliente)

        # Asignar permisos necesarios para ver la lista
        view_report_perm = Permission.objects.get(codename="view_report")
        cls.user.user_permissions.add(view_report_perm)

        # Crear equipos con datos variados
        cls.eq1 = Equipment.objects.create(
            user=cls.user,
            nombre="Equipo A1",
            marca="Siemens",
            modelo="X-100",
            serial="SN-A1",
        )
        cls.eq2 = Equipment.objects.create(
            user=cls.user,
            nombre="Equipo A2",
            marca="Siemens",
            modelo="Y-200",
            serial="SN-A2",
        )
        cls.eq3 = Equipment.objects.create(
            user=cls.user,
            nombre="Equipo B1",
            marca="GE",
            modelo="X-100",
            serial="SN-B1",
        )

        # Crear reportes asociados a los equipos
        cls.report1 = Report.objects.create(
            user=cls.user, title="Reporte para A1", equipment=cls.eq1
        )
        cls.report2 = Report.objects.create(
            user=cls.user, title="Reporte para A2", equipment=cls.eq2
        )
        cls.report3 = Report.objects.create(
            user=cls.user, title="Reporte para B1", equipment=cls.eq3
        )

        cls.url = reverse("report_list")

    def setUp(self):
        self.client.login(username="test_equip_filter", password="p")

    def test_filter_by_marca(self):
        """Prueba que el filtro por marca de equipo funcione."""
        response = self.client.get(self.url, {"marca": "Siemens"})
        self.assertEqual(response.status_code, 200)
        reports_in_context = response.context["reports"]
        self.assertEqual(len(reports_in_context), 2)
        self.assertIn(self.report1, reports_in_context)
        self.assertIn(self.report2, reports_in_context)
        self.assertEqual(response.context["marca_filter"], "Siemens")

    def test_filter_by_modelo_case_insensitive(self):
        """Prueba que el filtro por modelo sea insensible a mayúsculas."""
        response = self.client.get(self.url, {"modelo": "x-100"})  # en minúsculas
        self.assertEqual(response.status_code, 200)
        reports_in_context = response.context["reports"]
        self.assertEqual(len(reports_in_context), 2)
        self.assertIn(self.report1, reports_in_context)
        self.assertIn(self.report3, reports_in_context)
        self.assertEqual(response.context["modelo_filter"], "x-100")

    def test_filter_by_serial_partial(self):
        """Prueba que el filtro por serial parcial funcione."""
        response = self.client.get(self.url, {"serial": "SN-A"})
        self.assertEqual(response.status_code, 200)
        reports_in_context = response.context["reports"]
        self.assertEqual(len(reports_in_context), 2)
        self.assertIn(self.report1, reports_in_context)
        self.assertIn(self.report2, reports_in_context)
        self.assertEqual(response.context["serial_filter"], "SN-A")

    def test_combined_equipment_filters(self):
        """Prueba una combinación de los nuevos filtros de equipo."""
        params = {"marca": "Siemens", "modelo": "X-100"}
        response = self.client.get(self.url, params)
        self.assertEqual(response.status_code, 200)
        reports_in_context = response.context["reports"]
        self.assertEqual(len(reports_in_context), 1)
        self.assertIn(self.report1, reports_in_context)
        self.assertEqual(response.context["marca_filter"], "Siemens")
        self.assertEqual(response.context["modelo_filter"], "X-100")

    def test_filter_with_no_results(self):
        """Prueba un filtro de equipo que no debe devolver resultados."""
        response = self.client.get(self.url, {"marca": "Philips"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["reports"]), 0)
        self.assertContains(response, "No hay reportes registrados.")


class ReportFilterTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # ... (crear usuarios, roles, etc.) ...
        cls.client_user = User.objects.create_user(
            username="cliente_test", password="password"
        )
        role_cliente, _ = Role.objects.get_or_create(name=RoleChoices.CLIENTE)
        cls.client_user.roles.add(role_cliente)

        cls.profile = ClientProfile.objects.create(
            user=cls.client_user, razon_social="Cliente S.A.", nit="111"
        )

        cls.sede1 = ClientBranch.objects.create(
            company=cls.profile, nombre="Sede Norte", direccion_instalacion="Dir 1"
        )
        cls.sede2 = ClientBranch.objects.create(
            company=cls.profile, nombre="Sede Sur", direccion_instalacion="Dir 2"
        )

        cls.equipment1_sede1 = Equipment.objects.create(
            user=cls.client_user, nombre="Equipo A", sede=cls.sede1
        )
        cls.equipment2_sede2 = Equipment.objects.create(
            user=cls.client_user, nombre="Equipo B", sede=cls.sede2
        )

        cls.report1 = Report.objects.create(
            user=cls.client_user, title="Reporte Sede 1", equipment=cls.equipment1_sede1
        )
        cls.report2 = Report.objects.create(
            user=cls.client_user, title="Reporte Sede 2", equipment=cls.equipment2_sede2
        )

        cls.internal_user = User.objects.create_user(
            username="interno", password="password"
        )
        role_gerente, _ = Role.objects.get_or_create(name=RoleChoices.GERENTE)
        cls.internal_user.roles.add(role_gerente)

    def test_filter_by_sede_for_internal_user(self):
        """Verifica que un usuario interno puede filtrar reportes por sede."""
        self.client.login(username="interno", password="password")
        url = (
            reverse("report_list")
            + f"?client_user={self.client_user.id}&sede={self.sede1.id}"
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.report1.title)
        self.assertNotContains(response, self.report2.title)
        self.assertEqual(len(response.context["reports"]), 1)

    def test_filter_by_sede_for_client_user(self):
        """Verifica que un usuario cliente puede filtrar sus propios reportes por sede."""
        self.client.login(username="cliente_test", password="password")
        url = reverse("report_list") + f"?sede={self.sede2.id}"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.report1.title)
        self.assertContains(response, self.report2.title)
        self.assertEqual(len(response.context["reports"]), 1)

    def test_ajax_load_client_branches(self):
        """Verifica que la vista AJAX devuelve las sedes correctas."""
        self.client.login(username="interno", password="password")
        url = reverse("ajax_load_client_branches") + f"?user_id={self.client_user.id}"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
        sede_names = {item["name"] for item in data}
        self.assertIn("Sede Norte", sede_names)
        self.assertIn("Sede Sur", sede_names)

    def test_filter_by_client_user_only(self):
        """Test para verificar que un usuario interno puede filtrar reportes por cliente.

        Verifica que un usuario interno puede filtrar por cliente,
        obteniendo todos los reportes de todas las sedes de ese cliente.
        """
        # Crear un segundo cliente para asegurar que el filtro funciona
        other_client = User.objects.create_user(username="otro_cliente", password="p")
        role_cliente, _ = Role.objects.get_or_create(name=RoleChoices.CLIENTE)
        other_client.roles.add(role_cliente)
        other_profile = ClientProfile.objects.create(
            user=other_client, razon_social="Otra S.A.", nit="222"
        )
        other_sede = ClientBranch.objects.create(
            company=other_profile, nombre="Sede Unica", direccion_instalacion="Dir 3"
        )
        other_equipment = Equipment.objects.create(
            user=other_client, nombre="Equipo C", sede=other_sede
        )
        Report.objects.create(
            user=other_client, title="Reporte Otro Cliente", equipment=other_equipment
        )

        self.client.login(username="interno", password="password")
        # Filtrar solo por el primer cliente, sin especificar sede
        url = reverse("report_list") + f"?client_user={self.client_user.id}"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Debe contener los dos reportes del primer cliente
        self.assertContains(response, self.report1.title)
        self.assertContains(response, self.report2.title)
        # NO debe contener el reporte del otro cliente
        self.assertNotContains(response, "Reporte Otro Cliente")
        self.assertEqual(len(response.context["reports"]), 2)


class Select2WidgetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Crear roles
        cls.role_gerente, _ = Role.objects.get_or_create(name=RoleChoices.GERENTE)
        cls.role_cliente, _ = Role.objects.get_or_create(name=RoleChoices.CLIENTE)
        cls.role_director, _ = Role.objects.get_or_create(
            name=RoleChoices.DIRECTOR_TECNICO
        )

        # Crear usuario gerente para las pruebas
        cls.gerente_user = User.objects.create_user(
            username="gerente_select2", password="password"
        )
        cls.gerente_user.roles.add(cls.role_gerente)
        cls.director_user = User.objects.create_user(
            username="director_select2", password="password"
        )
        cls.director_user.roles.add(cls.role_director)

        # Crear usuarios cliente para buscar
        cls.cliente1 = User.objects.create_user(
            username="cliente_uno", first_name="Empresa", last_name="Uno"
        )
        cls.cliente1.roles.add(cls.role_cliente)
        ClientProfile.objects.create(
            user=cls.cliente1, razon_social="Empresa Uno S.A.S.", nit="111-1"
        )

        cls.cliente2 = User.objects.create_user(
            username="cliente_dos", first_name="Compañía", last_name="Dos"
        )
        cls.cliente2.roles.add(cls.role_cliente)
        ClientProfile.objects.create(
            user=cls.cliente2, razon_social="Compañía Dos Ltda.", nit="222-2"
        )

        # Cliente sin perfil para probar el caso límite
        cls.cliente3_sin_perfil = User.objects.create_user(
            username="cliente_tres_sinperfil", first_name="Cliente", last_name="Tres"
        )
        cls.cliente3_sin_perfil.roles.add(cls.role_cliente)

    def setUp(self):
        self.client.login(username="director_select2", password="password")

    def test_user_lookup_view_returns_json(self):
        """Verifica que la vista de búsqueda AJAX devuelve una respuesta JSON 200."""
        url = reverse("select2_model_user")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "application/json")

    def test_user_lookup_view_search_by_razon_social(self):
        """Verifica que la búsqueda por razón social funciona."""
        url = reverse("select2_model_user")
        response = self.client.get(url, {"term": "Uno S.A.S."})
        data = response.json()
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["results"][0]["id"], self.cliente1.id)
        self.assertEqual(data["results"][0]["text"], "Empresa Uno S.A.S.")

    def test_user_lookup_view_search_by_username(self):
        """Verifica que la búsqueda por nombre de usuario funciona."""
        url = reverse("select2_model_user")
        response = self.client.get(url, {"term": "cliente_dos"})
        data = response.json()
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["results"][0]["id"], self.cliente2.id)

    def test_user_lookup_view_handles_user_without_profile(self):
        """Verifica que la vista maneja correctamente usuarios sin ClientProfile."""
        url = reverse("select2_model_user")
        response = self.client.get(url, {"term": "tres_sinperfil"})
        data = response.json()
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["results"][0]["id"], self.cliente3_sin_perfil.id)
        self.assertEqual(
            data["results"][0]["text"], "Cliente Tres"
        )  # Fallback a get_full_name()

    def test_report_form_renders_select2_widget(self):
        """Verifica que el formulario de creación de reportes renderiza el widget Select2."""
        response = self.client.get(reverse("report_create"))
        self.assertEqual(response.status_code, 200)
        # Verificar la presencia de los atributos y clases de Select2
        self.assertContains(
            response,
            'class="modelselect2widget form-select django-select2 django-select2-heavy"',
        )
        self.assertContains(
            response, 'data-placeholder="Escriba para buscar un cliente..."'
        )

    def test_report_list_filter_renders_select2_ajax(self):
        """Verifica que el filtro de la lista de reportes está configurado para Select2 AJAX."""
        response = self.client.get(reverse("report_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, f'data-ajax--url="{reverse("select2_model_user")}"'
        )

    def test_report_list_filter_shows_selected_client(self):
        """Verifica que si un cliente está filtrado, aparece como seleccionado en el widget."""
        url = reverse("report_list") + f"?client_user={self.cliente1.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # El HTML debe contener la opción pre-seleccionada para que Select2 la muestre
        self.assertContains(response, "Empresa Uno S.A.S.")
