from django.contrib.auth.views import LogoutView
from django.urls import path
from . import views

app_name = "service_desk"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),

    # 3.1 Acceso
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(next_page="service_desk:login"), name="logout"),
    path("register/", views.register_client, name="register_client"),

    # 3.3 / 3.4 Cliente
    path("tickets/new/", views.create_ticket, name="create_ticket"),
    path("tickets/mine/", views.my_tickets, name="my_tickets"),

    # Agente
    path("tickets/assigned/", views.agent_tickets, name="agent_tickets"),
    path(
        "tickets/<int:ticket_number>/update/",
        views.add_ticket_update,
        name="add_ticket_update",
    ),

    # 3.2 / 4.3 Jefe de Departamento
    path("tickets/unassigned/", views.unassigned_tickets, name="unassigned_tickets"),
    path("tickets/<int:ticket_number>/assign/", views.assign_ticket, name="assign_ticket"),
    path("reports/", views.department_report, name="department_report"),
    path("reports/by-type/", views.report_by_request_type, name="report_by_request_type"),
]