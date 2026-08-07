from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


# ---------------------------------------------------------------------------
# Profile: extends Django's built-in User (does not replace it).
# The user's ROLE is NOT stored here as text: it is managed with
# django.contrib.auth.models.Group ("CLIENT" / "AGENT" / "DEPARTMENT_HEAD").
# This model only adds the extra fields required by the NEOBANK case
# (national id, phone).
# ---------------------------------------------------------------------------
class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    national_id = models.CharField("Cédula", max_length=10, unique=True)
    phone = models.CharField("Teléfono", max_length=15, blank=True)

    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfiles"

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.national_id})"


class Ticket(models.Model):
    REQUEST_INCIDENT = "INCIDENT"
    REQUEST_INQUIRY = "INQUIRY"
    REQUEST_COMPLAINT = "COMPLAINT"
    REQUEST_SUGGESTION = "SUGGESTION"
    REQUEST_TYPE_CHOICES = [
        (REQUEST_INCIDENT, "Incidente"),
        (REQUEST_INQUIRY, "Consulta"),
        (REQUEST_COMPLAINT, "Reclamo"),
        (REQUEST_SUGGESTION, "Sugerencia"),
    ]

    STATUS_OPEN = "OPEN"
    STATUS_ASSIGNED = "ASSIGNED"
    STATUS_IN_PROGRESS = "IN_PROGRESS"
    STATUS_ON_HOLD = "ON_HOLD"
    STATUS_RESOLVED = "RESOLVED"
    STATUS_CLOSED = "CLOSED"
    STATUS_CHOICES = [
        (STATUS_OPEN, "Abierto"),
        (STATUS_ASSIGNED, "Asignado"),
        (STATUS_IN_PROGRESS, "En proceso"),
        (STATUS_ON_HOLD, "En espera"),
        (STATUS_RESOLVED, "Resuelto"),
        (STATUS_CLOSED, "Cerrado"),
    ]

    ticket_number = models.AutoField(primary_key=True)
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tickets_created",
        verbose_name="Cliente",
    )
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tickets_assigned",
        verbose_name="Agente asignado",
    )
    subject = models.CharField("Asunto", max_length=150)
    description = models.TextField("Descripción")
    request_type = models.CharField(
        "Tipo de solicitud", max_length=20, choices=REQUEST_TYPE_CHOICES
    )
    incident_date = models.DateTimeField("Fecha del incidente")
    evidence = models.FileField(
        "Evidencia", upload_to="evidence/%Y/%m/", blank=True, null=True
    )
    status = models.CharField(
        "Estado", max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN
    )
    created_at = models.DateTimeField("Fecha de creación", auto_now_add=True)

    class Meta:
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"
        ordering = ["-incident_date"]

    def __str__(self):
        return f"#{self.ticket_number} - {self.subject}"

    def clean(self):

        if self._state.adding and self.incident_date and self.incident_date < timezone.now():
            raise ValidationError(
                {"incident_date": "La fecha del incidente no puede ser anterior a la fecha y hora actual."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class TicketUpdate(models.Model):
    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, related_name="updates", verbose_name="Ticket"
    )
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Empleado"
    )
    status = models.CharField(
        "Estado", max_length=20, choices=Ticket.STATUS_CHOICES
    )
    comment = models.TextField("Comentario")
    updated_at = models.DateTimeField("Fecha de seguimiento", auto_now_add=True)

    class Meta:
        verbose_name = "Seguimiento"
        verbose_name_plural = "Seguimientos"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Seguimiento de #{self.ticket_id} - {self.status}"

    def save(self, *args, **kwargs):
   
        super().save(*args, **kwargs)
        self.ticket.status = self.status
        self.ticket.save(update_fields=["status"])