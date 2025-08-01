from django.contrib.auth import views as auth_views
from django.urls import include, path, reverse_lazy

from app.views import (
    AnotacionCreateView,
    ClientBranchCreateView,
    ClientBranchUpdateView,
    ClientProfileCreateView,
    ClientProfileUpdateView,
    CustomLoginView,
    DashboardGerenteView,
    DashboardInternoView,
    EquiposCreateView,
    EquiposDeleteView,
    EquiposDetailView,
    EquiposListView,
    EquiposUpdateView,
    EquipoTuboUpdateView,
    ProcessCreateView,
    ProcessDeleteView,
    ProcessDetailView,
    ProcessInternalListView,
    ProcessListView,
    ProcessProgressUpdateView,
    ProcessUpdateAssignmentView,
    ProcessUpdateView,
    ReportCreateView,
    ReportDeleteView,
    ReportDetailView,
    ReportListView,
    ReportStatusAndNoteUpdateView,
    ReportUpdateView,
    UserCreateView,
    UserDeleteView,
    UserDetailView,
    UserListView,
    UserLookupView,
    UserUpdateView,
    load_client_branches,
    load_user_equipment,
    load_user_processes,
    logout_view,
    main,
)

urlpatterns = [
    path("", main, name="home"),
    path(
        "dashboard/gerente/", DashboardGerenteView.as_view(), name="dashboard_gerente"
    ),
    path(
        "dashboard/interno/", DashboardInternoView.as_view(), name="dashboard_interno"
    ),
    # Authentication URLs
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", logout_view, name="logout"),
    # Credential Managment URLs
    path(
        "reset_password/",
        auth_views.PasswordResetView.as_view(
            template_name="registration/password_reset_form.html",
            email_template_name="registration/password_reset_email.html",
            subject_template_name="registration/password_reset_subject.txt",
        ),
        name="password_reset",
    ),
    path(
        "reset_password/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="registration/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="registration/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    path(
        "change-password/",
        auth_views.PasswordChangeView.as_view(
            template_name="registration/password_change_form.html",
            success_url=reverse_lazy("password_change_done"),
        ),
        name="password_change",
    ),
    path(
        "change-password/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="registration/password_change_done.html"
        ),
        name="password_change_done",
    ),
    # User URLs
    path("users/", UserListView.as_view(), name="user_list"),
    path("users/<int:pk>/", UserDetailView.as_view(), name="user_detail"),
    path("users/create/", UserCreateView.as_view(), name="user_create"),
    path("users/<int:pk>/update/", UserUpdateView.as_view(), name="user_update"),
    path("users/<int:pk>/delete/", UserDeleteView.as_view(), name="user_delete"),
    path(
        "users/<int:user_pk>/profile/create/",
        ClientProfileCreateView.as_view(),
        name="client_profile_create",
    ),
    path(
        "profile/<int:pk>/update/",
        ClientProfileUpdateView.as_view(),
        name="client_profile_update",
    ),
    path(
        "profile/<int:profile_pk>/branch/create/",
        ClientBranchCreateView.as_view(),
        name="client_branch_create",
    ),
    path(
        "branch/<int:pk>/update/",
        ClientBranchUpdateView.as_view(),
        name="client_branch_update",
    ),
    # Report URLs
    path("reports/", ReportListView.as_view(), name="report_list"),
    path("reports/<int:pk>/", ReportDetailView.as_view(), name="report_detail"),
    path("reports/create/", ReportCreateView.as_view(), name="report_create"),
    path("reports/<int:pk>/update/", ReportUpdateView.as_view(), name="report_update"),
    path("reports/<int:pk>/delete/", ReportDeleteView.as_view(), name="report_delete"),
    path(
        "reports/<int:pk>/status-note/",
        ReportStatusAndNoteUpdateView.as_view(),
        name="report_status_and_note",
    ),
    # Process URLs
    path("processes/", ProcessListView.as_view(), name="process_list"),
    path(
        "processes/internal/",
        ProcessInternalListView.as_view(),
        name="process_internal_list",
    ),
    path("processes/<int:pk>/", ProcessDetailView.as_view(), name="process_detail"),
    path("processes/create/", ProcessCreateView.as_view(), name="process_create"),
    path(
        "processes/<int:pk>/update/", ProcessUpdateView.as_view(), name="process_update"
    ),
    path(
        "processes/<int:pk>/delete/", ProcessDeleteView.as_view(), name="process_delete"
    ),
    path(
        "processes/<int:pk>/assignment/",
        ProcessUpdateAssignmentView.as_view(),
        name="process_update_assignment",
    ),
    path(
        "processes/<int:pk>/progress/",
        ProcessProgressUpdateView.as_view(),
        name="process_progress",
    ),
    path(
        "processes/<int:process_id>/anotacion/create/",
        AnotacionCreateView.as_view(),
        name="anotacion_create",
    ),
    # Equipment URLs
    path("equipos/", EquiposListView.as_view(), name="equipos_list"),
    path("equipos/<int:pk>/", EquiposDetailView.as_view(), name="equipos_detail"),
    path("equipos/create/", EquiposCreateView.as_view(), name="equipos_create"),
    path(
        "equipos/<int:pk>/update/", EquiposUpdateView.as_view(), name="equipos_update"
    ),
    path(
        "equipos/<int:pk>/delete/", EquiposDeleteView.as_view(), name="equipos_delete"
    ),
    path(
        "equipos/<int:pk>/tubo/update/",
        EquipoTuboUpdateView.as_view(),
        name="tubo_update",
    ),
    # AJAX URLs
    path("select2/", include("django_select2.urls")),
    path("ajax/user-lookup/", UserLookupView.as_view(), name="select2_model_user"),
    path(
        "ajax/load-user-processes/",
        load_user_processes,
        name="ajax_load_user_processes",
    ),
    path(
        "ajax/load-user-equipment/",
        load_user_equipment,
        name="ajax_load_user_equipment",
    ),
    path(
        "ajax/load-client-branches/",
        load_client_branches,
        name="ajax_load_client_branches",
    ),
]
