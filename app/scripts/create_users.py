import logging

from django.contrib.auth import get_user_model

from app.models import Role, RoleChoices

logger = logging.getLogger(__name__)

User = get_user_model()


def run():
    """Create the default admin and client users if they don't exist."""
    # Create Admin User
    admin_username = "admin"
    admin_email = "admin@gmail.com"
    admin_pass = "admin"
    admin_user, admin_created = User.objects.get_or_create(
        username=admin_username,
        defaults={"email": admin_email, "is_staff": True, "is_superuser": True},
    )
    if admin_created:
        admin_user.set_password(admin_pass)
        admin_user.save()
        logger.info(
            f"Superuser '{admin_username}' created with password '{admin_pass}'."
        )
    else:
        logger.info(f"Superuser '{admin_username}' already exists.")

    # Create Client Role
    client_role_name = RoleChoices.CLIENTE
    client_role, role_created = Role.objects.get_or_create(name=client_role_name)
    if role_created:
        logger.info(f"Role '{client_role.get_name_display()}' created.")

    # Create Client User
    client_username = "cliente"
    client_email = "cliente@example.com"
    client_pass = "clientepass"
    client_user, user_created = User.objects.get_or_create(
        username=client_username,
        defaults={"email": client_email, "first_name": "Cliente", "last_name": "Demo"},
    )

    if user_created:
        client_user.set_password(client_pass)
        client_user.roles.add(client_role)
        client_user.save()
        logger.info(
            f"Client user '{client_username}' created with password '{client_pass}' and role '{client_role.get_name_display()}'."
        )
    else:
        logger.info(f"Client user '{client_username}' already exists.")
        # Ensure the role is assigned even if the user existed
        if not client_user.roles.filter(name=client_role_name).exists():
            client_user.roles.add(client_role)
            logger.info(
                f"Assigned role '{client_role.get_name_display()}' to existing user '{client_username}'."
            )

    logger.info("User creation script finished.")
