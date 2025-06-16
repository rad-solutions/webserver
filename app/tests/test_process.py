from datetime import date, datetime, timedelta, timezone

from django.test import TestCase
from django.urls import reverse

from ..models import (
    Anotacion,
    Equipment,
    Process,
    ProcessStatusChoices,
    ProcessTypeChoices,
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
