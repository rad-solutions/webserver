import re

from django.contrib.auth.models import Permission
from django.core import mail
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
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="interno")
        self.assertTrue(user.roles.filter(name=RoleChoices.GERENTE).exists())
        self.assertFalse(hasattr(user, "client_profile"))
        # Verificacion de correo de bienvenida
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ["interno@x.com"])
        self.assertIn("Bienvenido a RadSolutions", email.subject)
        self.assertIn("Se ha creado una cuenta para ti", email.body)
        self.assertIn("establece tu contraseña", email.body)

    def test_create_client_user_redirects_to_profile_form(self):
        """Verifica que al crear un usuario cliente, se redirige a crear el perfil."""
        self.client.login(username="external", password="externalpass")
        user_data = {
            "username": "cliente_nuevo",
            "first_name": "Nuevo",
            "last_name": "Cliente",
            "email": "cliente@nuevo.com",
            "role": self.role_cliente.id,
        }

        # 1. Crear el usuario
        response = self.client.post(self.url, user_data)
        new_user = User.objects.get(username="cliente_nuevo")

        # Verificar que se envió el correo de bienvenida
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ["cliente@nuevo.com"])
        self.assertIn("Bienvenido a RadSolutions", email.subject)

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
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse("client_profile_create", kwargs={"user_pk": self.user_to_edit.pk}),
        )

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
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="editme")
        self.assertTrue(user.roles.filter(name=RoleChoices.GERENTE).exists())
        self.assertFalse(hasattr(user, "client_profile"))


class PasswordResetFlowTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="oldpassword"
        )

    def test_full_password_reset_flow(self):
        """Prueba el flujo completo de restablecimiento de contraseña:

        Se compone de los siguientes pasos:
        1. Solicitar restablecimiento.
        2. Verificar que se envió el correo.
        3. Usar el enlace del correo para acceder al formulario.
        4. Enviar la nueva contraseña.
        5. Verificar que la contraseña se cambió y el usuario puede iniciar sesión.
        """
        # Asegurarse de que no hay ninguna sesión activa de un test anterior
        self.client.logout()
        # Paso 1: Solicitar el restablecimiento
        response = self.client.post(
            reverse("password_reset"), {"email": "test@example.com"}
        )
        self.assertRedirects(response, reverse("password_reset_done"))

        # Paso 2: Verificar que se envió un correo
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ["test@example.com"])
        self.assertIn("Restablecimiento de contraseña", email.subject)

        # Extraer el enlace del cuerpo del correo usando una expresión regular
        match = re.search(r"reset/([A-Za-z0-9\-_]+)/([A-Za-z0-9\-=_]+)/", email.body)
        self.assertIsNotNone(
            match, "No se encontró el enlace de restablecimiento en el correo."
        )
        uidb64, token = match.groups()

        # Paso 3: Usar el enlace para llegar al formulario de confirmación
        reset_url = reverse(
            "password_reset_confirm", kwargs={"uidb64": uidb64, "token": token}
        )
        response = self.client.get(reset_url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/password_reset_confirm.html")
        post_url = response.redirect_chain[-1][0]

        # Paso 4: Enviar la nueva contraseña
        new_password = "new_secure_password123"
        response = self.client.post(
            post_url, {"new_password1": new_password, "new_password2": new_password}
        )
        self.assertRedirects(response, reverse("password_reset_complete"))

        # Paso 5: Verificar que la nueva contraseña funciona
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new_password))

        # Probar el inicio de sesión con la nueva contraseña
        login_successful = self.client.login(username="testuser", password=new_password)
        self.assertTrue(login_successful)


class PasswordChangeFlowTest(TestCase):
    def setUp(self):
        """Crea un usuario y lo loguea antes de cada test."""
        self.old_password = "strong_password_123"
        self.user = User.objects.create_user(
            username="changepassuser",
            email="change@example.com",
            password=self.old_password,
        )
        self.client.login(username="changepassuser", password=self.old_password)
        self.url = reverse("password_change")

    def test_password_change_view_loads_for_logged_in_user(self):
        """Verifica que la página del formulario de cambio de contraseña carga correctamente."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/password_change_form.html")

    def test_successful_password_change(self):
        """Prueba el flujo completo y exitoso de cambio de contraseña."""
        new_password = "a_brand_new_password_456"
        data = {
            "old_password": self.old_password,
            "new_password1": new_password,
            "new_password2": new_password,
        }
        response = self.client.post(self.url, data)

        # Debería redirigir a la página de éxito
        self.assertRedirects(response, reverse("password_change_done"))

        # Verificar que la contraseña realmente cambió en la base de datos
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new_password))
        self.assertFalse(self.user.check_password(self.old_password))

    def test_password_change_fails_with_wrong_old_password(self):
        """Verifica que el cambio falle si la contraseña antigua es incorrecta."""
        new_password = "a_brand_new_password_456"
        data = {
            "old_password": "wrong_old_password",
            "new_password1": new_password,
            "new_password2": new_password,
        }
        response = self.client.post(self.url, data)

        # La página se vuelve a mostrar con un error, no redirige
        self.assertEqual(response.status_code, 200)
        form_in_context = response.context.get("form")
        self.assertFormError(
            form_in_context,
            "old_password",
            "Su contraseña antigua es incorrecta. Por favor, vuelva a introducirla.",
        )

        # Verificar que la contraseña NO cambió
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.old_password))

    def test_password_change_fails_with_mismatched_new_passwords(self):
        """Verifica que el cambio falle si las nuevas contraseñas no coinciden."""
        data = {
            "old_password": self.old_password,
            "new_password1": "new_password_a",
            "new_password2": "new_password_b",
        }
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        form_in_context = response.context.get("form")
        self.assertFormError(
            form_in_context,
            "new_password2",
            "Los dos campos de contraseña no coinciden.",
        )

        # Verificar que la contraseña NO cambió
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.old_password))
