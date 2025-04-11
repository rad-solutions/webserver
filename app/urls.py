from django.urls import path

from app.views import (
    CustomLoginView,
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
]
