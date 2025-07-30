import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from app.models import (
    ClientBranch,
    ClientProfile,
    Equipment,
    Process,
    ProcessStatusChoices,
    ProcessTypeChoices,
    Report,
    Role,
    RoleChoices,
    User,
)


class Command(BaseCommand):
    help = "Populates the database with a large amount of test data for pagination testing."

    def handle(self, *args, **kwargs):
        self.stdout.write("Iniciando la creación de datos de prueba...")

        # Obtener o crear roles
        role_cliente, _ = Role.objects.get_or_create(name=RoleChoices.CLIENTE)
        role_gerente, _ = Role.objects.get_or_create(name=RoleChoices.GERENTE)

        # Crear un usuario gerente para iniciar sesión
        gerente, created = User.objects.get_or_create(
            username="gerente_test",
            defaults={"first_name": "Gerente", "last_name": "Pruebas"},
        )
        if created:
            gerente.set_password("password")
            gerente.roles.add(role_gerente)
            gerente.save()
            self.stdout.write(
                self.style.SUCCESS(f"Usuario '{gerente.username}' creado.")
            )

        # Crear 30 usuarios clientes
        for i in range(1, 31):
            username = f"cliente_test_{i}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": "Cliente",
                    "last_name": f"Test {i}",
                    "email": f"cliente{i}@test.com",
                },
            )
            if not created:
                continue  # Si ya existe, no hacer nada más con él

            user.set_password("password")
            user.roles.add(role_cliente)
            user.save()

            profile = ClientProfile.objects.create(
                user=user,
                razon_social=f"Empresa de Prueba {i} S.A.S",
                nit=f"900.123.{i:03d}-0",
            )

            branch = ClientBranch.objects.create(
                company=profile,
                nombre="Sede Principal",
                direccion_instalacion=f"Calle Falsa 123, Oficina {i}",
                departamento="Antioquia",
                municipio="Medellín",
            )

            # Crear procesos, equipos y reportes para cada usuario
            for j in range(random.randint(1, 5)):  # Entre 1 y 5 procesos por cliente
                process = Process.objects.create(
                    user=user,
                    process_type=random.choice(ProcessTypeChoices.values),
                    estado=random.choice(ProcessStatusChoices.values),
                    fecha_inicio=timezone.now()
                    - timedelta(days=random.randint(1, 365)),
                )

                equipment = Equipment.objects.create(
                    user=user,
                    nombre=f"Equipo {j} de {username}",
                    serial=f"SN-{i}-{j}",
                    sede=branch,
                    process=process,
                )

                Report.objects.create(
                    user=user,
                    process=process,
                    equipment=equipment,
                    title=f"Reporte {j} para {username}",
                    description="Reporte autogenerado para pruebas de paginación.",
                )

        self.stdout.write(self.style.SUCCESS("¡Datos de prueba creados exitosamente!"))
