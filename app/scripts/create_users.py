import json
import logging
import os

from django.contrib.auth import get_user_model
from django.db import transaction
from dotenv import load_dotenv

from app.models import Role, RoleChoices

load_dotenv(override=True)

logger = logging.getLogger(__name__)

User = get_user_model()


def create_user_with_role(
    username, email, password, first_name, last_name, role_choice
):
    """Create a user with a specific role and assign them to the relevant group."""
    role_name = role_choice.value  # Use the actual value for role name
    role_display_name = role_choice.label

    # Get or create the Role object
    role, role_created = Role.objects.get_or_create(name=role_name)
    if role_created:
        logger.info(f"Role '{role_display_name}' created.")
    else:
        logger.info(f"Role '{role_display_name}' already exists.")

    # Get or create the User object
    user, user_created = User.objects.get_or_create(
        username=username,
        defaults={
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "is_staff": False,  # Staff status should be explicit for admin/superuser
            "is_superuser": False,
        },
    )

    if user_created:
        user.set_password(password)
        logger.info(f"User '{username}' created")
    else:
        logger.info(f"User '{username}' already exists.")

    # Assign the role to the user
    if not user.roles.filter(name=role_name).exists():
        user.roles.add(role)
        logger.info(f"Assigned role '{role_display_name}' to user '{username}'.")
    else:
        logger.info(f"User '{username}' already has role '{role_display_name}'.")
    user.save()
    return user


@transaction.atomic
def run():
    """Create users for various roles if they don't exist."""
    json_test_users = os.getenv("TEST_USERS")
    my_dict = json.loads(json_test_users)
    # Create Admin User (Superuser)
    admin_username = my_dict.get("admin").get("username")
    admin_email = my_dict.get("admin").get("email")
    admin_pass = my_dict.get("admin").get("password")
    admin_user, admin_created = User.objects.get_or_create(
        username=admin_username,
        defaults={"email": admin_email, "is_staff": True, "is_superuser": True},
    )
    if admin_created:
        admin_user.set_password(admin_pass)
        admin_user.save()
        logger.info(f"Superuser '{admin_username}' created.")
    else:
        logger.info(f"Superuser '{admin_username}' already exists.")

    # Define user data for each role
    users_to_create = [
        {
            "username": my_dict.get("cliente").get("username"),
            "email": my_dict.get("cliente").get("email"),
            "password": my_dict.get("cliente").get("password"),
            "first_name": "Cliente",
            "last_name": "Prueba",
            "role_choice": RoleChoices.CLIENTE,
        },
        {
            "username": my_dict.get("gerente").get("username"),
            "email": my_dict.get("gerente").get("email"),
            "password": my_dict.get("gerente").get("password"),
            "first_name": "Gerente",
            "last_name": "Prueba",
            "role_choice": RoleChoices.GERENTE,
        },
        {
            "username": my_dict.get("director").get("username"),
            "email": my_dict.get("director").get("email"),
            "password": my_dict.get("director").get("password"),
            "first_name": "Director",
            "last_name": "Tecnico",
            "role_choice": RoleChoices.DIRECTOR_TECNICO,
        },
        {
            "username": my_dict.get("tecnico_apoyo").get("username"),
            "email": my_dict.get("tecnico_apoyo").get("email"),
            "password": my_dict.get("tecnico_apoyo").get("password"),
            "first_name": "Tecnico",
            "last_name": "Apoyo",
            "role_choice": RoleChoices.PERSONAL_TECNICO_APOYO,
        },
        {
            "username": my_dict.get("personal_administrativo").get("username"),
            "email": my_dict.get("personal_administrativo").get("email"),
            "password": my_dict.get("personal_administrativo").get("password"),
            "first_name": "Personal",
            "last_name": "Administrativo",
            "role_choice": RoleChoices.PERSONAL_ADMINISTRATIVO,
        },
    ]

    for user_data in users_to_create:
        create_user_with_role(
            username=user_data["username"],
            email=user_data["email"],
            password=user_data["password"],
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            role_choice=user_data["role_choice"],
        )

    logger.info("User creation script finished.")
