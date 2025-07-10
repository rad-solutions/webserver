import random

from django.core.files.uploadedfile import SimpleUploadedFile  # For dummy PDF
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from faker import Faker

# Import your models
from app.models import (
    Anotacion,
    ClientProfile,
    Equipment,
    EstadoEquipoChoices,
    EstadoReporteChoices,
    HistorialTuboRayosX,
    PracticeCategoryChoices,
    Process,
    ProcessStatusChoices,
    ProcessTypeChoices,
    Report,
    Role,
    RoleChoices,
    User,
)

# Number of records to create for each model
NUM_USERS = 10
NUM_CLIENT_PROFILES = 7  # Should be <= NUM_USERS and match client role users
NUM_INTERNAL_USERS = NUM_USERS - NUM_CLIENT_PROFILES
NUM_PROCESSES_PER_USER = 2
NUM_EQUIPMENT_PER_CLIENT = 2
NUM_REPORTS_PER_PROCESS = 1
NUM_ANOTACIONES_PER_PROCESS = 3
NUM_HISTORIAL_TUBOS_PER_EQUIPMENT = 2


class Command(BaseCommand):
    help = "Populates the database with synthetic data for testing."

    @transaction.atomic  # Ensure all operations are done in a single transaction
    def handle(self, *args, **options):
        self.stdout.write("Starting database population...")
        fake = Faker("es_CO")  # Using Spanish (Colombia) locale for more relevant data

        # --- Clear existing data (optional, but recommended for reruns) ---
        self.stdout.write(
            "Clearing existing data (excluding superusers and specific predefined users)..."
        )
        # Exclude users created by create_users.py script from deletion
        # Superusers are already excluded by is_superuser=False
        predefined_usernames = [
            "cliente_test",
            "gerente_test",
            "director_test",
            "tecnico_apoyo_test",
            "admin_staff_test",
            # Add 'admin' if it's created in create_users.py and not as a superuser by default
        ]
        User.objects.filter(is_superuser=False).exclude(
            username__in=predefined_usernames
        ).delete()
        Role.objects.all().delete()
        # ClientProfile, Process, Equipment, Report, Anotacion will cascade delete
        # or be deleted if their User/Process is deleted.

        # --- Create Roles ---
        self.stdout.write("Creating Roles...")
        roles_to_create = {}
        for choice_value, choice_label in RoleChoices.choices:
            role, created = Role.objects.get_or_create(name=choice_value)
            roles_to_create[choice_value] = role
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created role: {choice_label}"))

        # --- Create Users ---
        self.stdout.write(f"Creating {NUM_USERS} Users...")
        users = []
        client_users = []
        internal_staff_users = []

        # Create Client Users
        for i in range(NUM_CLIENT_PROFILES):
            username = fake.unique.user_name()
            user = User.objects.create_user(
                username=username,
                email=fake.unique.email(),
                password="password123",  # Use a common password for test users
                first_name=fake.first_name(),
                last_name=fake.last_name(),
            )
            user.roles.add(roles_to_create[RoleChoices.CLIENTE])
            users.append(user)
            client_users.append(user)
            self.stdout.write(self.style.SUCCESS(f"Created client user: {username}"))

        # Create Internal Staff Users
        internal_role_choices = [
            RoleChoices.GERENTE,
            RoleChoices.DIRECTOR_TECNICO,
            RoleChoices.PERSONAL_TECNICO_APOYO,
            RoleChoices.PERSONAL_ADMINISTRATIVO,
        ]
        for i in range(NUM_INTERNAL_USERS):
            username = fake.unique.user_name()
            user = User.objects.create_user(
                username=username,
                email=fake.unique.email(),
                password="password123",
                first_name=fake.first_name(),
                last_name=fake.last_name(),
            )
            # Assign a random internal role
            user.roles.add(roles_to_create[random.choice(internal_role_choices)])
            users.append(user)
            internal_staff_users.append(user)
            self.stdout.write(self.style.SUCCESS(f"Created internal user: {username}"))

        # --- Create Client Profiles ---
        self.stdout.write(f"Creating {NUM_CLIENT_PROFILES} Client Profiles...")
        for client_user in client_users:
            ClientProfile.objects.create(
                user=client_user,
                razon_social=fake.company(),
                nit=fake.unique.numerify(text="#########-#"),  # Basic NIT format
                representante_legal=fake.name(),
                direccion_instalacion=fake.street_address(),
                departamento=fake.administrative_unit(),  # Changed from fake.state()
                municipio=fake.city(),
                persona_contacto=fake.name(),
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created client profile for: {client_user.username}"
                )
            )

        # --- Create Processes ---
        self.stdout.write("Creating Processes...")  # Corrected F541
        processes = []
        for user_obj in users:  # Create processes for all types of users
            for _ in range(NUM_PROCESSES_PER_USER):
                process_type = random.choice(ProcessTypeChoices.choices)[0]
                practice_category = None
                if process_type == ProcessTypeChoices.ASESORIA:
                    practice_category = random.choice(PracticeCategoryChoices.choices)[
                        0
                    ]

                process = Process.objects.create(
                    user=user_obj,
                    process_type=process_type,
                    practice_category=practice_category,
                    estado=random.choice(ProcessStatusChoices.choices)[0],
                    fecha_final=(
                        fake.date_time_this_decade(
                            tzinfo=timezone.get_current_timezone()
                        )
                        if random.choice([True, False])
                        else None
                    ),
                )
                processes.append(process)
                self.stdout.write(
                    self.style.SUCCESS(f"Created process for user: {user_obj.username}")
                )

        # --- Create Equipment ---
        # Equipment is typically associated with client users
        self.stdout.write("Creating Equipment...")  # Corrected F541
        equipments = []
        if client_users:  # Only create equipment if there are client users
            for client_user in client_users:
                for _ in range(NUM_EQUIPMENT_PER_CLIENT):
                    # Ensure serial is unique if not blank/null
                    serial_number = None
                    if random.choice(
                        [True, True, False]
                    ):  # 2/3 chance of having a serial
                        serial_number = fake.unique.ean(length=13)

                    equipment = Equipment.objects.create(
                        user=client_user,  # Equipment owned by a client user
                        nombre=fake.sentence(nb_words=3),
                        marca=fake.company_suffix() + " " + fake.word().capitalize(),
                        modelo=fake.bothify(text="Model-####??"),
                        serial=serial_number,
                        practica_asociada=fake.bs(),
                        fecha_adquisicion=fake.date_between(
                            start_date="-5y", end_date="today"
                        ),
                        fecha_vigencia_licencia=fake.date_between(
                            start_date="today", end_date="+2y"
                        ),
                        fecha_ultimo_control_calidad=fake.date_between(
                            start_date="-1y", end_date="today"
                        ),
                        fecha_vencimiento_control_calidad=fake.date_between(
                            start_date="today", end_date="+1y"
                        ),
                        tiene_proceso_de_asesoria=fake.boolean(
                            chance_of_getting_true=30
                        ),
                        process=(
                            random.choice(processes)
                            if processes and random.choice([True, False])
                            else None
                        ),  # Optionally link to a random process
                        estado_actual=random.choice(EstadoEquipoChoices.choices)[0],
                        sede=fake.city_suffix() + " " + fake.street_name(),
                    )
                    equipments.append(equipment)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Created equipment for user: {client_user.username}"
                        )
                    )

        # --- Create HistorialTuboRayosX ---
        self.stdout.write("Creating HistorialTuboRayosX...")
        if equipments:
            for equipment_obj in equipments:
                for i in range(NUM_HISTORIAL_TUBOS_PER_EQUIPMENT):
                    HistorialTuboRayosX.objects.create(
                        equipment=equipment_obj,
                        marca=fake.company(),
                        modelo=fake.bothify(text="Tubo-??##"),
                        serial=fake.unique.ean(length=8),
                        fecha_cambio=fake.date_between(
                            start_date=equipment_obj.fecha_adquisicion or "-5y",
                            end_date="today",
                        ),
                    )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created tube history for equipment ID: {equipment_obj.id}"
                    )
                )

        # --- Create Reports ---
        self.stdout.write("Creating Reports...")  # Corrected F541
        if processes:  # Only create reports if there are processes
            for process_obj in processes:
                for _ in range(NUM_REPORTS_PER_PROCESS):
                    # Create a dummy PDF file for the report
                    dummy_pdf_content = (  # Corrected E501
                        b"%PDF-1.4\\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\\n"
                        b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\\n"
                        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\\n"
                        b"xref\\n0 4\\n0000000000 65535 f\\n0000000010 00000 n\\n"
                        b"0000000059 00000 n\\n0000000118 00000 n\\n"
                        b"trailer<</Size 4/Root 1 0 R>>\\nstartxref\\n196\\n%%EOF"
                    )
                    pdf_name = fake.slug() + ".pdf"

                    # User creating the report can be the process owner or another internal staff
                    report_creator = (
                        process_obj.user
                        if not internal_staff_users or random.choice([True, False])
                        else random.choice(internal_staff_users)
                    )

                    # Optionally associate with an equipment
                    associated_equipment = None
                    if equipments and random.choice(
                        [True, False, False]
                    ):  # 1/3 chance to associate equipment
                        associated_equipment = random.choice(equipments)

                    Report.objects.create(
                        user=report_creator,
                        process=process_obj,
                        equipment=associated_equipment,  # Assign equipment here
                        title=fake.catch_phrase(),
                        description=fake.paragraph(nb_sentences=2),
                        pdf_file=SimpleUploadedFile(
                            pdf_name, dummy_pdf_content, content_type="application/pdf"
                        ),
                        fecha_vencimiento=(
                            fake.date_between(start_date="today", end_date="+1y")
                            if random.choice([True, False])
                            else None
                        ),
                        estado_reporte=random.choice(EstadoReporteChoices.choices)[0],
                    )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Created report for process ID: {process_obj.id}"
                        )
                    )

        # --- Create Anotaciones ---
        self.stdout.write("Creating Anotaciones...")  # Corrected F541
        if processes:  # Only create annotations if there are processes
            for process_obj in processes:
                for _ in range(NUM_ANOTACIONES_PER_PROCESS):
                    # Annotation user can be the process owner or any internal staff, or system (None)
                    annotator_options = (
                        [process_obj.user] + internal_staff_users + [None]
                    )
                    annotator_user = random.choice(annotator_options)

                    Anotacion.objects.create(
                        proceso=process_obj,
                        usuario=annotator_user,
                        contenido=fake.text(max_nb_chars=200),
                    )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Created anotacion for process ID: {process_obj.id}"
                        )
                    )

        self.stdout.write(self.style.SUCCESS("Database population complete!"))
