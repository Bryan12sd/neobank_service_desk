from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages

from .decorators import group_required
from .forms import (
    TicketForm,
    TicketUpdateForm,
    AssignTicketForm,
    AgentReportFilterForm,
    RequestTypeFilterForm,
    ClientRegistrationForm,
)
from .models import Ticket, TicketUpdate


class CustomLoginView(LoginView):
    template_name = "login.html"

    def get_success_url(self):
        return reverse_lazy("service_desk:dashboard")


@login_required
def dashboard(request):
    """Punto de entrada único (usado por el sidebar): redirige según el rol."""
    user = request.user
    if user.is_superuser or user.groups.filter(name="DEPARTMENT_HEAD").exists():
        return redirect("service_desk:unassigned_tickets")
    if user.groups.filter(name="AGENT").exists():
        return redirect("service_desk:agent_tickets")
    return redirect("service_desk:create_ticket")


def register_client(request):
    """Alta de un nuevo Cliente (autoservicio previo al login)."""
    if request.method == "POST":
        form = ClientRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Cuenta creada. Ya puedes iniciar sesión.")
            return redirect("service_desk:login")
    else:
        form = ClientRegistrationForm()
    return render(request, "register_client.html", {"form": form})



@group_required("CLIENT")
def create_ticket(request):
    if request.method == "POST":
        form = TicketForm(request.POST, request.FILES)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.client = request.user
            ticket.save()
            messages.success(
                request, f"Ticket #{ticket.ticket_number} registrado correctamente."
            )
            return redirect("service_desk:my_tickets")
    else:
        form = TicketForm()
    return render(request, "create_ticket.html", {"form": form})


@group_required("CLIENT")
def my_tickets(request):
    """Botón 'Consultar' del formulario del caso base: historial del propio cliente."""
    tickets = Ticket.objects.filter(client=request.user)
    return render(request, "my_tickets.html", {"tickets": tickets})



# Agente: ve sus tickets asignados y registra seguimiento (cambia estado)

@group_required("AGENT")
def agent_tickets(request):
    tickets = Ticket.objects.filter(agent=request.user)
    return render(request, "agent_tickets.html", {"tickets": tickets})


@group_required("AGENT")
def add_ticket_update(request, ticket_number):
    ticket = get_object_or_404(
        Ticket, ticket_number=ticket_number, agent=request.user
    )
    if request.method == "POST":
        form = TicketUpdateForm(request.POST)
        if form.is_valid():
            update = form.save(commit=False)
            update.ticket = ticket
            update.employee = request.user
            update.save()  # el save() del modelo sincroniza el estado en Ticket
            messages.success(request, "Seguimiento registrado.")
            return redirect("service_desk:agent_tickets")
    else:
        form = TicketUpdateForm(initial={"status": ticket.status})
    return render(
        request,
        "add_ticket_update.html",
        {"form": form, "ticket": ticket},
    )



# Asignación de ticket (Jefe de Departamento -> Agente)
@group_required("DEPARTMENT_HEAD")
def unassigned_tickets(request):
    """Bandeja de tickets recién creados por clientes, aún sin agente."""
    tickets = Ticket.objects.filter(agent__isnull=True)
    return render(request, "unassigned_tickets.html", {"tickets": tickets})


@group_required("DEPARTMENT_HEAD")
def assign_ticket(request, ticket_number):
    ticket = get_object_or_404(Ticket, ticket_number=ticket_number)
    if request.method == "POST":
        form = AssignTicketForm(request.POST)
        if form.is_valid():
            agent = form.cleaned_data["agent"]
            ticket.agent = agent
            ticket.save(update_fields=["agent"])
            # El TicketUpdate sincroniza el estado del ticket a ASSIGNED automáticamente.
            TicketUpdate.objects.create(
                ticket=ticket,
                employee=request.user,
                status=Ticket.STATUS_ASSIGNED,
                comment=(
                    f"Ticket asignado a {agent.get_full_name() or agent.username} "
                    f"por {request.user.get_full_name() or request.user.username}."
                ),
            )
            messages.success(
                request, f"Ticket #{ticket.ticket_number} asignado a {agent.username}."
            )
            return redirect("service_desk:unassigned_tickets")
    else:
        form = AssignTicketForm()
    return render(request, "assign_ticket.html", {"form": form, "ticket": ticket})



# Interfaz de reporte (Jefe de Departamento)
# Clientes atendidos por un empleado en una fecha (parámetros)
@group_required("DEPARTMENT_HEAD")
def department_report(request):
    form = AgentReportFilterForm(request.GET or None)
    tickets = Ticket.objects.none()
    if form.is_valid():
        agent = form.cleaned_data["agent"]
        date = form.cleaned_data["date"]
        tickets = Ticket.objects.filter(agent=agent, incident_date__date=date)
    return render(
        request,
        "department_report.html",
        {"form": form, "tickets": tickets},
    )

# Lista de clientes por tipo de solicitud

@group_required("DEPARTMENT_HEAD")
def report_by_request_type(request):
    form = RequestTypeFilterForm(request.GET or None)
    tickets = Ticket.objects.none()
    if form.is_valid():
        tickets = Ticket.objects.filter(request_type=form.cleaned_data["request_type"])
    return render(
        request,
        "report_by_request_type.html",
        {"form": form, "tickets": tickets},
    )