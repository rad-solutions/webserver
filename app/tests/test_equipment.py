from datetime import date

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from ..models import (
    Equipment,
    EstadoEquipoChoices,
    Process,
    ProcessStatusChoices,
    ProcessTypeChoices,
    Role,
    RoleChoices,
    User,
)


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
        self.user_cliente, _ = Role.objects.get_or_create(name=RoleChoices.CLIENTE)
        self.user_client.roles.add(self.user_cliente)

        # Assign a role with manage_equipment permission
        try:
            gerente_group = Group.objects.get(name=RoleChoices.GERENTE)
            self.admin_user.groups.add(gerente_group)
        except Group.DoesNotExist:
            # This might happen if migrations haven't run or groups aren't created yet
            # For testing, we might need to ensure groups are created or mock permissions
            # For now, let's assume the group exists as per migrations
            pass
        self.admin_user.save()  # Ensure the user's group membership is saved

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
            modelo="ModeloX100",
            serial="SN-ALPHA-001",
            fecha_adquisicion=date(2023, 1, 15),
            fecha_vigencia_licencia=date(2025, 6, 30),
            fecha_ultimo_control_calidad=date(2024, 1, 10),
            fecha_vencimiento_control_calidad=date(2025, 1, 10),
        )
        self.eq2 = Equipment.objects.create(
            nombre="Equipo Beta",
            user=self.user_client,
            process=self.process_blindajes,
            modelo="ModeloY200",
            serial="SN-BETA-002",
            fecha_adquisicion=date(2023, 7, 20),
            fecha_vigencia_licencia=date(2026, 1, 15),
            fecha_ultimo_control_calidad=date(2024, 7, 5),
            fecha_vencimiento_control_calidad=date(2025, 7, 5),
        )
        self.eq3 = Equipment.objects.create(
            nombre="Equipo Gamma (Admin)",
            user=self.admin_user,  # Para probar filtro de usuario
            modelo="ModeloX100",
            serial="SN-GAMMA-003",
            fecha_adquisicion=date(2024, 1, 1),
            fecha_vigencia_licencia=date(2025, 12, 1),
            fecha_ultimo_control_calidad=date(2024, 6, 1),
            fecha_vencimiento_control_calidad=date(2025, 6, 1),
        )
        self.eq4_no_dates = Equipment.objects.create(
            nombre="Equipo Delta Sin Fechas",
            user=self.user_client,
            process=self.process_calidad,
            modelo="ModeloZ300",
            serial="SN-DELTA-004",
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

    def test_equipos_list_filter_by_text_search_modelo_exact(self):
        """Testea el filtro de texto por modelo exacto."""
        response = self.client.get(self.url, {"text_search_term": "ModeloX100"})
        self.assertEqual(response.status_code, 200)
        equipos_en_contexto = response.context["equipos"]
        # eq1 y eq3_admin tienen "ModeloX100"
        self.assertEqual(len(equipos_en_contexto), 2)
        self.assertIn(self.eq1, equipos_en_contexto)
        self.assertIn(self.eq3, equipos_en_contexto)
        self.assertEqual(response.context["text_search_term"], "ModeloX100")

    def test_equipos_list_filter_by_text_search_serial_exact(self):
        """Testea el filtro de texto por serial exacto."""
        response = self.client.get(self.url, {"text_search_term": "SN-BETA-002"})
        self.assertEqual(response.status_code, 200)
        equipos_en_contexto = response.context["equipos"]
        self.assertEqual(len(equipos_en_contexto), 1)
        self.assertIn(self.eq2, equipos_en_contexto)
        self.assertEqual(response.context["text_search_term"], "SN-BETA-002")

    def test_equipos_list_filter_by_text_search_modelo_partial_icontains(self):
        """Testea el filtro de texto por modelo parcial (insensible a mayúsculas)."""
        response = self.client.get(
            self.url, {"text_search_term": "modelox"}
        )  # Minúsculas
        self.assertEqual(response.status_code, 200)
        equipos_en_contexto = response.context["equipos"]
        self.assertEqual(len(equipos_en_contexto), 2)  # eq1 y eq3
        self.assertIn(self.eq1, equipos_en_contexto)
        self.assertIn(self.eq3, equipos_en_contexto)
        self.assertEqual(response.context["text_search_term"], "modelox")

    def test_equipos_list_filter_by_text_search_serial_partial_icontains(self):
        """Testea el filtro de texto por serial parcial (insensible a mayúsculas)."""
        response = self.client.get(
            self.url, {"text_search_term": "alpha"}
        )  # Minúsculas
        self.assertEqual(response.status_code, 200)
        equipos_en_contexto = response.context["equipos"]
        self.assertEqual(len(equipos_en_contexto), 1)
        self.assertIn(self.eq1, equipos_en_contexto)
        self.assertEqual(response.context["text_search_term"], "alpha")

    def test_equipos_list_filter_by_text_search_matches_modelo_or_serial(self):
        """Testea el filtro de texto que coincide con modelo de un equipo y serial de otro."""
        # "ModeloX100" está en eq1 y eq3_admin (modelo)
        # "SN-BETA-002" está en eq2 (serial)
        # Si buscamos "00" debería encontrar eq1, eq2, eq3_admin, eq4_no_dates
        response = self.client.get(self.url, {"text_search_term": "00"})
        self.assertEqual(response.status_code, 200)
        equipos_en_contexto = response.context["equipos"]
        self.assertEqual(len(equipos_en_contexto), 4)
        self.assertIn(self.eq1, equipos_en_contexto)  # SN-ALPHA-001
        self.assertIn(self.eq2, equipos_en_contexto)  # SN-BETA-002
        self.assertIn(self.eq3, equipos_en_contexto)  # SN-GAMMA-003
        self.assertIn(self.eq4_no_dates, equipos_en_contexto)
        # SN-DELTA-004 ModeloX100, ModeloY200, ModeloZ300 Todos los modelos tienen "00"

    def test_equipos_list_filter_by_text_search_no_results(self):
        """Testea el filtro de texto que no devuelve resultados."""
        response = self.client.get(
            self.url, {"text_search_term": "TerminoInexistente123"}
        )
        self.assertEqual(response.status_code, 200)
        equipos_en_contexto = response.context["equipos"]
        self.assertEqual(len(equipos_en_contexto), 0)
        self.assertEqual(response.context["text_search_term"], "TerminoInexistente123")

    def test_equipos_list_filter_by_text_search_with_other_filters(self):
        """Testea el filtro de texto combinado con otro filtro (ej. tipo de proceso)."""
        # eq1: process_calidad, modelo="ModeloX100"
        # eq4_no_dates: process_calidad, modelo="ModeloZ300"
        # eq3_admin: (sin proceso asignado en este setUp), modelo="ModeloX100"
        # eq2: process_blindajes, modelo="ModeloY200"

        # Buscar "ModeloX100" (eq1, eq3_admin) Y process_type=CONTROL_CALIDAD (eq1, eq4_no_dates)
        # Resultado esperado: eq1
        response = self.client.get(
            self.url,
            {
                "text_search_term": "ModeloX100",
                "process_type": ProcessTypeChoices.CONTROL_CALIDAD,
            },
        )
        self.assertEqual(response.status_code, 200)
        equipos_en_contexto = response.context["equipos"]
        self.assertEqual(len(equipos_en_contexto), 1)
        self.assertIn(self.eq1, equipos_en_contexto)
        self.assertNotIn(self.eq3, equipos_en_contexto)  # No coincide con process_type
        self.assertNotIn(
            self.eq4_no_dates, equipos_en_contexto
        )  # No coincide con text_search_term
        self.assertEqual(response.context["text_search_term"], "ModeloX100")
        self.assertEqual(
            response.context["selected_process_type"],
            ProcessTypeChoices.CONTROL_CALIDAD,
        )

    def test_equipos_list_filter_by_text_search_client_user(self):
        """Testea el filtro de texto para un usuario cliente (solo ve sus equipos)."""
        self.client.logout()
        self.client.login(username="equipclient", password="password")
        # eq1 (user_client): modelo="ModeloX100"
        # eq3 (admin_user): modelo="ModeloX100"
        response = self.client.get(self.url, {"text_search_term": "ModeloX100"})
        self.assertEqual(response.status_code, 200)
        equipos_en_contexto = response.context["equipos"]
        self.assertEqual(len(equipos_en_contexto), 1)  # Solo eq1
        self.assertIn(self.eq1, equipos_en_contexto)
        self.assertNotIn(self.eq3, equipos_en_contexto)  # Pertenece a admin_user
        self.assertEqual(response.context["text_search_term"], "ModeloX100")
