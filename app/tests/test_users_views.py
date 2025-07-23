from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from app.models import ClientBranch, ClientProfile, Role, RoleChoices, User


class UserCreatePermissionTest(TestCase):
    def setUp(self):
        self.role_admin, _ = Role.objects.get_or_create(name=RoleChoices.GERENTE)
        self.role_cliente, _ = Role.objects.get_or_create(name=RoleChoices.CLIENTE)
        self.admin_user = User.objects.create_user(
            username="admin", password="adminpass", email="admin@x.com"
        )
        perm = Permission.objects.get(
            codename="add_user", content_type__app_label="app"
        )
        self.admin_user.user_permissions.add(perm)
        self.external_user = User.objects.create_user(
            username="external", password="externalpass", email="external@x.com"
        )
        perm = Permission.objects.get(
            codename="add_external_user", content_type__app_label="app"
        )
        self.external_user.user_permissions.add(perm)
        self.url = reverse("user_create")

    def test_access_denied_without_permission(self):
        self.user = User.objects.create_user(username="noperm", password="nopass")
        self.client.login(username="noperm", password="nopass")
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_access_allowed_with_add_user(self):
        self.client.login(username="admin", password="adminpass")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        role_labels = [
            str(choice[1]) for choice in form.fields["role"].choices if choice[0]
        ]
        self.assertNotIn("Cliente", role_labels)
        self.assertIn("Gerente", role_labels)

    def test_access_allowed_with_add_external_user(self):
        self.client.login(username="external", password="externalpass")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        role_labels = [
            str(choice[1]) for choice in form.fields["role"].choices if choice[0]
        ]
        self.assertIn("Cliente", role_labels)
        self.assertNotIn("Gerente", role_labels)


class UserCreateFormTest(TestCase):
    def setUp(self):
        self.role_admin, _ = Role.objects.get_or_create(name=RoleChoices.GERENTE)
        self.role_cliente, _ = Role.objects.get_or_create(name=RoleChoices.CLIENTE)
        self.admin_user = User.objects.create_user(
            username="admin", password="adminpass", email="admin@x.com"
        )
        self.admin_user.roles.add(self.role_admin)
        perm = Permission.objects.get(
            codename="add_user", content_type__app_label="app"
        )
        self.admin_user.user_permissions.add(perm)
        self.external_user = User.objects.create_user(
            username="external", password="externalpass", email="external@x.com"
        )
        self.external_user.roles.add(self.role_admin)
        perm = Permission.objects.get(
            codename="add_external_user", content_type__app_label="app"
        )
        self.external_user.user_permissions.add(perm)
        self.url = reverse("user_create")

    def test_create_internal_user(self):
        self.client.login(username="admin", password="adminpass")
        data = {
            "username": "interno",
            "first_name": "Interno",
            "last_name": "Test",
            "email": "interno@x.com",
            "role": self.role_admin.id,
            "password1": "Testpass123!",
            "password2": "Testpass123!",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="interno")
        self.assertTrue(user.roles.filter(name=RoleChoices.GERENTE).exists())
        self.assertFalse(hasattr(user, "client_profile"))

    def test_create_client_user_redirects_to_profile_form(self):
        """Verifica que al crear un usuario cliente, se redirige a crear el perfil."""
        self.client.login(username="external", password="externalpass")
        user_data = {
            "username": "cliente_nuevo",
            "first_name": "Nuevo",
            "last_name": "Cliente",
            "email": "cliente@nuevo.com",
            "role": self.role_cliente.id,
            "password1": "Testpass123!",
            "password2": "Testpass123!",
        }

        # 1. Crear el usuario
        response = self.client.post(self.url, user_data)
        new_user = User.objects.get(username="cliente_nuevo")

        # Verificar redirección a la creación del perfil
        self.assertRedirects(
            response, reverse("client_profile_create", kwargs={"user_pk": new_user.pk})
        )

        # 2. Crear el perfil del cliente
        profile_data = {
            "razon_social": "Empresa Nueva S.A.S.",
            "nit": "987.654.321-0",
            "representante_legal": "Maria Rojas",
        }
        profile_url = reverse("client_profile_create", kwargs={"user_pk": new_user.pk})
        response = self.client.post(profile_url, profile_data)
        new_profile = ClientProfile.objects.get(user=new_user)

        # Verificar redirección a la creación de la sede
        self.assertRedirects(
            response,
            reverse("client_branch_create", kwargs={"profile_pk": new_profile.pk}),
        )

        # 3. Crear la primera sede
        branch_data = {
            "nombre": "Sede Principal",
            "direccion_instalacion": "Avenida 45 # 12-34",
            "departamento": "Cundinamarca",
            "municipio": "Bogotá D.C.",
            "persona_contacto": "Carlos Diaz",
        }
        branch_url = reverse(
            "client_branch_create", kwargs={"profile_pk": new_profile.pk}
        )
        response = self.client.post(branch_url, branch_data)

        # Verificar redirección final a los detalles del usuario
        self.assertRedirects(
            response, reverse("user_detail", kwargs={"pk": new_user.pk})
        )

        # Verificar que todo se creó correctamente
        self.assertTrue(ClientBranch.objects.filter(company=new_profile).exists())
        branch = ClientBranch.objects.get(company=new_profile)
        self.assertEqual(branch.nombre, "Sede Principal")


