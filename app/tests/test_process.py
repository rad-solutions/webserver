import re
from datetime import date, datetime, timedelta, timezone

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone as tz

from ..models import (
    Anotacion,
    ChecklistItemDefinition,
    ChecklistItemStatusChoices,
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
from ..views import AnotacionForm


class ProcessAPITest(TestCase):
    def setUp(self):
        self.user_cliente, _ = Role.objects.get_or_create(name=RoleChoices.CLIENTE)
        self.user_gerente, _ = Role.objects.get_or_create(name=RoleChoices.GERENTE)
        self.user = User.objects.create_user(username="procuser", password="password")
        self.user.roles.add(self.user_cliente)

        self.admin_user = User.objects.create_user(
            username="admin_proc", password="password", is_staff=True
        )
        self.admin_user.roles.add(self.user_gerente)
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

        # Anotaciones para el proceso 1
        self.anotacion1_p1 = Anotacion.objects.create(
            proceso=self.proc1,
            usuario=self.admin_user,
            contenido="Primera anotación para P1",
            fecha_creacion=datetime(
                2023, 1, 1, 10, 0, 0, tzinfo=timezone.utc
            ),  # Fecha explícita
        )
        self.anotacion2_p1 = Anotacion.objects.create(
            proceso=self.proc1,
            usuario=self.user,
            contenido="Segunda anotación para P1",
            fecha_creacion=datetime(
                2023, 1, 2, 11, 0, 0, tzinfo=timezone.utc
            ),  # Fecha explícita
        )
        # Forzar la actualización de fecha_creacion si auto_now_add interfiere con fechas explícitas
        Anotacion.objects.filter(id=self.anotacion1_p1.id).update(
            fecha_creacion=datetime(2023, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        )
        Anotacion.objects.filter(id=self.anotacion2_p1.id).update(
            fecha_creacion=datetime(2023, 1, 2, 11, 0, 0, tzinfo=timezone.utc)
        )
        self.anotacion1_p1.refresh_from_db()
        self.anotacion2_p1.refresh_from_db()

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

        # Tipos de Proceso
        self.pt_asesoria = ProcessTypeChoices.ASESORIA
        self.pt_calidad = ProcessTypeChoices.CONTROL_CALIDAD
        self.pt_blindajes = ProcessTypeChoices.CALCULO_BLINDAJES

        # Estados de Proceso
        self.estado_progreso = ProcessStatusChoices.EN_PROGRESO
        self.estado_finalizado = ProcessStatusChoices.FINALIZADO

        # Procesos
        self.proceso1_asesoria_progreso = Process.objects.create(
            user=self.user,
            process_type=self.pt_asesoria,
            estado=self.estado_progreso,
            fecha_inicio=datetime(2023, 1, 10, tzinfo=timezone.utc),
        )
        self.proceso1_asesoria_progreso.fecha_inicio = datetime(
            2023, 1, 10, tzinfo=timezone.utc
        )
        self.proceso1_asesoria_progreso.save()

        self.proceso2_calidad_finalizado = Process.objects.create(
            user=self.user,
            process_type=self.pt_calidad,
            estado=self.estado_finalizado,
            fecha_inicio=datetime(2023, 2, 10, tzinfo=timezone.utc),
            fecha_final=datetime(2023, 2, 20, tzinfo=timezone.utc),
        )
        self.proceso2_calidad_finalizado.fecha_inicio = datetime(
            2023, 2, 10, tzinfo=timezone.utc
        )
        self.proceso2_calidad_finalizado.save()

        self.proceso4_blindajes_progreso = Process.objects.create(
            user=self.user,
            process_type=self.pt_blindajes,
            estado=self.estado_progreso,
            fecha_inicio=datetime(2023, 4, 10, tzinfo=timezone.utc),
        )
        self.proceso4_blindajes_progreso.fecha_inicio = datetime(
            2023, 4, 10, tzinfo=timezone.utc
        )
        self.proceso4_blindajes_progreso.save()

        # Equipos (asociados a los procesos)
        self.equipo1_proc1 = Equipment.objects.create(
            nombre="Equipo P1 Asesoria",
            user=self.user,
            process=self.proceso1_asesoria_progreso,
            serial="EQP1",
        )
        self.equipo2_proc2 = Equipment.objects.create(
            nombre="Equipo P2 Calidad",
            user=self.user,
            process=self.proceso2_calidad_finalizado,
            serial="EQP2",
        )
        self.equipo4_proc4 = Equipment.objects.create(
            nombre="Equipo P4 Blindajes",
            user=self.user,
            process=self.proceso4_blindajes_progreso,
            serial="EQP4",
        )
        self.process = Process.objects.create(
            user=self.user,
            process_type=ProcessTypeChoices.ASESORIA,
            estado=ProcessStatusChoices.EN_PROGRESO,
            fecha_inicio=datetime.now(timezone.utc),
        )

        # Crear definiciones de checklist y asociar items al proceso
        self.def1 = ChecklistItemDefinition.objects.create(
            process_type=ProcessTypeChoices.ASESORIA,
            name="Primer ítem",
            order=1,
            percentage=50,
        )
        self.def2 = ChecklistItemDefinition.objects.create(
            process_type=ProcessTypeChoices.ASESORIA,
            name="Segundo ítem",
            order=2,
            percentage=50,
        )
        self.item1 = ProcessChecklistItem.objects.create(
            process=self.process,
            definition=self.def1,
            status=ChecklistItemStatusChoices.PENDIENTE,
        )
        self.item2 = ProcessChecklistItem.objects.create(
            process=self.process,
            definition=self.def2,
            status=ChecklistItemStatusChoices.APROBADO,
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

    def test_process_detail_view_shows_anotaciones(self):
        self.client.login(username="clientuser", password="password123")
        url = reverse("process_detail", args=[self.proc1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "process/process_detail.html")
        self.assertContains(response, self.anotacion1_p1.contenido)
        self.assertContains(response, self.anotacion2_p1.contenido)

        # Verificar el orden (la más reciente primero)
        # El contenido de la anotacion2 (más reciente) debe aparecer antes que el de la anotacion1
        content_str = response.content.decode("utf-8")
        pos_anotacion2 = content_str.find(self.anotacion2_p1.contenido)
        pos_anotacion1 = content_str.find(self.anotacion1_p1.contenido)
        self.assertTrue(
            pos_anotacion1 != -1 and pos_anotacion2 != -1,
            "Ambas anotaciones deben estar en la respuesta",
        )
        self.assertTrue(
            pos_anotacion2 < pos_anotacion1,
            "La anotación más reciente debe aparecer primero.",
        )

        # Verificar enlace para agregar anotación (si el usuario tiene permiso)
        # El cliente no tiene permiso para añadir anotaciones en este setup.
        self.assertNotContains(
            response, reverse("anotacion_create", kwargs={"process_id": self.proc1.id})
        )

        # Probar con usuario que sí tiene permiso
        self.client.logout()
        self.client.login(username="admin_proc", password="password")
        url = reverse("process_detail", args=[self.proc1.id])
        response_manager = self.client.get(url)
        self.assertEqual(response_manager.status_code, 200)
        self.assertContains(
            response_manager,
            reverse("anotacion_create", kwargs={"process_id": self.proc1.id}),
        )

    def test_anotacion_create_for_process_view_get(self):
        self.client.login(
            username="admin_proc", password="password"
        )  # Usuario con permiso
        url = reverse("anotacion_create", kwargs={"process_id": self.proc1.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "process/anotacion_form.html")
        self.assertIsInstance(response.context["form"], AnotacionForm)
        self.assertEqual(response.context["proceso"], self.proc1)

    def test_anotacion_create_for_process_view_post(self):
        self.client.login(username="admin_proc", password="password")
        url = reverse("anotacion_create", kwargs={"process_id": self.proc1.id})
        initial_anotaciones_count = Anotacion.objects.filter(proceso=self.proc1).count()
        data = {
            "contenido": "Nueva anotación desde test POST",
        }
        response = self.client.post(url, data)

        # Debería redirigir a process_detail
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("process_detail", args=[self.proc1.id]))

        self.assertEqual(
            Anotacion.objects.filter(proceso=self.proc1).count(),
            initial_anotaciones_count + 1,
        )
        nueva_anotacion = (
            Anotacion.objects.filter(proceso=self.proc1)
            .order_by("-fecha_creacion")
            .first()
        )
        self.assertEqual(nueva_anotacion.contenido, "Nueva anotación desde test POST")
        self.assertEqual(
            nueva_anotacion.usuario, self.admin_user
        )  # Asignado automáticamente
        self.assertEqual(nueva_anotacion.proceso, self.proc1)  # Asignado desde URL

    def test_anotacion_create_for_process_view_no_permission(self):
        self.client.login(
            username="procuser", password="password"
        )  # Usuario SIN permiso
        url = reverse("anotacion_create", kwargs={"process_id": self.proc1.id})
        response = self.client.get(url)
        self.assertEqual(
            response.status_code, 403
        )  # O la redirección a login si raise_exception=False

        response_post = self.client.post(url, {"contenido": "Intento fallido"})
        self.assertEqual(response_post.status_code, 403)

    def test_process_list_filter_by_estado(self):
        """Test ProcessListView filtrando por estado del proceso del equipo."""
        url = reverse("process_list") + f"?estado={self.estado_progreso}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        equipos_in_context = response.context.get("equipos", [])
        self.assertEqual(
            len(equipos_in_context), 3
        )  # eq_p1 equipo1_proc1 y equipo4_proc4
        self.assertIn(self.equipo1_proc1, equipos_in_context)
        self.assertIn(self.equipo4_proc4, equipos_in_context)
        self.assertIn(self.eq_p1, equipos_in_context)
        self.assertNotIn(self.equipo2_proc2, equipos_in_context)  # Es finalizado
        self.assertEqual(response.context.get("selected_estado"), self.estado_progreso)

    def test_process_list_filter_by_process_type_and_estado(self):
        """Test ProcessListView filtrando por tipo de proceso y estado."""
        url = (
            reverse("process_list")
            + f"?process_type={self.pt_asesoria}&estado={self.estado_progreso}"
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        equipos_in_context = response.context.get("equipos", [])
        self.assertEqual(len(equipos_in_context), 2)  # eq_p1 y equipo1_proc1
        self.assertIn(self.equipo1_proc1, equipos_in_context)
        self.assertIn(self.eq_p1, equipos_in_context)
        self.assertEqual(
            response.context.get("selected_process_type"), self.pt_asesoria
        )
        self.assertEqual(response.context.get("selected_estado"), self.estado_progreso)

    def test_process_list_filter_by_estado_and_fecha_inicio(self):
        """Test ProcessListView combinando filtro de estado y fecha_inicio."""
        start_date = "2023-01-01"
        end_date = "2023-01-31"  # Solo Enero
        url = (
            reverse("process_list")
            + f"?estado={self.estado_progreso}&inicio_start_date={start_date}&inicio_end_date={end_date}"
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        equipos_in_context = response.context.get("equipos", [])
        self.assertEqual(len(equipos_in_context), 1)
        self.assertIn(
            self.equipo1_proc1, equipos_in_context
        )  # Proceso 1 es EN_PROGRESO y fecha_inicio 2023-01-10
        self.assertEqual(response.context.get("selected_estado"), self.estado_progreso)
        self.assertEqual(response.context.get("inicio_start_date"), start_date)
        self.assertEqual(response.context.get("inicio_end_date"), end_date)

    def test_progress_form_shows_checklist_items(self):
        self.url = reverse("process_progress", args=[self.process.id])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        # Los nombres de los ítems deben aparecer
        self.assertContains(response, self.def1.name)
        self.assertContains(response, self.def2.name)

    def test_progress_form_update_checklist_and_status(self):
        # Simula marcar el primer ítem como completado y cambiar el estado del proceso
        self.url = reverse("process_progress", args=[self.process.id])
        started_at = date(2025, 6, 20)
        completed_at = date(2025, 6, 21)
        data = {
            "estado": ProcessStatusChoices.FINALIZADO,
            "checklist_items-TOTAL_FORMS": "2",
            "checklist_items-INITIAL_FORMS": "2",
            "checklist_items-MIN_NUM_FORMS": "0",
            "checklist_items-MAX_NUM_FORMS": "1000",
            "checklist_items-0-id": str(self.item1.id),
            "checklist_items-0-status": ChecklistItemStatusChoices.APROBADO,  # Marcar como aprobado
            "checklist_items-0-started_at": started_at.strftime("%Y-%m-%d"),
            "checklist_items-0-completed_at": completed_at.strftime("%Y-%m-%d"),
            "checklist_items-1-id": str(self.item2.id),
            "checklist_items-1-status": ChecklistItemStatusChoices.PENDIENTE,  # Marcar como pendiente
            "checklist_items-1-started_at": "",
            "checklist_items-1-completed_at": "",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)  # Redirige al detalle del proceso

        # Refrescar de la base de datos
        self.item1.refresh_from_db()
        self.item2.refresh_from_db()
        self.process.refresh_from_db()
        self.assertTrue(self.item1.is_completed)
        self.assertEqual(self.item1.status, ChecklistItemStatusChoices.APROBADO)
        self.assertFalse(self.item2.is_completed)
        self.assertEqual(self.item2.status, ChecklistItemStatusChoices.PENDIENTE)
        self.assertEqual(self.process.estado, ProcessStatusChoices.FINALIZADO)
        # Verifica fechas y completed_by
        self.assertEqual(self.item1.started_at, started_at)
        self.assertEqual(self.item1.completed_at, completed_at)
        self.assertEqual(self.item1.completed_by, self.user)
        self.assertIsNone(self.item2.completed_by)

    def test_progress_form_no_checklist_items(self):
        # Crear un proceso sin checklist items
        process_no_items = Process.objects.create(
            user=self.user,
            process_type=ProcessTypeChoices.OTRO,
            estado=ProcessStatusChoices.EN_PROGRESO,
            fecha_inicio=datetime.now(timezone.utc),
        )
        url = reverse("process_progress", args=[process_no_items.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # No debe haber checkboxes
        self.assertNotContains(response, 'type="checkbox"')
        # El formulario debe permitir actualizar el estado
        data = {
            "estado": ProcessStatusChoices.FINALIZADO,
            "checklist_items-TOTAL_FORMS": "0",
            "checklist_items-INITIAL_FORMS": "0",
            "checklist_items-MIN_NUM_FORMS": "0",
            "checklist_items-MAX_NUM_FORMS": "1000",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        process_no_items.refresh_from_db()
        self.assertEqual(process_no_items.estado, ProcessStatusChoices.FINALIZADO)

    def test_progress_form_update_dates_without_completion(self):
        self.url = reverse("process_progress", args=[self.process.id])
        started_at = date(2025, 6, 20)
        completed_at = date(2025, 6, 21)
        data = {
            "estado": ProcessStatusChoices.EN_PROGRESO,
            "checklist_items-TOTAL_FORMS": "2",
            "checklist_items-INITIAL_FORMS": "2",
            "checklist_items-MIN_NUM_FORMS": "0",
            "checklist_items-MAX_NUM_FORMS": "1000",
            "checklist_items-0-id": str(self.item1.id),
            # No status change, solo fechas
            "checklist_items-0-started_at": started_at.strftime("%Y-%m-%d"),
            "checklist_items-0-status": ChecklistItemStatusChoices.PENDIENTE,
            "checklist_items-0-completed_at": completed_at.strftime("%Y-%m-%d"),
            "checklist_items-1-id": str(self.item2.id),
            "checklist_items-1-status": ChecklistItemStatusChoices.PENDIENTE,
            "checklist_items-1-started_at": "",
            "checklist_items-1-completed_at": "",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)

        self.item1.refresh_from_db()
        self.assertFalse(self.item1.is_completed)
        self.assertEqual(self.item1.started_at, started_at)
        self.assertEqual(self.item1.completed_at, completed_at)
        self.assertIsNone(self.item1.completed_by)

    def test_process_detail_view_shows_status_logs(self):
        # Forzar algunos cambios de estado para generar logs
        self.proc1.estado = ProcessStatusChoices.EN_REVISION
        self.proc1.save(user_who_modified=self.admin_user)
        self.proc1.estado = ProcessStatusChoices.FINALIZADO
        self.proc1.save(user_who_modified=self.user)

        url = reverse("process_detail", args=[self.proc1.id])
        self.client.login(username="admin_proc", password="password")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Debe contener los logs en el HTML (usando __str__)
        logs = self.proc1.status_logs.all()
        content_str = response.content.decode("utf-8")
        for log in logs:
            expected = str(log).replace("->", "-&gt;")
            self.assertIn(expected, content_str)

        # El log más reciente debe aparecer primero (por ordenamiento)
        content_str = response.content.decode("utf-8")
        if logs.count() >= 2:
            expected_newest = str(logs[0]).replace("->", "-&gt;")
            expected_old = str(logs[1]).replace("->", "-&gt;")
            pos_newest = content_str.find(expected_newest)
            pos_old = content_str.find(expected_old)
            self.assertTrue(
                pos_newest != -1 and pos_old != -1,
                "Ambos logs deben estar en el HTML",
            )
            self.assertTrue(
                pos_newest < pos_old,
                "El log más reciente debe aparecer primero en el historial.",
            )

    def test_progress_form_displays_completed_by_user(self):
        """Verifica que el formulario de progreso muestre quién completó un ítem."""
        # Setup: Marcar un ítem como completado por un usuario específico
        completing_user = User.objects.create_user(
            username="completer", password="p", first_name="Juan", last_name="Perez"
        )
        self.item1.status = ChecklistItemStatusChoices.APROBADO
        self.item1.completed_by = completing_user
        self.item1.save()

        # Acceder a la vista de progreso
        self.client.login(username="admin_proc", password="password")
        url = reverse("process_progress", args=[self.process.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "process/process_progress_form.html")

        # Verificar que el nombre del usuario que completó el ítem 1 está en el HTML
        # Usamos una expresión regular para encontrar la fila de la tabla (<tr>) que contiene
        # el nombre del ítem y luego verificamos que el nombre del usuario esté en esa misma fila.
        content = response.content.decode("utf-8")

        # Buscar la fila del item1 y verificar que contiene el nombre "Juan Perez"
        match_item1 = re.search(
            rf"<tr.*?>"  # Inicio de la fila
            rf".*?<td>\s*{re.escape(self.item1.name)}.*?</td>"  # Celda que CONTIENE el nombre del ítem
            rf".*?<td>\s*Juan Perez\s*</td>"  # Celda que CONTIENE el nombre del usuario
            rf".*?</tr>",  # Fin de la fila
            content,
            re.DOTALL | re.IGNORECASE,
        )
        self.assertIsNotNone(
            match_item1,
            "No se encontró el nombre del usuario que completó el ítem 1 en su fila.",
        )

        # Buscar la fila del item2 y verificar que contiene el guion "-"
        match_item2 = re.search(
            rf'<tr.*?>.*?<td>\s*{re.escape(self.item2.name)}.*?</td>.*?<span class="text-muted">-</span>.*?</tr>',
            content,
            re.DOTALL | re.IGNORECASE,
        )
        self.assertIsNotNone(
            match_item2, "No se encontró el guion para el ítem 2 incompleto."
        )

    def test_process_create_view_shows_correct_labels(self):
        """Verifica que el formulario de creación de procesos muestra las etiquetas en español."""
        self.client.login(
            username="admin_proc", password="password"
        )  # Usar un usuario con permisos
        url = reverse("process_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Verificar algunas de las nuevas etiquetas
        self.assertContains(response, "Tipo de Proceso")
        self.assertContains(response, "Cliente")
        self.assertContains(response, "Fecha de Finalización")


class ProcessAssignmentTest(TestCase):
    def setUp(self):
        # Crea usuarios y roles
        self.rol_gerente, _ = Role.objects.get_or_create(name=RoleChoices.GERENTE)
        self.rol_cliente, _ = Role.objects.get_or_create(name=RoleChoices.CLIENTE)
        self.user = User.objects.create_user(username="cliente1", password="pass")
        self.user.roles.add(self.rol_cliente)
        self.gerente = User.objects.create_user(username="gerente1", password="pass")
        self.gerente.roles.add(self.rol_gerente)
        self.rol_tecnico, _ = Role.objects.get_or_create(
            name=RoleChoices.PERSONAL_TECNICO_APOYO
        )
        self.tecnico1 = User.objects.create_user(username="tecnico1", password="pass")
        self.tecnico1.roles.add(self.rol_tecnico)
        self.tecnico2 = User.objects.create_user(username="tecnico2", password="pass")
        self.tecnico2.roles.add(self.rol_tecnico)
        self.tecnico3 = User.objects.create_user(username="tecnico3", password="pass")
        self.tecnico3.roles.add(self.rol_tecnico)
        self.tecnico4 = User.objects.create_user(username="tecnico4", password="pass")
        self.tecnico4.roles.add(self.rol_tecnico)
        self.process = Process.objects.create(
            user=self.user,
            process_type=ProcessTypeChoices.ASESORIA,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )
        self.url = reverse("process_update_assignment", args=[self.process.id])

    def test_assignment_view_requires_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_assignment_view_requires_permission(self):
        self.client.login(username="cliente1", password="pass")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_assignment_view_get(self):
        self.client.login(username="gerente1", password="pass")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "process/process_update_assignment.html")
        self.assertIn("form", response.context)
        self.assertEqual(response.context["form"].instance, self.process)

    def test_assignment_view_post_valid(self):
        self.client.login(username="gerente1", password="pass")
        data = {
            "assigned_to": self.gerente.id,
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.process.refresh_from_db()
        self.assertEqual(self.process.assigned_to.count(), 1)
        self.assertEqual(self.process.assigned_to.first(), self.gerente)

    def test_assignment_view_post_valid_multiple_users(self):
        """Prueba que se puedan asignar múltiples usuarios a un proceso."""
        self.client.login(username="gerente1", password="pass")
        data = {
            # Enviar una lista de IDs para el campo ManyToManyField
            "assigned_to": [self.gerente.id, self.tecnico1.id]
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.process.refresh_from_db()
        self.assertEqual(self.process.assigned_to.count(), 2)
        self.assertIn(self.gerente, self.process.assigned_to.all())
        self.assertIn(self.tecnico1, self.process.assigned_to.all())

    def test_assignment_fails_with_more_than_three_users(self):
        """Prueba que la validación del modelo falle al asignar más de 3 usuarios."""
        self.client.login(username="gerente1", password="pass")
        data = {
            "assigned_to": [
                self.gerente.id,
                self.tecnico1.id,
                self.tecnico2.id,
                self.tecnico3.id,  # 4 usuarios
            ]
        }
        response = self.client.post(self.url, data)
        # La validación del modelo (método clean) hace que el formulario no sea válido
        self.assertEqual(response.status_code, 200)
        form_in_context = response.context.get("form")
        self.assertFormError(
            form_in_context,
            "assigned_to",
            "No se pueden asignar más de 3 usuarios a un proceso.",
        )

    def test_assignment_view_post_invalid(self):
        self.client.login(username="gerente1", password="pass")
        # Enviar un usuario inexistente
        data = {
            "assigned_to": 99999,
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertFormError(
            form,
            "assigned_to",
            "Select a valid choice. 99999 is not one of the available choices.",
        )


class ProcessInternalListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Crea datos una sola vez para toda la clase de tests."""
        # Roles
        cls.role_cliente, _ = Role.objects.get_or_create(name=RoleChoices.CLIENTE)
        cls.role_tecnico, _ = Role.objects.get_or_create(
            name=RoleChoices.DIRECTOR_TECNICO
        )
        cls.role_gerente, _ = Role.objects.get_or_create(name=RoleChoices.GERENTE)

        # Usuarios Clientes con Perfiles
        cls.cliente_aaa = User.objects.create_user(username="cliente_aaa", password="p")
        cls.cliente_aaa.roles.add(cls.role_cliente)
        # Importante para probar el ordenamiento por razón social
        from ..models import ClientProfile

        ClientProfile.objects.create(user=cls.cliente_aaa, razon_social="AAA Company")

        cls.cliente_zzz = User.objects.create_user(username="cliente_zzz", password="p")
        cls.cliente_zzz.roles.add(cls.role_cliente)
        ClientProfile.objects.create(
            user=cls.cliente_zzz, razon_social="ZZZ Company", nit="123456789"
        )

        # Usuarios Internos
        cls.tecnico_1 = User.objects.create_user(username="tecnico_juan", password="p")
        cls.tecnico_1.roles.add(cls.role_tecnico)
        cls.tecnico_2 = User.objects.create_user(username="tecnico_ana", password="p")
        cls.tecnico_2.roles.add(cls.role_tecnico)

        cls.gerente = User.objects.create_user(
            username="gerente_test", password="p", is_staff=True
        )
        cls.gerente.roles.add(cls.role_gerente)
        # Asignar permiso para ver la vista
        from django.contrib.auth.models import Permission

        view_process_perm = Permission.objects.get(codename="view_process")
        cls.gerente.user_permissions.add(view_process_perm)

        # Procesos para pruebas
        hoy = tz.now().date()
        cls.p1 = Process.objects.create(
            user=cls.cliente_zzz,
            process_type=ProcessTypeChoices.ASESORIA,
            estado=ProcessStatusChoices.EN_PROGRESO,
            fecha_inicio=hoy - timedelta(days=10),
            fecha_final=hoy + timedelta(days=30),
        )
        cls.p1.assigned_to.add(cls.tecnico_1)  # Asignar a tecnico_1
        cls.p1.refresh_from_db()
        Process.objects.filter(pk=cls.p1.pk).update(
            fecha_inicio=hoy - timedelta(days=10), fecha_final=hoy + timedelta(days=30)
        )
        cls.p1.refresh_from_db()
        cls.p2 = Process.objects.create(
            user=cls.cliente_aaa,
            process_type=ProcessTypeChoices.CONTROL_CALIDAD,
            estado=ProcessStatusChoices.FINALIZADO,
            fecha_inicio=hoy - timedelta(days=20),
            fecha_final=hoy + timedelta(days=10),
        )
        cls.p2.assigned_to.add(cls.tecnico_2)  # Asignar a tecnico_2
        cls.p2.refresh_from_db()
        Process.objects.filter(pk=cls.p2.pk).update(
            fecha_inicio=hoy - timedelta(days=20), fecha_final=hoy + timedelta(days=10)
        )
        cls.p2.refresh_from_db()
        cls.p3 = Process.objects.create(
            user=cls.cliente_aaa,
            process_type=ProcessTypeChoices.ASESORIA,
            estado=ProcessStatusChoices.EN_PROGRESO,
            fecha_inicio=hoy - timedelta(days=5),
            fecha_final=None,
        )
        cls.p3.assigned_to.add(cls.tecnico_1)  # Asignar a tecnico_1
        cls.p3.refresh_from_db()
        Process.objects.filter(pk=cls.p3.pk).update(
            fecha_inicio=hoy - timedelta(days=5), fecha_final=None
        )
        cls.p3.refresh_from_db()
        cls.p4 = Process.objects.create(
            user=cls.cliente_zzz,
            process_type=ProcessTypeChoices.OTRO,
            estado=ProcessStatusChoices.RADICADO,
            fecha_inicio=hoy - timedelta(days=30),
            fecha_final=hoy - timedelta(days=1),
        )
        Process.objects.filter(pk=cls.p4.pk).update(
            fecha_inicio=hoy - timedelta(days=30), fecha_final=hoy - timedelta(days=1)
        )
        cls.p4.refresh_from_db()
        cls.url = reverse("process_internal_list")

    def setUp(self):
        """Loguea un usuario con permisos antes de cada test."""
        self.client.login(username="gerente_test", password="p")

    def test_view_access_and_template(self):
        """Verifica que la vista carga correctamente para un usuario interno."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "process/process_internal_list.html")
        self.assertIn("procesos", response.context)
        # Por defecto, debe haber 4 procesos
        self.assertEqual(len(response.context["procesos"]), 4)

    def test_filter_by_assigned_user(self):
        """Prueba el filtro por usuario asignado."""
        # p1 y p3 están asignados a tecnico_1
        response = self.client.get(self.url, {"assigned_user": self.tecnico_1.id})
        self.assertEqual(response.status_code, 200)
        procesos = response.context["procesos"]
        self.assertEqual(len(procesos), 2)
        self.assertIn(self.p1, procesos)
        self.assertIn(self.p3, procesos)
        self.assertNotIn(self.p2, procesos)  # p2 está asignado a tecnico_2

    def test_filter_by_process_type(self):
        """Prueba el filtro por tipo de proceso."""
        response = self.client.get(
            self.url, {"process_type": ProcessTypeChoices.ASESORIA}
        )
        self.assertEqual(response.status_code, 200)
        procesos = response.context["procesos"]
        self.assertEqual(len(procesos), 2)
        self.assertIn(self.p1, procesos)
        self.assertIn(self.p3, procesos)

    def test_combined_filters(self):
        """Prueba una combinación de filtros."""
        params = {
            "process_type": ProcessTypeChoices.ASESORIA,
            "estado": ProcessStatusChoices.EN_PROGRESO,
            "assigned_user": self.tecnico_1.id,
        }
        response = self.client.get(self.url, params)
        self.assertEqual(response.status_code, 200)
        procesos = response.context["procesos"]
        self.assertEqual(len(procesos), 2)  # p1 y p3 coinciden

    def test_filter_no_results(self):
        """Prueba un filtro que no debe devolver resultados."""
        response = self.client.get(
            self.url, {"process_type": ProcessTypeChoices.CALCULO_BLINDAJES}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["procesos"]), 0)
        self.assertContains(
            response, "No se encontraron procesos con los filtros aplicados."
        )

    def test_default_sorting_is_by_fecha_inicio_desc(self):
        """Verifica que el orden por defecto sea por fecha de inicio descendente."""
        response = self.client.get(self.url)
        procesos = list(response.context["procesos"])
        expected_order = [self.p3, self.p1, self.p2, self.p4]  # -5, -10, -20, -30 días
        self.assertEqual(procesos, expected_order)

    def test_sort_by_fecha_final_asc(self):
        """Prueba el ordenamiento por fecha de finalización ascendente."""
        # Los valores None se ordenan al final en PostgreSQL por defecto
        response = self.client.get(
            self.url, {"sort_by": "fecha_final", "sort_dir": "asc"}
        )
        procesos = list(response.context["procesos"])
        # p4 (-1d), p2 (+10d), p1 (+30d), p3 (None)
        expected_order = [self.p4, self.p2, self.p1, self.p3]
        self.assertEqual(procesos, expected_order)

    def test_sort_by_cliente_razon_social_desc(self):
        """Prueba el ordenamiento por razón social del cliente descendente."""
        response = self.client.get(self.url, {"sort_by": "cliente", "sort_dir": "desc"})
        procesos = list(response.context["procesos"])
        # ZZZ Company (p1, p4), AAA Company (p2, p3)
        # El orden secundario es el por defecto (fecha_inicio desc)
        expected_order = [self.p1, self.p4, self.p3, self.p2]
        self.assertEqual(procesos, expected_order)

    def test_sort_by_assigned_user_asc_with_filter(self):
        """Prueba el ordenamiento por usuario asignado (asc) combinado con un filtro."""
        response = self.client.get(
            self.url,
            {
                "estado": ProcessStatusChoices.EN_PROGRESO,  # Filtra p1 y p3
                "sort_by": "asignado",
                "sort_dir": "asc",
            },
        )
        procesos = list(response.context["procesos"])
        # Ambos (p1, p3) están asignados a tecnico_juan, el orden secundario es fecha_inicio desc
        expected_order = [self.p1, self.p3]
        self.assertEqual(procesos, expected_order)

    def test_view_calculates_and_displays_process_days(self):
        """Verifica que la vista calcule y muestre los días de proceso y vencimiento."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        # Verificar que las cabeceras de las columnas están en el template
        self.assertContains(response, "<th>Días de Proceso</th>")
        self.assertContains(response, "<th>Días para Vencimiento</th>")

        # Verificar los valores calculados en el contexto
        today = tz.now().date()
        procesos_en_contexto = {p.id: p for p in response.context["procesos"]}

        # Caso 1: Proceso próximo a vencer (p2)
        p2_context = procesos_en_contexto.get(self.p2.id)
        self.assertIsNotNone(p2_context)
        dias_proceso_p2 = (today - self.p2.fecha_inicio.date()).days
        dias_vencimiento_p2 = (self.p2.fecha_final.date() - today).days
        self.assertEqual(p2_context.dias_de_proceso, dias_proceso_p2)
        self.assertEqual(p2_context.dias_hasta_vencimiento, dias_vencimiento_p2)
        self.assertContains(
            response,
            f'<span class="badge bg-success">{dias_vencimiento_p2} días restantes</span>',
        )

        # Caso 2: Proceso vencido (p4)
        p4_context = procesos_en_contexto.get(self.p4.id)
        self.assertIsNotNone(p4_context)
        dias_vencimiento_p4 = (self.p4.fecha_final.date() - today).days
        self.assertEqual(p4_context.dias_hasta_vencimiento, dias_vencimiento_p4)
        self.assertContains(
            response,
            f'<span class="badge bg-danger">Vencido hace {abs(dias_vencimiento_p4)} días</span>',
        )

        # Caso 3: Proceso sin fecha de finalización (p3)
        p3_context = procesos_en_contexto.get(self.p3.id)
        self.assertIsNotNone(p3_context)
        self.assertIsNone(p3_context.dias_hasta_vencimiento)
        # El HTML debe contener el N/A para este proceso
        # (Esta es una prueba menos específica pero suficiente)
        self.assertContains(response, '<span class="text-muted">N/A</span>')


class ProcessListViewTest(TestCase):

    def test_process_list_shows_most_recent_process_progress(self):
        """Test ProcessListView muestra el progreso del proceso más reciente.

        Prueba que la lista de equipos muestre el progreso del proceso
        asociado más reciente (por fecha_inicio), ya sea directo o vía reporte.
        """
        # --- Arrange ---
        client_user = User.objects.create_user(
            username="progress_test_user", password="p"
        )
        client_role, _ = Role.objects.get_or_create(name=RoleChoices.CLIENTE)
        client_user.roles.add(client_role)
        def1 = ChecklistItemDefinition.objects.create(
            process_type=ProcessTypeChoices.ASESORIA,
            name="Def1",
            order=1,
            percentage=50,
        )
        ChecklistItemDefinition.objects.create(
            process_type=ProcessTypeChoices.ASESORIA,
            name="Def2",
            order=2,
            percentage=50,
        )

        equipment = Equipment.objects.create(
            user=client_user, nombre="Equipo de Test de Progreso"
        )

        # 1. Crear los procesos (los checklist items se crean automáticamente)
        process_old = Process.objects.create(
            user=client_user,
            process_type=ProcessTypeChoices.ASESORIA,
            fecha_inicio=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        equipment.process = process_old
        equipment.save()

        process_new = Process.objects.create(
            user=client_user,
            process_type=ProcessTypeChoices.ASESORIA,
            fecha_inicio=datetime(2024, 6, 1, tzinfo=timezone.utc),
        )
        Report.objects.create(
            user=client_user,
            equipment=equipment,
            process=process_new,
            title="Reporte Reciente",
        )

        # 2. Recuperar y actualizar los items del checklist en lugar de crearlos
        # Para el proceso antiguo (50% de progreso)
        item_old_1 = ProcessChecklistItem.objects.get(
            process=process_old, definition=def1
        )
        item_old_1.status = "aprobado"
        item_old_1.save()
        # El segundo ítem (item_old_2) se queda como is_completed=False

        # Para el proceso nuevo (100% de progreso)
        ProcessChecklistItem.objects.filter(process=process_new).update(
            status="aprobado"
        )

        # --- Act ---
        self.client.login(username="progress_test_user", password="p")
        response = self.client.get(reverse("process_list"))

        # --- Assert ---
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Equipo de Test de Progreso")
        # Verifica que se muestra el progreso del proceso más reciente (100%)
        self.assertContains(response, "width: 100%")
        # Verifica que NO se muestra el progreso del proceso antiguo (50%)
        self.assertNotContains(response, "width: 50%")
