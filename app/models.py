from django.contrib.auth.models import AbstractUser
from django.db import models

from app.storage import PDFStorage



class RoleChoices(models.TextChoices):
    EMPLEADO = 'empleado', 'Empleado'
    CLIENTE = 'cliente', 'Cliente'



class Role(models.Model):
    name = models.CharField(
        max_length=10,
        choices=RoleChoices.choices,
        unique=True 
    )

    def __str__(self):
        return self.get_name_display() 


class User(AbstractUser):
    created_at = models.DateTimeField(auto_now_add=True)
    
    roles = models.ManyToManyField(
        Role,
        blank=True, 
        related_name="users"
    )

    def __str__(self):
        
        return f"{self.first_name} {self.last_name} ({self.email})"


class Report(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reports")
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=400, blank=True, null=True)
    pdf_file = models.FileField(upload_to="reports_pdfs/", storage=PDFStorage())
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report by {self.user.first_name}: {self.title}"

    def delete(self, *args, **kwargs):
        if self.pdf_file:
            storage = self.pdf_file.storage
            file_name = self.pdf_file.name

            super().delete(*args, **kwargs)

            if storage.exists(file_name):
                storage.delete(file_name)
        else:
            super().delete(*args, **kwargs)
