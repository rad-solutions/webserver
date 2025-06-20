from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from app.models import ClientProfile, Role, RoleChoices, User


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

    def test_create_client_user(self):
        self.client.login(username="external", password="externalpass")
        data = {
            "username": "cliente",
            "first_name": "Cliente",
            "last_name": "Test",
            "email": "cliente@x.com",
            "role": self.role_cliente.id,
            "password1": "Testpass123!",
            "password2": "Testpass123!",
            "razon_social": "Empresa S.A.",
            "nit": "123456789",
            "direccion_instalacion": "Calle 123",
            "departamento": "Cundinamarca",
            "municipio": "Bogotá",
            "representante_legal": "Juan Perez",
            "persona_contacto": "Maria Lopez",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="cliente")
        self.assertTrue(user.roles.filter(name=RoleChoices.CLIENTE).exists())
        self.assertTrue(hasattr(user, "client_profile"))
        profile = user.client_profile
        self.assertEqual(profile.razon_social, "Empresa S.A.")
        self.assertEqual(profile.nit, "123456789")
        self.assertEqual(profile.departamento, "Cundinamarca")
        self.assertEqual(profile.municipio, "Bogotá")
        self.assertEqual(profile.representante_legal, "Juan Perez")
        self.assertEqual(profile.persona_contacto, "Maria Lopez")

    def test_client_user_missing_required_profile_fields(self):
        self.client.login(username="external", password="externalpass")
        data = {
            "username": "cliente2",
            "first_name": "Cliente2",
            "last_name": "Test",
            "email": "cliente2@x.com",
            "role": self.role_cliente.id,
            "password1": "Testpass123!",
            "password2": "Testpass123!",
            # Falta razon_social, nit, direccion_instalacion, departamento, municipio
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)
        form = response.context["form"]
        self.assertFormError(
            form, "razon_social", "Este campo es obligatorio para clientes."
        )
        self.assertFormError(form, "nit", "Este campo es obligatorio para clientes.")
        self.assertFormError(
            form, "direccion_instalacion", "Este campo es obligatorio para clientes."
        )
        self.assertFormError(
            form, "departamento", "Este campo es obligatorio para clientes."
        )
        self.assertFormError(
            form, "municipio", "Este campo es obligatorio para clientes."
        )
        self.assertFalse(User.objects.filter(username="cliente2").exists())


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
            "razon_social": "Empresa Nueva",
            "nit": "987654321",
            "direccion_instalacion": "Calle Nueva",
            "departamento": "Antioquia",
            "municipio": "Medellín",
            "representante_legal": "Ana Ruiz",
            "persona_contacto": "Carlos Gómez",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="editme")
        self.assertTrue(user.roles.filter(name=RoleChoices.CLIENTE).exists())
        self.assertTrue(hasattr(user, "client_profile"))
        profile = user.client_profile
        self.assertEqual(profile.razon_social, "Empresa Nueva")
        self.assertEqual(profile.nit, "987654321")
        self.assertEqual(profile.departamento, "Antioquia")
        self.assertEqual(profile.municipio, "Medellín")
        self.assertEqual(profile.representante_legal, "Ana Ruiz")
        self.assertEqual(profile.persona_contacto, "Carlos Gómez")

    def test_update_client_user_missing_required_profile_fields(self):
        self.client.login(username="admin", password="adminpass")
        data = {
            "username": "editme",
            "first_name": "Cliente",
            "last_name": "Editado",
            "email": "clienteeditado@x.com",
            "role": self.role_cliente.id,
            "password1": "Testpass123!",
            "password2": "Testpass123!",
            # Falta razon_social, nit, direccion_instalacion, departamento, municipio
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)
        form = response.context["form"]
        self.assertFormError(
            form, "razon_social", "Este campo es obligatorio para clientes."
        )
        self.assertFormError(form, "nit", "Este campo es obligatorio para clientes.")
        self.assertFormError(
            form, "direccion_instalacion", "Este campo es obligatorio para clientes."
        )
        self.assertFormError(
            form, "departamento", "Este campo es obligatorio para clientes."
        )
        self.assertFormError(
            form, "municipio", "Este campo es obligatorio para clientes."
        )

    def test_update_from_client_to_internal_removes_profile(self):
        # Primero, convierte el usuario en cliente con perfil
        self.client.login(username="admin", password="adminpass")
        self.user_to_edit.roles.set([self.role_cliente])
        ClientProfile.objects.create(
            user=self.user_to_edit,
            razon_social="Empresa",
            nit="123",
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
