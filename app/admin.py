from django.contrib import admin

from .models import (
    Anotacion,
    ClientProfile,
    Equipment,
    Process,
    ProcessStatusLog,
    Report,
    Role,
    User,
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "username",
        "first_name",
        "last_name",
        "email",
        "created_at",
        "is_staff",
        "is_active",
    )
    search_fields = ("username", "first_name", "last_name", "email")
    list_filter = ("is_active", "is_staff", "created_at", "roles")
    filter_horizontal = ("roles", "groups", "user_permissions")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "razon_social", "nit", "municipio", "departamento")
    search_fields = ("user__username", "razon_social", "nit")
    list_filter = ("departamento", "municipio")
    raw_id_fields = ("user",)


@admin.register(Process)
class ProcessAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "process_type",
        "user",
        "estado",
        "fecha_inicio",
        "fecha_final",
    )
    search_fields = ("user__username", "id")
    list_filter = ("process_type", "estado", "fecha_inicio")
    raw_id_fields = ("user",)
    readonly_fields = ("fecha_inicio",)


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "serial",
        "marca",
        "modelo",
        "user",
        "process",
        "estado_actual",
        "sede",
    )
    search_fields = ("nombre", "serial", "marca", "modelo", "user__username", "sede")
    list_filter = ("estado_actual", "marca", "user")
    raw_id_fields = ("user", "process")


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "user",
        "process",
        "equipment",
        "estado_reporte",
        "created_at",
    )
    search_fields = (
        "title",
        "description",
        "user__username",
        "process__id",
        "equipment__nombre",
        "equipment__serial",
    )
    list_filter = ("created_at", "estado_reporte", "equipment")
    raw_id_fields = ("user", "process", "equipment")
    readonly_fields = ("created_at",)


@admin.register(Anotacion)
class AnotacionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "proceso",
        "usuario",
        "fecha_creacion_display",
        "contenido_snippet",
    )
    search_fields = ("proceso__id", "usuario__username", "contenido")
    list_filter = ("fecha_creacion", "usuario")
    raw_id_fields = ("proceso", "usuario")
    readonly_fields = ("fecha_creacion",)

    def fecha_creacion_display(self, obj):
        return obj.fecha_creacion.strftime("%Y-%m-%d %H:%M")

    fecha_creacion_display.short_description = "Fecha Creación"

    def contenido_snippet(self, obj):
        return obj.contenido[:50] + "..." if len(obj.contenido) > 50 else obj.contenido

    contenido_snippet.short_description = "Contenido"


@admin.register(ProcessStatusLog)
class ProcessStatusLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "proceso",
        "estado_anterior",
        "estado_nuevo",
        "fecha_cambio_display",
        "usuario_modifico",
    )
    search_fields = (
        "proceso__id",
        "usuario_modifico__username",
        "estado_anterior",
        "estado_nuevo",
    )
    list_filter = (
        "fecha_cambio",
        "usuario_modifico",
        "estado_nuevo",
        "estado_anterior",
    )
    raw_id_fields = ("proceso", "usuario_modifico")
    readonly_fields = ("fecha_cambio",)

    def fecha_cambio_display(self, obj):
        return obj.fecha_cambio.strftime("%Y-%m-%d %H:%M")

    fecha_cambio_display.short_description = "Fecha Cambio"
