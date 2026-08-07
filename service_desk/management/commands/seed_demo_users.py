from datetime import timedelta

from django.contrib.auth.models import User, Group
from django.core.management.base import BaseCommand
from django.utils import timezone

from service_desk.models import Profile, Ticket, TicketUpdate


class Command(BaseCommand):
    help = (
        "Crea usuarios de prueba (1 Cliente, 1 Agente, 1 Jefe de Departamento) "
        "y un par de tickets de ejemplo, para probar el flujo completo del sistema."
    )

    def handle(self, *args, **options):
        # Asegura que los grupos existan (por si no se corrió create_groups antes).
        client_group, _ = Group.objects.get_or_create(name="CLIENT")
        agent_group, _ = Group.objects.get_or_create(name="AGENT")
        head_group, _ = Group.objects.get_or_create(name="DEPARTMENT_HEAD")

        client = self._get_or_create_user(
            username="ana.torres",
            password="Cliente#2026",
            first_name="Ana",
            last_name="Torres",
            email="ana.torres@example.com",
            group=client_group,
            national_id="0912345678",
            phone="0991234567",
        )

        agent = self._get_or_create_user(
            username="juan.perez",
            password="Agente#2026",
            first_name="Juan",
            last_name="Perez",
            email="juan.perez@neobank.ec",
            group=agent_group,
            national_id="1712345678",
            phone="0987654321",
        )

        head = self._get_or_create_user(
            username="maria.gomez",
            password="Jefe#2026",
            first_name="Maria",
            last_name="Gomez",
            email="maria.gomez@neobank.ec",
            group=head_group,
            national_id="1798765432",
            phone="0976543210",
        )

        self._create_demo_ticket(
            client=client,
            agent=agent,
            subject="Bloqueo de tarjeta de crédito",
            description="El cliente reporta que su tarjeta fue bloqueada tras varios intentos fallidos.",
            request_type=Ticket.REQUEST_INCIDENT,
            status=Ticket.STATUS_IN_PROGRESS,
        )
        self._create_demo_ticket(
            client=client,
            agent=agent,
            subject="Consulta de saldo disponible",
            description="El cliente solicita conocer su saldo disponible antes de una transferencia.",
            request_type=Ticket.REQUEST_INQUIRY,
            status=Ticket.STATUS_RESOLVED,
        )

        self.stdout.write(self.style.SUCCESS("\nUsuarios de prueba listos:"))
        self.stdout.write("  CLIENTE           -> usuario: ana.torres   / clave: Cliente#2026")
        self.stdout.write("  AGENTE            -> usuario: juan.perez   / clave: Agente#2026")
        self.stdout.write("  JEFE_DEPARTAMENTO -> usuario: maria.gomez  / clave: Jefe#2026")
        self.stdout.write(self.style.SUCCESS("2 tickets de ejemplo creados (asignados a juan.perez)."))

    def _get_or_create_user(self, username, password, first_name, last_name, email, group, national_id, phone):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"first_name": first_name, "last_name": last_name, "email": email},
        )
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Usuario creado: {username}"))
        else:
            self.stdout.write(f"Usuario ya existía: {username}")

        user.groups.add(group)

        Profile.objects.get_or_create(
            user=user, defaults={"national_id": national_id, "phone": phone}
        )
        return user

    def _create_demo_ticket(self, client, agent, subject, description, request_type, status):
        ticket, created = Ticket.objects.get_or_create(
            client=client,
            subject=subject,
            defaults={
                "agent": agent,
                "description": description,
                "request_type": request_type,
                "incident_date": timezone.now() + timedelta(hours=1),
                "status": status,
            },
        )
        if created and status != Ticket.STATUS_OPEN:
            TicketUpdate.objects.create(
                ticket=ticket,
                employee=agent,
                status=status,
                comment="Seguimiento generado automáticamente por el comando de datos de prueba.",
            )
        return ticket