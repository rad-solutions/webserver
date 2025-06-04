from django.urls import path

from app.views import (
    AnotacionCreateView,
    CustomLoginView,
    EquiposCreateView,
    EquiposDeleteView,
    EquiposDetailView,
    EquiposListView,
    EquiposUpdateView,
    ProcessCreateView,
    ProcessDeleteView,
    ProcessDetailView,
    ProcessListView,
    ProcessUpdateView,
    ReportCreateView,
    ReportDeleteView,
    ReportDetailView,
    ReportListView,
    ReportUpdateView,
    UserCreateView,
    UserDeleteView,
    UserDetailView,
    UserListView,
    UserUpdateView,
    logout_view,
    main,
)

urlpatterns = [
    path("", main, name="home"),
    # Authentication URLs
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", logout_view, name="logout"),
    # User URLs
    path("users/", UserListView.as_view(), name="user_list"),
    path("users/<int:pk>/", UserDetailView.as_view(), name="user_detail"),
    path("users/create/", UserCreateView.as_view(), name="user_create"),
    path("users/<int:pk>/update/", UserUpdateView.as_view(), name="user_update"),
    path("users/<int:pk>/delete/", UserDeleteView.as_view(), name="user_delete"),
    # Report URLs
    path("reports/", ReportListView.as_view(), name="report_list"),
    path("reports/<int:pk>/", ReportDetailView.as_view(), name="report_detail"),
    path("reports/create/", ReportCreateView.as_view(), name="report_create"),
    path("reports/<int:pk>/update/", ReportUpdateView.as_view(), name="report_update"),
    path("reports/<int:pk>/delete/", ReportDeleteView.as_view(), name="report_delete"),
    # Process URLs
    path("processes/", ProcessListView.as_view(), name="process_list"),
    path("processes/<int:pk>/", ProcessDetailView.as_view(), name="process_detail"),
    path("processes/create/", ProcessCreateView.as_view(), name="process_create"),
    path(
        "processes/<int:pk>/update/", ProcessUpdateView.as_view(), name="process_update"
    ),
    path(
        "processes/<int:pk>/delete/", ProcessDeleteView.as_view(), name="process_delete"
    ),
    path(
        "processes/anotacion/", AnotacionCreateView.as_view(), name="anotacion_create"
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
]