class UserUpdatePermissionTest(TestCase):
    def setUp(self):
        self.role_admin, _ = Role.objects.get_or_create(name=RoleChoices.GERENTE)
        self.role_cliente, _ = Role.objects.get_or_create(name=RoleChoices.CLIENTE)
        self.admin_user = User.objects.create_user(
            username="admin", password="adminpass", email="admin@x.com"
        )
        perm = Permission.objects.get(
            codename="add_user", content_type__app_label="app"
        )
        self.admin_user.user_permissions.set([perm])
        self.external_user = User.objects.create_user(
            username="external", password="externalpass", email="external@x.com"
        )
        perm = Permission.objects.get(
            codename="add_external_user", content_type__app_label="app"
        )
        self.external_user.user_permissions.set([perm])
        self.user_to_edit = User.objects.create_user(
            username="editme", password="editpass", email="editme@x.com"
        )
        self.url = reverse("user_update", args=[self.user_to_edit.id])

    def test_access_denied_without_permission(self):
        User.objects.create_user(username="noperm", password="nopass")
        self.client.login(username="noperm", password="nopass")
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_access_allowed_with_change_user(self):
        self.client.login(username="admin", password="adminpass")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        role_labels = [
            str(choice[1]) for choice in form.fields["role"].choices if choice[0]
        ]
        self.assertNotIn("Cliente", role_labels)
        self.assertIn("Gerente", role_labels)

    def test_access_allowed_with_add_external_user(self):
        self.client.login(username="external", password="externalpass")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        role_labels = [
            str(choice[1]) for choice in form.fields["role"].choices if choice[0]
        ]
        self.assertIn("Cliente", role_labels)
        self.assertNotIn("Gerente", role_labels)


class UserUpdateFormTest(TestCase):
    def setUp(self):
        self.role_admin, _ = Role.objects.get_or_create(name=RoleChoices.GERENTE)
        self.role_cliente, _ = Role.objects.get_or_create(name=RoleChoices.CLIENTE)
        self.admin_user = User.objects.create_user(
            username="admin", password="adminpass", email="admin@x.com"
        )
        self.admin_user.roles.add(self.role_admin)
        perm = Permission.objects.get(
            codename="change_user", content_type__app_label="app"
        )
        self.admin_user.user_permissions.set([perm])
        self.user_to_edit = User.objects.create_user(
            username="editme", password="editpass", email="editme@x.com"
        )
        self.user_to_edit.roles.add(self.role_admin)
        self.url = reverse("user_update", args=[self.user_to_edit.id])

    def test_update_internal_user(self):
        self.client.login(username="admin", password="adminpass")
        data = {
            "username": "editme",
            "first_name": "NuevoNombre",
            "last_name": "NuevoApellido",
            "email": "nuevo@x.com",
            "role": self.role_admin.id,
            "password1": "Testpass123!",
            "password2": "Testpass123!",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="editme")
        self.assertEqual(user.first_name, "NuevoNombre")
        self.assertEqual(user.last_name, "NuevoApellido")
        self.assertTrue(user.roles.filter(name=RoleChoices.GERENTE).exists())
        self.assertFalse(hasattr(user, "client_profile"))

    def test_update_to_client_user(self):
        self.client.login(username="admin", password="adminpass")
        data = {
            "username": "editme",
            "first_name": "Cliente",
            "last_name": "Editado",
            "email": "clienteeditado@x.com",
            "role": self.role_cliente.id,
            "password1": "Testpass123!",
            "password2": "Testpass123!",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("user_list"))

    def test_update_from_client_to_internal_removes_profile(self):
        # Primero, convierte el usuario en cliente con perfil
        self.client.login(username="admin", password="adminpass")
        self.user_to_edit.roles.set([self.role_cliente])
        self.client_profile = ClientProfile.objects.create(
            user=self.user_to_edit,
            razon_social="Empresa",
            nit="123",
        )
        self.client_branch = ClientBranch.objects.create(
            company=self.client_profile,
            nombre="Sede de Equipos",
            direccion_instalacion="Calle",
            departamento="Depto",
            municipio="Ciudad",
        )
        data = {
            "username": "editme",
            "first_name": "Interno",
            "last_name": "Editado",
            "email": "internoeditado@x.com",
            "role": self.role_admin.id,
            "password1": "Testpass123!",
            "password2": "Testpass123!",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="editme")
        self.assertTrue(user.roles.filter(name=RoleChoices.GERENTE).exists())
        self.assertFalse(hasattr(user, "client_profile"))
