from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from app.models import (
    ChecklistItemDefinition,
    PracticeCategoryChoices,
    Process,
    ProcessStatusChoices,
    ProcessTypeChoices,
)

User = get_user_model()


class AsesoriaChecklistCreationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.test_user = User.objects.create_user(
            username="testuser_asesoria_checklist",
            password="password123",
            email="test_ac@example.com",
        )

    def test_create_checklist_items_asesoria_veterinaria(self):
        """Test checklist creation for Asesoría - Veterinaria."""
        ChecklistItemDefinition.objects.filter(
            process_type=ProcessTypeChoices.ASESORIA,
            practice_category=PracticeCategoryChoices.VETERINARIA,
        ).delete()
        # Create definitions for Asesoría - Veterinaria
        items = [
            "CARTA SOLICITUD DE LICENCIA (Bogotá no)",
            "ANEXO 4",
            "RUT",
            "CÉDULA Y DIPLOMAS EPR",
            "PROGRAMA DE PROTECCIÓN RADIOLÓGICA",
            "ESTUDIO AMBIENTAL",
            "ESTUDIO MEDIO AMBIENTAL",
            "CÁLCULO DE BLINDAJES",
            "PROGRAMA DE VIGILANCIA POST MERCADO",
            "CERTIFICADO DE CURSO DE PROTECCIÓN RADIOLÓGICA TOES",
            "CONSTANCIA ASISTENCIA A CURSO SOBRE MANEJO DE EQUIPOS RX",
            "PROGRAMA DE CAPACITACIÓN EN PROTECCIÓN RADIOLÓGICA",
            "CERTIFICADO DE DOSIMETRÍA",
            "EVALUACIÓN DE EMERGENCIAS. (NO APLICA PARA INDUSTRIALES CAT I)",
            "HOJA DE VIDA DEL EQUIPO/MANTENIMIENTO/FICHA TECNICA/MANUAL DE USUARIO / REGISTRO DE IMPORTACIÓN",
            "LICENCIA ANTERIOR/PUESTA EN MARCHA O PRUEBAS INICIALES",
            "PLANO GENERAL",
        ]
        percentage = round(100 / len(items), 2)
        for idx, name in enumerate(items, 1):
            ChecklistItemDefinition.objects.get_or_create(
                process_type=ProcessTypeChoices.ASESORIA,
                practice_category=PracticeCategoryChoices.VETERINARIA,
                name=name,
                order=idx,
                defaults={"percentage": percentage},
            )
        process = Process.objects.create(
            process_type=ProcessTypeChoices.ASESORIA,
            practice_category=PracticeCategoryChoices.VETERINARIA,
            user=self.test_user,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )
        self.assertEqual(process.checklist_items.count(), len(items))
        for idx, name in enumerate(items, 1):
            self.assertTrue(
                process.checklist_items.filter(
                    definition__name=name, definition__order=idx
                ).exists()
            )

    def test_create_checklist_items_asesoria_medica_cat1(self):
        """Test checklist creation for Asesoría - Médica Categoría 1."""
        ChecklistItemDefinition.objects.filter(
            process_type=ProcessTypeChoices.ASESORIA,
            practice_category=PracticeCategoryChoices.MEDICA_CAT1,
        ).delete()
        items = [
            "ANEXO 3 SOLICITUD DE REGISTRO.",
            "CEDULA SOLICITANTE Y RUT",
            "CERTIFICADO REPRESENTANTE LEGAL",
            "DOCUMENTOS OPR (acta de grado)",
            "CÁLCULO DE BLINDAJE",
            "CONTROL DE CALIDAD",
            "REPORTE DE DOSIMETRÍA.",
            "NIVELES DE REFERENCIA (anexo)",
            "PLANO DE LA INSTALACIÓN Revisa:1. Elementos consumibles en cada área 2. Aire o ventilación en cada área Y los demás requerimientos.",
            "CURSOS DE PROTECCIÓN RADIOLÓGICA DEL PERSONAL.(actas de grado)",
            "PROGRAMA DE CAPACITACIÓN (anexo asistencia)",
            "HOJA DE VIDA EQUIPOS - REGISTROS DE MANTENIMIENTO DEL EQUIPO - INVIMA – ",
            "FORMATO DE PUESTA EN MARCHA (SI EL EQUIPO ES NUEVO)",
            "MANUAL DE TECNOVIGILANCIA (anexo foreia)",
            "MANUAL DE PROTECCIÓN RADIOLÓGICA anexo(incidentes -accidentes)",
            "LICENCIA ANTERIOR DEL EQUIPO (no si el equipo es nuevo) "
            '("CUNDINAMARCA, si son equipos fabricados antes del 2005 factura o '
            "certificado de ingreso al inventario de la entidad). o para Cundinamarca – "
            "inclusión en el inventario.",
        ]
        percentage = round(100 / len(items), 2)
        for idx, name in enumerate(items, 1):
            ChecklistItemDefinition.objects.get_or_create(
                process_type=ProcessTypeChoices.ASESORIA,
                practice_category=PracticeCategoryChoices.MEDICA_CAT1,
                name=name,
                order=idx,
                defaults={"percentage": percentage},
            )
        process = Process.objects.create(
            process_type=ProcessTypeChoices.ASESORIA,
            practice_category=PracticeCategoryChoices.MEDICA_CAT1,
            user=self.test_user,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )
        self.assertEqual(process.checklist_items.count(), len(items))
        for idx, name in enumerate(items, 1):
            self.assertTrue(
                process.checklist_items.filter(
                    definition__name=name, definition__order=idx
                ).exists()
            )

    def test_create_checklist_items_asesoria_medica_cat2(self):
        """Test checklist creation for Asesoría - Médica Categoría 2."""
        ChecklistItemDefinition.objects.filter(
            process_type=ProcessTypeChoices.ASESORIA,
            practice_category=PracticeCategoryChoices.MEDICA_CAT2,
        ).delete()
        items = [
            "ANEXO 3 SOLICITUD DE REGISTRO.",
            "CÁMARA DE COMERCIO Y RUT",
            "CEDULA REPRESENTANTE LEGAL",
            "DOCUMENTOS OPR (actas de grado)",
            "CÁLCULO DE BLINDAJE.",
            "CONTROL DE CALIDAD.",
            "REPORTE DE DOSIMETRÍA",
            "PLANO DE LA INSTALACIÓN",
            "CURSOS DE PROTECCIÓN RADIOLÓGICA DEL PERSONAL.",
            "PROGRAMA DE CAPACITACIÓN",
            "NIVELES DE REFERENCIA",
            "DESCRIPCIÓN SISTEMAS DE SEGURIDAD",
            "HOJA DE VIDA EQUIPOS - REGISTROS DE MANTENIMIENTO DEL EQUIPO - INVIMA – PERMISO DE IMPORTACIÓN",
            "1 FORMATO DE PUESTA EN MARCHA (SI EL EQUIPO ES NUEVO).",
            "MANUAL DE PROTECCIÓN RADIOLÓGICA",
            "MANUAL DE TECNOVIGILANCIA",
            "LICENCIA ANTERIOR DEL EQUIPO (no si el equipo es nuevo) REGISTRO",
            "EVALUACIÓN DE PUESTO DE TRABAJO",
            "ACEPTACIÓN DE RESPONSABILIDADES OPR",
        ]
        percentage = round(100 / len(items), 2)
        for idx, name in enumerate(items, 1):
            ChecklistItemDefinition.objects.get_or_create(
                process_type=ProcessTypeChoices.ASESORIA,
                practice_category=PracticeCategoryChoices.MEDICA_CAT2,
                name=name,
                order=idx,
                defaults={"percentage": percentage},
            )
        process = Process.objects.create(
            process_type=ProcessTypeChoices.ASESORIA,
            practice_category=PracticeCategoryChoices.MEDICA_CAT2,
            user=self.test_user,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )
        self.assertEqual(process.checklist_items.count(), len(items))
        for idx, name in enumerate(items, 1):
            self.assertTrue(
                process.checklist_items.filter(
                    definition__name=name, definition__order=idx
                ).exists()
            )

    def test_get_progress_percentage_asesoria_medica_cat1(self):
        """Test progress percentage for Asesoría - Médica Categoría 1 reaches 100%."""
        ChecklistItemDefinition.objects.filter(
            process_type=ProcessTypeChoices.ASESORIA,
            practice_category=PracticeCategoryChoices.MEDICA_CAT1,
        ).delete()
        items_data = [
            ("ANEXO 3 SOLICITUD DE REGISTRO.", 7),
            ("CEDULA SOLICITANTE Y RUT", 7),
            ("CERTIFICADO REPRESENTANTE LEGAL", 7),
            ("DOCUMENTOS OPR (acta de grado)", 7),
            ("CÁLCULO DE BLINDAJE", 6),
            ("CONTROL DE CALIDAD", 6),
            ("REPORTE DE DOSIMETRÍA.", 6),
            ("NIVELES DE REFERENCIA (anexo)", 6),
            (
                "PLANO DE LA INSTALACIÓN Revisa:1. Elementos consumibles en cada área 2. Aire o ventilación en cada área Y los demás requerimientos.",
                6,
            ),
            ("CURSOS DE PROTECCIÓN RADIOLÓGICA DEL PERSONAL.(actas de grado)", 6),
            ("PROGRAMA DE CAPACITACIÓN (anexo asistencia)", 6),
            (
                "HOJA DE VIDA EQUIPOS - REGISTROS DE MANTENIMIENTO DEL EQUIPO - INVIMA – ",
                6,
            ),
            ("FORMATO DE PUESTA EN MARCHA (SI EL EQUIPO ES NUEVO)", 6),
            ("MANUAL DE TECNOVIGILANCIA (anexo foreia)", 6),
            ("MANUAL DE PROTECCIÓN RADIOLÓGICA anexo(incidentes -accidentes)", 6),
            (
                "LICENCIA ANTERIOR DEL EQUIPO (no si el equipo es nuevo) "
                '("CUNDINAMARCA, si son equipos fabricados antes del 2005 factura o '
                "certificado de ingreso al inventario de la entidad). o para Cundinamarca – "
                "inclusión en el inventario.",
                6,
            ),
        ]  # 4*7 + 12*6 = 28 + 72 = 100

        self.assertEqual(
            sum(p[1] for p in items_data),
            100,
            "Percentages for MEDICA_CAT1 definitions must sum to 100",
        )

        for idx, (name, percentage) in enumerate(items_data, 1):
            ChecklistItemDefinition.objects.get_or_create(
                process_type=ProcessTypeChoices.ASESORIA,
                practice_category=PracticeCategoryChoices.MEDICA_CAT1,
                name=name,
                order=idx,
                defaults={"percentage": percentage},
            )

        process = Process.objects.create(
            process_type=ProcessTypeChoices.ASESORIA,
            practice_category=PracticeCategoryChoices.MEDICA_CAT1,
            user=self.test_user,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )
        self.assertEqual(process.checklist_items.count(), len(items_data))
        self.assertEqual(
            process.get_progress_percentage(), 0, "Initial progress should be 0"
        )

        for item in process.checklist_items.all():
            item.is_completed = True
            item.completed_at = timezone.now()
            item.save()

        self.assertEqual(
            process.get_progress_percentage(),
            100,
            "Progress should be 100% after completing all MEDICA_CAT1 items",
        )

    def test_get_progress_percentage_asesoria_medica_cat2(self):
        """Test progress percentage for Asesoría - Médica Categoría 2 reaches 100%."""
        ChecklistItemDefinition.objects.filter(
            process_type=ProcessTypeChoices.ASESORIA,
            practice_category=PracticeCategoryChoices.MEDICA_CAT2,
        ).delete()
        items_data = [
            ("ANEXO 3 SOLICITUD DE REGISTRO.", 6),
            ("CÁMARA DE COMERCIO Y RUT", 6),
            ("CEDULA REPRESENTANTE LEGAL", 6),
            ("DOCUMENTOS OPR (actas de grado)", 6),
            ("CÁLCULO DE BLINDAJE.", 6),
            ("CONTROL DE CALIDAD.", 5),
            ("REPORTE DE DOSIMETRÍA", 5),
            ("PLANO DE LA INSTALACIÓN", 5),
            ("CURSOS DE PROTECCIÓN RADIOLÓGICA DEL PERSONAL.", 5),
            ("PROGRAMA DE CAPACITACIÓN", 5),
            ("NIVELES DE REFERENCIA", 5),
            ("DESCRIPCIÓN SISTEMAS DE SEGURIDAD", 5),
            (
                "HOJA DE VIDA EQUIPOS - REGISTROS DE MANTENIMIENTO DEL EQUIPO - INVIMA – PERMISO DE IMPORTACIÓN",
                5,
            ),
            ("1 FORMATO DE PUESTA EN MARCHA (SI EL EQUIPO ES NUEVO).", 5),
            ("MANUAL DE PROTECCIÓN RADIOLÓGICA", 5),
            ("MANUAL DE TECNOVIGILANCIA", 5),
            ("LICENCIA ANTERIOR DEL EQUIPO (no si el equipo es nuevo) REGISTRO", 5),
            ("EVALUACIÓN DE PUESTO DE TRABAJO", 5),
            ("ACEPTACIÓN DE RESPONSABILIDADES OPR", 5),
        ]  # 5*6 + 14*5 = 30 + 70 = 100

        self.assertEqual(
            sum(p[1] for p in items_data),
            100,
            "Percentages for MEDICA_CAT2 definitions must sum to 100",
        )

        for idx, (name, percentage) in enumerate(items_data, 1):
            ChecklistItemDefinition.objects.get_or_create(
                process_type=ProcessTypeChoices.ASESORIA,
                practice_category=PracticeCategoryChoices.MEDICA_CAT2,
                name=name,
                order=idx,
                defaults={"percentage": percentage},
            )

        process = Process.objects.create(
            process_type=ProcessTypeChoices.ASESORIA,
            practice_category=PracticeCategoryChoices.MEDICA_CAT2,
            user=self.test_user,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )
        self.assertEqual(process.checklist_items.count(), len(items_data))
        self.assertEqual(
            process.get_progress_percentage(), 0, "Initial progress should be 0"
        )

        for item in process.checklist_items.all():
            item.is_completed = True
            item.completed_at = timezone.now()
            item.save()

        self.assertEqual(
            process.get_progress_percentage(),
            100,
            "Progress should be 100% after completing all MEDICA_CAT2 items",
        )


class ProcessChecklistModelTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.test_user = User.objects.create_user(
            username="testuser_process_checklist",
            password="password123",
            email="test_pc@example.com",
        )

        # Definitions for Cálculo de Blindajes - aligned with migration 0012
        cls.def1_calc, _ = ChecklistItemDefinition.objects.get_or_create(
            process_type=ProcessTypeChoices.CALCULO_BLINDAJES,
            name="Elaboración de cálculo.",  # Matched migration
            order=1,
            defaults={"percentage": 30},
        )
        cls.def2_calc, _ = ChecklistItemDefinition.objects.get_or_create(
            process_type=ProcessTypeChoices.CALCULO_BLINDAJES,
            name="Elaboración de informe.",  # Matched migration
            order=2,
            defaults={"percentage": 30},
        )
        cls.def3_calc, _ = ChecklistItemDefinition.objects.get_or_create(
            process_type=ProcessTypeChoices.CALCULO_BLINDAJES,
            name="Revisión de informe.",  # Matched migration
            order=3,
            defaults={"percentage": 20},
        )
        cls.def4_calc, _ = ChecklistItemDefinition.objects.get_or_create(
            process_type=ProcessTypeChoices.CALCULO_BLINDAJES,
            name="Publicación de informe.",  # Matched migration
            order=4,
            defaults={"percentage": 20},
        )

        # Definitions for Control de Calidad - aligned with migration 0012
        cls.def1_ctrl, _ = ChecklistItemDefinition.objects.get_or_create(
            process_type=ProcessTypeChoices.CONTROL_CALIDAD,
            name="Realización de medidas.",  # Matched migration
            order=1,
            defaults={"percentage": 30},  # Matched migration
        )
        cls.def2_ctrl, _ = ChecklistItemDefinition.objects.get_or_create(
            process_type=ProcessTypeChoices.CONTROL_CALIDAD,
            name="Elaboración de informe.",  # Matched migration
            order=2,
            defaults={"percentage": 30},  # Matched migration
        )
        cls.def3_ctrl, _ = ChecklistItemDefinition.objects.get_or_create(
            process_type=ProcessTypeChoices.CONTROL_CALIDAD,
            name="Revisión de informe.",  # Matched migration
            order=3,
            defaults={"percentage": 20},  # Matched migration
        )
        cls.def4_ctrl, _ = ChecklistItemDefinition.objects.get_or_create(
            process_type=ProcessTypeChoices.CONTROL_CALIDAD,
            name="Publicación de informe",  # Matched migration (no period here)
            order=4,
            defaults={"percentage": 20},  # Matched migration
        )

    def test_create_checklist_items_on_new_process(self):
        """Test that checklist items are created when a new process is saved."""
        process_calc = Process.objects.create(
            process_type=ProcessTypeChoices.CALCULO_BLINDAJES,
            # asesoria_subtype=AsesoriaSubtypeChoices.NO_APLICA, # Removed
            user=self.test_user,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )
        self.assertEqual(process_calc.checklist_items.count(), 4)
        self.assertTrue(
            process_calc.checklist_items.filter(definition=self.def1_calc).exists()
        )
        self.assertTrue(
            process_calc.checklist_items.filter(definition=self.def2_calc).exists()
        )
        self.assertTrue(
            process_calc.checklist_items.filter(definition=self.def3_calc).exists()
        )
        self.assertTrue(
            process_calc.checklist_items.filter(definition=self.def4_calc).exists()
        )

        process_ctrl = Process.objects.create(
            process_type=ProcessTypeChoices.CONTROL_CALIDAD,
            # asesoria_subtype=AsesoriaSubtypeChoices.NO_APLICA, # Removed
            user=self.test_user,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )
        self.assertEqual(process_ctrl.checklist_items.count(), 4)  # Expect 4 items now
        self.assertTrue(
            process_ctrl.checklist_items.filter(definition=self.def1_ctrl).exists()
        )
        self.assertTrue(
            process_ctrl.checklist_items.filter(definition=self.def2_ctrl).exists()
        )
        self.assertTrue(
            process_ctrl.checklist_items.filter(definition=self.def3_ctrl).exists()
        )  # Added assertion for 3rd item
        self.assertTrue(
            process_ctrl.checklist_items.filter(definition=self.def4_ctrl).exists()
        )  # Added assertion for 4th item

    def test_get_progress_percentage(self):
        """Test calculation of progress percentage."""
        process = Process.objects.create(
            process_type=ProcessTypeChoices.CALCULO_BLINDAJES,
            # asesoria_subtype=AsesoriaSubtypeChoices.NO_APLICA, # Removed
            user=self.test_user,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )
        self.assertEqual(
            process.get_progress_percentage(), 0, "Initial progress should be 0"
        )

        item1 = process.checklist_items.get(definition=self.def1_calc)
        item1.is_completed = True
        item1.completed_at = timezone.now()
        item1.save()
        self.assertEqual(
            process.get_progress_percentage(), 30, "Progress after completing 30% item"
        )

        item2 = process.checklist_items.get(definition=self.def2_calc)
        item2.is_completed = True
        item2.completed_at = timezone.now()
        item2.save()
        self.assertEqual(
            process.get_progress_percentage(),
            60,
            "Progress after completing another 30% item",
        )

        item3 = process.checklist_items.get(definition=self.def3_calc)
        item3.is_completed = True
        item3.completed_at = timezone.now()
        item3.save()
        self.assertEqual(
            process.get_progress_percentage(), 80, "Progress after completing 20% item"
        )

        item4 = process.checklist_items.get(definition=self.def4_calc)
        item4.is_completed = True
        item4.completed_at = timezone.now()
        item4.save()
        self.assertEqual(
            process.get_progress_percentage(),
            100,
            "Progress after completing final 20% item",
        )

    def test_reset_checklist_items_on_modification_status(self):
        """Test that checklist items are reset when status changes to EN_MODIFICACION."""
        process = Process.objects.create(
            process_type=ProcessTypeChoices.CALCULO_BLINDAJES,
            # asesoria_subtype=AsesoriaSubtypeChoices.NO_APLICA, # Removed
            user=self.test_user,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )
        item1 = process.checklist_items.get(definition=self.def1_calc)
        item1.is_completed = True
        item1.completed_at = timezone.now()
        item1.save()

        self.assertEqual(process.get_progress_percentage(), 30)
        self.assertTrue(item1.is_completed)

        process.estado = ProcessStatusChoices.EN_MODIFICACION
        process.save(user_who_modified=self.test_user)

        item1.refresh_from_db()
        self.assertFalse(
            item1.is_completed, "Item should be marked incomplete after reset"
        )
        self.assertIsNone(item1.completed_at, "Completed_at should be None after reset")
        self.assertEqual(
            process.get_progress_percentage(), 0, "Progress should be 0 after reset"
        )

        for item in process.checklist_items.all():
            self.assertFalse(item.is_completed)
            self.assertIsNone(item.completed_at)

    def test_create_checklist_for_existing_process_without_items_on_status_change(self):
        """Test checklist creation for an old process when its status changes."""
        process = Process.objects.create(
            process_type=ProcessTypeChoices.CALCULO_BLINDAJES,
            # asesoria_subtype=AsesoriaSubtypeChoices.NO_APLICA, # Removed
            user=self.test_user,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )
        self.assertTrue(process.checklist_items.exists())
        process.checklist_items.all().delete()  # Simulate an old process
        self.assertFalse(process.checklist_items.exists())

        process.estado = ProcessStatusChoices.EN_REVISION
        process.save(user_who_modified=self.test_user)

        self.assertEqual(
            process.checklist_items.count(), 4, "Checklist items should be recreated"
        )
        self.assertEqual(
            process.get_progress_percentage(),
            0,
            "Progress of newly created items should be 0",
        )

    def test_no_checklist_reset_if_status_not_modification(self):
        """Test that checklist items are not reset if status changes to something other than EN_MODIFICACION."""
        process = Process.objects.create(
            process_type=ProcessTypeChoices.CALCULO_BLINDAJES,
            # asesoria_subtype=AsesoriaSubtypeChoices.NO_APLICA, # Removed
            user=self.test_user,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )
        item1 = process.checklist_items.get(definition=self.def1_calc)
        item1.is_completed = True
        item1.completed_at = timezone.now()
        item1.save()
        self.assertEqual(process.get_progress_percentage(), 30)

        process.estado = ProcessStatusChoices.EN_REVISION  # Not EN_MODIFICACION
        process.save(user_who_modified=self.test_user)

        item1.refresh_from_db()
        self.assertTrue(item1.is_completed, "Item should remain completed")
        self.assertIsNotNone(item1.completed_at, "Completed_at should remain")
        self.assertEqual(
            process.get_progress_percentage(), 30, "Progress should be preserved"
        )

    def test_process_save_with_user_who_modified_in_log(self):
        """Test that user_who_modified is correctly logged in ProcessStatusLog."""
        process = Process.objects.create(
            process_type=ProcessTypeChoices.CALCULO_BLINDAJES,
            # asesoria_subtype=AsesoriaSubtypeChoices.NO_APLICA, # Removed
            user=self.test_user,
            estado=ProcessStatusChoices.EN_PROGRESO,
            # user_who_modified is None for the creation log via Process.objects.create
        )
        creation_log = process.status_logs.latest("fecha_cambio")
        self.assertIsNone(
            creation_log.usuario_modifico,
            "user_who_modified should be None for initial creation log via create()",
        )
        self.assertEqual(creation_log.estado_nuevo, ProcessStatusChoices.EN_PROGRESO)

        process.estado = ProcessStatusChoices.EN_REVISION
        process.save(user_who_modified=self.test_user)

        self.assertEqual(process.status_logs.count(), 2)
        modification_log = process.status_logs.latest("fecha_cambio")
        self.assertEqual(
            modification_log.usuario_modifico,
            self.test_user,
            "user_who_modified should be test_user for modification log",
        )
        self.assertEqual(
            modification_log.estado_nuevo, ProcessStatusChoices.EN_REVISION
        )
        self.assertEqual(
            modification_log.estado_anterior, ProcessStatusChoices.EN_PROGRESO
        )
