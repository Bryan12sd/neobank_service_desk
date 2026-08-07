from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = "Crea los grupos de roles del módulo Service Desk (CLIENT, AGENT, DEPARTMENT_HEAD)"

    def handle(self, *args, **options):
        groups = ["CLIENT", "AGENT", "DEPARTMENT_HEAD"]
        for name in groups:
            group, created = Group.objects.get_or_create(name=name)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Grupo creado: {name}"))
            else:
                self.stdout.write(f"Grupo ya existía: {name}")