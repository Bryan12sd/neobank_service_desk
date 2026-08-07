from django.contrib import admin
from .models import Profile, Ticket, TicketUpdate


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "national_id", "phone")
    search_fields = ("user__username", "user__first_name", "user__last_name", "national_id")


class TicketUpdateInline(admin.TabularInline):
    model = TicketUpdate
    extra = 0
    readonly_fields = ("updated_at",)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "ticket_number",
        "client",
        "agent",
        "request_type",
        "status",
        "incident_date",
    )
    list_filter = ("status", "request_type")
    search_fields = ("subject", "client__username", "client__first_name", "client__last_name")
    inlines = [TicketUpdateInline]


@admin.register(TicketUpdate)
class TicketUpdateAdmin(admin.ModelAdmin):
    list_display = ("ticket", "employee", "status", "updated_at")
    list_filter = ("status",)