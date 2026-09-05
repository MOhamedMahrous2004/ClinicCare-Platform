from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from clinics.models import Patient

class Command(BaseCommand):
    help = "Link patients with users"

    def handle(self, *args, **kwargs):
        group, _ = Group.objects.get_or_create(name="Patient")

        for patient in Patient.objects.all():

            if patient.user:
                self.stdout.write(f"Skipped {patient.name}")
                continue

            username = f"p_{patient.id}"

            user = User.objects.create(username=username)
            user.set_password("123456")
            user.save()

            patient.user = user
            patient.save()

            user.groups.add(group)

            self.stdout.write(f"Linked {patient.name} -> {username}")

        self.stdout.write(self.style.SUCCESS("✅ Done"))