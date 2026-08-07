from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from django.utils import timezone

from .models import Ticket, TicketUpdate, Profile


class BootstrapFormMixin:
    """Agrega la clase 'form-control' (o 'form-check-input' en checkboxes) a
    todos los widgets del formulario, para que se vean bien con SB Admin 2
    sin tener que repetir 'class=form-control' en cada template."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.CheckboxInput,)):
                css_class = "form-check-input"
            else:
                css_class = "form-control"
            existing = widget.attrs.get("class", "")
            widget.attrs["class"] = (existing + " " + css_class).strip()

# Interfaz de registro de incidente (Cliente)

class TicketForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Ticket
        fields = [
            "subject",
            "description",
            "request_type",
            "incident_date",
            "evidence",
        ]
        labels = {
            "subject": "Asunto del incidente",
            "description": "Descripción del incidente",
            "request_type": "Tipo de solicitud",
            "incident_date": "Fecha del incidente",
            "evidence": "Evidencia del incidente",
        }
        widgets = {
            "incident_date": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def clean_incident_date(self):
        # Validación: no permitir fecha/hora anterior a la actual.
        incident_date = self.cleaned_data["incident_date"]
        if incident_date < timezone.now():
            raise forms.ValidationError(
                "La fecha del incidente no puede ser anterior a la fecha y hora actual."
            )
        return incident_date
# Seguimiento (Agente): cambia el estado y deja un comentario.

class TicketUpdateForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = TicketUpdate
        fields = ["status", "comment"]
        labels = {"status": "Estado", "comment": "Comentario"}
        widgets = {"comment": forms.Textarea(attrs={"rows": 3})}

# Asignación de ticket (Jefe de Departamento -> Agente)

class AssignTicketForm(BootstrapFormMixin, forms.Form):
    agent = forms.ModelChoiceField(
        queryset=User.objects.filter(groups__name="AGENT"),
        label="Asignar a",
        required=True,
    )

# 3.2 Interfaz de reporte (Jefe de Departamento): filtro por empleado y fecha.

class AgentReportFilterForm(BootstrapFormMixin, forms.Form):
    agent = forms.ModelChoiceField(
        queryset=User.objects.filter(groups__name="AGENT"),
        label="Empleado",
        required=True,
    )
    date = forms.DateField(
        label="Fecha", widget=forms.DateInput(attrs={"type": "date"}), required=True
    )


class RequestTypeFilterForm(BootstrapFormMixin, forms.Form):
    request_type = forms.ChoiceField(
        label="Tipo de solicitud",
        choices=Ticket.REQUEST_TYPE_CHOICES,
        required=True,
    )
# Registro de un nuevo Cliente. Crea el User + Profile y lo agrega al
# grupo CLIENT.

class ClientRegistrationForm(BootstrapFormMixin, UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True, label="Nombres")
    last_name = forms.CharField(max_length=150, required=True, label="Apellidos")
    email = forms.EmailField(required=True, label="Correo electrónico")
    national_id = forms.CharField(max_length=10, required=True, label="Cédula")
    phone = forms.CharField(max_length=15, required=False, label="Teléfono")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["username", "first_name", "last_name", "email"]

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            Profile.objects.create(
                user=user,
                national_id=self.cleaned_data["national_id"],
                phone=self.cleaned_data.get("phone", ""),
            )
            client_group, _ = Group.objects.get_or_create(name="CLIENT")
            user.groups.add(client_group)
        return user